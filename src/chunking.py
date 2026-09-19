from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        # Split on sentence boundaries: ". ", "! ", "? ", or ".\n"
        raw_sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        sentences = [s.strip() for s in raw_sentences if s.strip()]

        if not sentences:
            return []

        chunks: list[str] = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            chunk_text = " ".join(sentences[i : i + self.max_sentences_per_chunk]).strip()
            if chunk_text:
                chunks.append(chunk_text)
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if not current_text:
            return []
        if len(current_text) <= self.chunk_size:
            return [current_text]

        if not remaining_separators:
            return [
                current_text[i : i + self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
            ]

        # Find the first separator that is present in current_text
        separator = None
        next_separators: list[str] = []
        for i, sep in enumerate(remaining_separators):
            if sep == "" or sep in current_text:
                separator = sep
                next_separators = remaining_separators[i + 1 :]
                break

        if separator is None:
            return [
                current_text[i : i + self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
            ]

        splits = list(current_text) if separator == "" else current_text.split(separator)

        # Recursively split pieces that exceed chunk_size
        good_splits: list[str] = []
        for s in splits:
            if len(s) > self.chunk_size:
                good_splits.extend(self._split(s, next_separators))
            elif s:
                good_splits.append(s)

        # Merge pieces into chunks up to chunk_size
        chunks: list[str] = []
        current_chunk = ""
        for piece in good_splits:
            if not piece:
                continue
            if not current_chunk:
                current_chunk = piece
            else:
                candidate = current_chunk + separator + piece
                if len(candidate) <= self.chunk_size:
                    current_chunk = candidate
                else:
                    chunks.append(current_chunk)
                    current_chunk = piece
        if current_chunk:
            chunks.append(current_chunk)

        return chunks if chunks else [current_text]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot_prod = _dot(vec_a, vec_b)
    norm_a = math.sqrt(sum(x * x for x in vec_a))
    norm_b = math.sqrt(sum(y * y for y in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_prod / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        def _stats(chunks: list[str]) -> dict:
            count = len(chunks)
            avg_length = sum(len(c) for c in chunks) / count if count > 0 else 0.0
            return {
                "chunks": chunks,
                "count": count,
                "avg_length": avg_length,
            }

        fixed_chunks = FixedSizeChunker(chunk_size=chunk_size).chunk(text)
        sentence_chunks = SentenceChunker().chunk(text)
        recursive_chunks = RecursiveChunker(chunk_size=chunk_size).chunk(text)

        return {
            "fixed_size": _stats(fixed_chunks),
            "by_sentences": _stats(sentence_chunks),
            "recursive": _stats(recursive_chunks),
        }


class HeadingChunker:
    """
    Split Markdown text into chunks by heading structure.

    Each chunk starts at a heading line (# ... or ## ... etc.) and includes
    all content up to (but not including) the next heading of equal or higher
    level.  Content before the first heading becomes a separate chunk.

    Parameters:
        max_heading_level: headings deeper than this level are treated as body
                           text rather than split points (default 3, i.e.
                           split on #, ##, ###).
        include_heading:   if True (default), the heading line itself is
                           prepended to the chunk body.
    """

    # Regex that matches a Markdown ATX heading at the start of a line.
    _HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)", re.MULTILINE)

    def __init__(
        self,
        max_heading_level: int = 3,
        include_heading: bool = True,
        max_chunk_size: int | None = None,
    ) -> None:
        self.max_heading_level = max_heading_level
        self.include_heading = include_heading
        self.max_chunk_size = max_chunk_size

    def chunk(self, text: str) -> list[str]:
        """Return a list of text chunks split by Markdown headings."""
        if not text:
            return []

        # Find all headings that qualify as split points
        split_points: list[tuple[int, int, str, str]] = []
        for m in self._HEADING_RE.finditer(text):
            level = len(m.group(1))  # number of '#' chars
            if level <= self.max_heading_level:
                split_points.append((m.start(), level, m.group(0), m.group(2)))

        if not split_points:
            # No qualifying headings found — fallback to recursive or single chunk
            cleaned = text.strip()
            if not cleaned:
                return []
            if self.max_chunk_size and len(cleaned) > self.max_chunk_size:
                return RecursiveChunker(chunk_size=self.max_chunk_size).chunk(cleaned)
            return [cleaned]

        chunks: list[str] = []

        # Content before the first heading (preamble / front-matter body)
        preamble = text[: split_points[0][0]].strip()
        if preamble:
            if self.max_chunk_size and len(preamble) > self.max_chunk_size:
                chunks.extend(RecursiveChunker(chunk_size=self.max_chunk_size).chunk(preamble))
            else:
                chunks.append(preamble)

        # Build a chunk for each heading section
        for idx, (start, _level, heading_line, _title) in enumerate(split_points):
            # Section body runs from this heading to the next split point
            if idx + 1 < len(split_points):
                section_end = split_points[idx + 1][0]
            else:
                section_end = len(text)

            section_text = text[start:section_end]

            if not self.include_heading:
                # Remove the heading line itself
                section_text = section_text[len(heading_line) :].lstrip("\n")

            section_text = section_text.strip()
            if not section_text:
                continue

            # If section exceeds max_chunk_size, recursively split and reattach heading
            if self.max_chunk_size and len(section_text) > self.max_chunk_size:
                body_text = section_text[len(heading_line) :].strip() if self.include_heading else section_text
                sub_size = max(50, self.max_chunk_size - (len(heading_line) + 2 if self.include_heading else 0))
                sub_chunks = RecursiveChunker(chunk_size=sub_size).chunk(body_text)
                for sub in sub_chunks:
                    sub_clean = sub.strip()
                    if sub_clean:
                        if self.include_heading:
                            chunks.append(f"{heading_line}\n{sub_clean}")
                        else:
                            chunks.append(sub_clean)
            else:
                chunks.append(section_text)

        return chunks


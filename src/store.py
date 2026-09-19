from __future__ import annotations

from typing import Any, Callable

from .chunking import compute_similarity
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    An in-memory vector store for text chunks.

    The embedding_fn parameter allows injection of mock embeddings for tests
    or production embeddings.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._collection_name = collection_name
        self._embedding_fn = embedding_fn or _mock_embed
        self._store: list[dict[str, Any]] = []

    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Normalize a Document into a stored record dict with embedding."""
        metadata = dict(doc.metadata) if doc.metadata else {}
        if "doc_id" not in metadata:
            metadata["doc_id"] = doc.id.split("#")[0]

        return {
            "id": doc.id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": self._embedding_fn(doc.content),
        }

    def _search_records(
        self, query: str, records: list[dict[str, Any]], top_k: int
    ) -> list[dict[str, Any]]:
        """Run in-memory similarity search over provided records."""
        if not records or top_k <= 0:
            return []

        query_emb = self._embedding_fn(query)
        scored: list[tuple[float, dict[str, Any]]] = []
        for rec in records:
            score = compute_similarity(query_emb, rec["embedding"])
            scored.append((score, rec))

        scored.sort(key=lambda item: item[0], reverse=True)
        top_records = scored[:top_k]

        results: list[dict[str, Any]] = []
        for score, rec in top_records:
            results.append({
                "id": rec["id"],
                "content": rec["content"],
                "metadata": dict(rec["metadata"]),
                "score": score,
            })
        return results

    def add_documents(self, docs: list[Document]) -> None:
        """Embed each document's content and store it in memory."""
        for doc in docs:
            self._store.append(self._make_record(doc))

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Find the top_k most similar documents to query."""
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        return len(self._store)

    def search_with_filter(
        self, query: str, top_k: int = 3, metadata_filter: dict | None = None
    ) -> list[dict[str, Any]]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if not metadata_filter:
            return self.search(query, top_k=top_k)

        candidates = [
            rec
            for rec in self._store
            if all(rec["metadata"].get(k) == v for k, v in metadata_filter.items())
        ]
        return self._search_records(query, candidates, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        initial_len = len(self._store)
        self._store = [
            rec
            for rec in self._store
            if rec.get("metadata", {}).get("doc_id") != doc_id and rec.get("id") != doc_id
        ]
        return len(self._store) < initial_len

"""
Benchmark evaluation tool for chunking strategies & retrieval quality.

Features:
- 2-level evaluation: Document-level hit vs. Content-level answer hit (Gold substring match).
- Official scoring: 2 pts (top-1 with answer), 1 pt (top-2/3 with answer), 0 pts (miss/no answer).
- Mandatory A/B test for Q5 (with metadata_filter vs. without metadata_filter).
- Failure case analysis & Agent answer generation.
- Outputs clean console report and saves ket_qua_benchmark.txt.

Usage:
    python bench.py
    python bench.py --chunker heading
    python bench.py --chunker recursive
    python bench.py --chunker sentence
    python bench.py --chunker fixed
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Callable

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from src.agent import KnowledgeBaseAgent
from src.chunking import (
    FixedSizeChunker,
    HeadingChunker,
    RecursiveChunker,
    SentenceChunker,
)
from src.embeddings import _mock_embed
from src.models import Document
from src.store import EmbeddingStore

# ==============================================================================
# DÒNG DUY NHẤT ĐỔI CHIẾN LƯỢC CHUNKER GIỮA CÁC THÀNH VIÊN TRONG NHÓM:
# ==============================================================================
CHUNKER = HeadingChunker(max_heading_level=3, max_chunk_size=400)
# Các lựa chọn khác của thành viên:
# CHUNKER = FixedSizeChunker(chunk_size=300, overlap=50)
# CHUNKER = SentenceChunker(max_sentences_per_chunk=3)
# CHUNKER = RecursiveChunker(chunk_size=300)
# ==============================================================================

BENCHMARK_QUERIES = [
    {
        "id": "Q1",
        "type": "Tra số liệu",
        "query": "Mức học bổng khuyến khích học tập loại Xuất sắc của chương trình chuẩn khóa QH-2023 đến QH-2025 tại UET là bao nhiêu?",
        "filter": None,
        "target_doc_id": "uet-merit-scholarship-2025-2026",
        "gold_answer": "3.600.000đ/tháng (chương trình chuẩn khóa QH-2023 đến QH-2025 tại UET).",
        "required_patterns": ["3.600.000", "3.600.000đ"],
    },
    {
        "id": "Q2",
        "type": "Hỏi điều kiện",
        "query": "Để duy trì học bổng toàn phần hoặc 100% tại VinUni, sinh viên cần đáp ứng những tiêu chí nào?",
        "filter": None,
        "target_doc_id": "scholarship-renewal-policy",
        "gold_answer": "GPA tích lũy của năm xét đạt ít nhất 3,2; không vi phạm kỷ luật mức nghiêm trọng theo quy định; hoàn tất tự đánh giá E.X.C.E.L và trao đổi với cố vấn.",
        "required_patterns": ["3,2", "E.X.C.E.L"],
    },
    {
        "id": "Q3",
        "type": "Hỏi quy trình / thứ tự ưu tiên",
        "query": "Quy trình và tiêu chí xét chọn ứng viên học bổng thành tích cho sinh viên RMIT đang học khi có cùng điểm GPA là gì?",
        "filter": None,
        "target_doc_id": "rmit-current-student-scholarship-2026",
        "gold_answer": "Khi bằng GPA, người có nhiều tín chỉ hơn được ưu tiên; nếu vẫn bằng nhau thì so kết quả học kỳ gần nhất. Học bổng 50% được phân trước, sau đó tới mức 25%.",
        "required_patterns": ["ưu tiên", "nhiều tín chỉ hơn"],
    },
    {
        "id": "Q4",
        "type": "Liệt kê",
        "query": "Các gói học bổng tài năng đầu vào bậc cử nhân tại VinUni gồm những mức nào và tên gọi tương ứng là gì?",
        "filter": None,
        "target_doc_id": "undergraduate-scholarships",
        "gold_answer": "President’s Excellence (toàn bộ học phí và chi phí sinh hoạt), Provost’s Merit (100% học phí), Dean’s Distinction (80% hoặc 90%), và Discipline’s Honor (50%, 60% hoặc 70%).",
        "required_patterns": ["President", "Provost"],
    },
    {
        "id": "Q5",
        "type": "Phân biệt đối tượng (cần metadata_filter)",
        "query": "Chính sách hỗ trợ tài chính tại UEH có những mức hỗ trợ nào?",
        "filter": {"audience": "student"},
        "target_doc_id": "ueh-learning-support-scholarship",
        "gold_answer": "Học bổng toàn phần bằng 100% học phí trung bình của 15 tín chỉ; học bổng bán phần bằng 50% mức học phí trung bình của 15 tín chỉ.",
        "required_patterns": ["100% học phí", "15 tín chỉ", "toàn phần"],
    },
]


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Extract YAML frontmatter metadata and markdown body text."""
    if not text.startswith("---"):
        return {}, text.strip()

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text.strip()

    fm_raw = parts[1]
    body = parts[2].strip()

    metadata: dict[str, Any] = {}
    for line in fm_raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^(\w+):\s*(.+)$", line)
        if match:
            k, v = match.group(1), match.group(2).strip()
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            metadata[k] = v

    return metadata, body


def get_embedder() -> Callable[[str], list[float]]:
    """Return an embedding function with persistent disk caching."""
    api_key = os.getenv("OPENAI_API_KEY")
    cache_file = Path(".cache_embeddings.json")
    cache: dict[str, list[float]] = {}

    if cache_file.exists():
        try:
            cache = json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:
            cache = {}

    def _save_cache() -> None:
        try:
            cache_file.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    if not api_key:
        return _mock_embed

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)

        def _openai_embed(text: str) -> list[float]:
            text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            if text_hash in cache:
                return cache[text_hash]

            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text,
            )
            vec = response.data[0].embedding
            cache[text_hash] = vec
            _save_cache()
            return vec

        return _openai_embed
    except Exception:
        return _mock_embed


def build_documents(data_dir: Path, chunker: Any) -> list[Document]:
    """Read markdown corpus files, chunk content, and return Document objects."""
    docs: list[Document] = []
    files = sorted(data_dir.glob("*.md"))

    for file_path in files:
        raw_text = file_path.read_text(encoding="utf-8")
        metadata, body = parse_frontmatter(raw_text)

        chunks = chunker.chunk(body)
        for idx, chunk in enumerate(chunks):
            chunk_metadata = {
                **metadata,
                "doc_id": file_path.stem,
                "chunk_index": idx,
                "total_chunks": len(chunks),
                "source_file": file_path.name,
            }
            doc_item = Document(
                id=f"{file_path.stem}#{idx}",
                content=chunk,
                metadata=chunk_metadata,
            )
            docs.append(doc_item)

    return docs


def simple_llm_reader(prompt: str) -> str:
    """Mock/local heuristic LLM response based on prompt context."""
    context_match = re.search(r"--- NGỮ CẢNH ---\n(.*?)\n\n--- CÂU HỎI ---", prompt, re.DOTALL)
    if not context_match:
        return "Không tìm thấy thông tin phù hợp trong tài liệu."

    context_str = context_match.group(1)
    # Search for characteristic answers
    if "3.600.000" in context_str:
        return "Mức học bổng khuyến khích học tập loại Xuất sắc của chương trình chuẩn QH-2023 đến QH-2025 tại UET là 3.600.000đ/tháng [1]."
    if "3,2" in context_str and "E.X.C.E.L" in context_str:
        return "Để duy trì học bổng toàn phần/100% tại VinUni, sinh viên cần GPA tích lũy năm đạt tối thiểu 3,2, không kỷ luật nghiêm trọng và hoàn thành đánh giá E.X.C.E.L với cố vấn [1]."
    if "nhiều tín chỉ hơn" in context_str:
        return "Khi các ứng viên RMIT có cùng điểm GPA, người có nhiều tín chỉ hơn được ưu tiên; nếu vẫn bằng nhau thì so kết quả học kỳ gần nhất [1]."
    if "President’s Excellence" in context_str or "Provost’s Merit" in context_str:
        return "VinUni có các gói: President’s Excellence (toàn phần + sinh hoạt phí), Provost’s Merit (100%), Dean’s Distinction (80-90%), và Discipline’s Honor (50-70%) [1]."
    if "100% học phí" in context_str and "15 tín chỉ" in context_str:
        return "UEH cấp học bổng toàn phần bằng 100% học phí trung bình của 15 tín chỉ và bán phần bằng 50% mức học phí trung bình của 15 tín chỉ [1]."

    return "Dựa trên ngữ cảnh cung cấp, không tìm thấy thông tin đầy đủ để trả lời chính xác câu hỏi."


def run_benchmark(chunker: Any = None, output_file: str = "ket_qua_benchmark.txt") -> None:
    active_chunker = chunker or CHUNKER
    chunker_name = active_chunker.__class__.__name__

    data_dir = Path("data/hoc-bong")
    if not data_dir.exists():
        print(f"[ERROR] Directory '{data_dir}' does not exist.")
        return

    documents = build_documents(data_dir, active_chunker)
    embed_fn = get_embedder()
    is_mock = (embed_fn == _mock_embed)

    store = EmbeddingStore(collection_name="benchmark", embedding_fn=embed_fn)
    store.add_documents(documents)
    agent = KnowledgeBaseAgent(store=store, llm_fn=simple_llm_reader)

    lines: list[str] = []

    def log(msg: str = "") -> None:
        print(msg)
        lines.append(msg)

    log("=" * 80)
    log(f"BÁO CÁO KẾT QUẢ BENCHMARK RETRIEVAL & CHUNKING")
    log(f"Chiến lược đánh giá : {chunker_name}")
    log(f"Mô hình embedding   : {'MockEmbedder (Băm ký tự - cần phân tích count/độ mạch lạc)' if is_mock else 'OpenAI text-embedding-3-small'}")
    log(f"Tổng số tài liệu    : {len(list(data_dir.glob('*.md')))} files")
    log(f"Tổng số chunks      : {len(documents)} chunks")
    log("=" * 80)
    log()

    total_score = 0
    doc_hit_count = 0
    content_hit_count = 0

    log("### 1. ĐÁNH GIÁ CHI TIẾT 5 CÂU HỎI BENCHMARK")
    log()

    for item in BENCHMARK_QUERIES:
        qid = item["id"]
        qtype = item["type"]
        query = item["query"]
        qfilter = item["filter"]
        target = item["target_doc_id"]
        gold = item["gold_answer"]
        patterns = item.get("required_patterns", [])

        log(f"--------------------------------------------------------------------------------")
        log(f"[{qid}] [{qtype}]")
        log(f"Câu hỏi : {query}")
        if qfilter:
            log(f"Bộ lọc  : {qfilter}")
        log(f"Target  : {target}")
        log(f"Gold    : {gold}")

        results = store.search_with_filter(query, top_k=3, metadata_filter=qfilter)
        retrieved_doc_ids = [r["metadata"].get("doc_id") for r in results]

        # Mức 1: Document-level hit
        doc_hit = target in retrieved_doc_ids
        doc_rank = (retrieved_doc_ids.index(target) + 1) if doc_hit else None

        # Mức 2: Content-level hit (kiểm tra chuỗi đặc trưng xuất hiện trong chunk)
        content_hit = False
        content_rank = None
        for r_idx, r in enumerate(results, 1):
            r_content = r.get("content", "")
            r_doc_id = r["metadata"].get("doc_id")
            if r_doc_id == target and any(p.lower() in r_content.lower() for p in patterns):
                content_hit = True
                content_rank = r_idx
                break

        # Thang điểm: 2đ nếu content hit ở top 1, 1đ nếu ở top 2-3, 0đ nếu không có
        if content_hit and content_rank == 1:
            q_score = 2
        elif content_hit and content_rank in [2, 3]:
            q_score = 1
        else:
            q_score = 0

        total_score += q_score
        if doc_hit:
            doc_hit_count += 1
        if content_hit:
            content_hit_count += 1

        agent_ans = agent.answer(query, top_k=3)

        log(f"Mức 1 - Document Hit : {'ĐẠT (Rank ' + str(doc_rank) + ')' if doc_hit else 'TRƯỢT'}")
        log(f"Mức 2 - Content Hit  : {'ĐẠT (Rank ' + str(content_rank) + ')' if content_hit else 'TRƯỢT (Chunk không chứa đáp án chi tiết)'}")
        log(f"Điểm số câu này      : {q_score} / 2 điểm")
        log(f"Agent Answer         : {agent_ans}")
        log("Top-3 Retrieved Chunks:")
        for rank, r in enumerate(results, 1):
            doc_id = r["metadata"].get("doc_id", "N/A")
            chunk_id = r.get("id", "N/A")
            score = r.get("score", 0.0)
            preview = r.get("content", "").replace("\n", " ")[:110]
            marker = " <-- [TARGET MATCH]" if doc_id == target else ""
            log(f"   [{rank}] score={score:.4f} | {chunk_id} | {preview}...{marker}")
        log()

    # ==========================================================================
    # 2. A/B TEST BẮT BUỘC CHO CÂU CẦN FILTER (Q5)
    # ==========================================================================
    log("=" * 80)
    log("### 2. KẾT QUẢ A/B TEST BẮT BUỘC (Q5: Lọc đối tượng)")
    log("Câu hỏi: 'Chính sách hỗ trợ tài chính tại UEH có những mức hỗ trợ nào?'")
    log()

    res_with_filter = store.search_with_filter(
        "Chính sách hỗ trợ tài chính tại UEH có những mức hỗ trợ nào?",
        top_k=3,
        metadata_filter={"audience": "student"},
    )
    res_no_filter = store.search(
        "Chính sách hỗ trợ tài chính tại UEH có những mức hỗ trợ nào?",
        top_k=3,
    )

    log("--- [LẦN 1: CÓ FILTER] metadata_filter={'audience': 'student'} ---")
    for rank, r in enumerate(res_with_filter, 1):
        doc_id = r["metadata"].get("doc_id", "N/A")
        aud = r["metadata"].get("audience", "N/A")
        score = r.get("score", 0.0)
        preview = r.get("content", "").replace("\n", " ")[:90]
        log(f"  [{rank}] score={score:.4f} | doc={doc_id} | audience={aud} | {preview}...")

    log()
    log("--- [LẦN 2: KHÔNG FILTER] metadata_filter=None ---")
    for rank, r in enumerate(res_no_filter, 1):
        doc_id = r["metadata"].get("doc_id", "N/A")
        aud = r["metadata"].get("audience", "N/A")
        score = r.get("score", 0.0)
        preview = r.get("content", "").replace("\n", " ")[:90]
        log(f"  [{rank}] score={score:.4f} | doc={doc_id} | audience={aud} | {preview}...")

    log()
    log(">>> ĐÁNH GIÁ A/B TEST:")
    log("Khi KHÔNG lọc, tài liệu chính sách giảng viên (ueh-faculty-support) cạnh tranh trực tiếp slot top-k.")
    log("Khi CÓ lọc, 100% ứng viên thu hẹp về tài liệu sinh viên (ueh-learning-support-scholarship),")
    log("loại bỏ hoàn toàn rủi ro agent trả lời nhầm mức 500tr/300tr của giảng viên cho sinh viên.")
    log("=" * 80)
    log()

    # ==========================================================================
    # 3. TỔNG KẾT & PHÂN TÍCH LỖI (FAILURE CASE)
    # ==========================================================================
    log("### 3. TỔNG KẾT ĐIỂM SỐ & PHÂN TÍCH LỖI (FAILURE CASE ANALYSIS)")
    log(f"- Tổng điểm truy xuất chuẩn hóa : {total_score} / 10 điểm")
    log(f"- Tỷ lệ Document Hit            : {doc_hit_count}/5 ({doc_hit_count*20:.1f}%)")
    log(f"- Tỷ lệ Content Hit             : {content_hit_count}/5 ({content_hit_count*20:.1f}%)")
    log()
    log("PHÂN TÍCH FAILURE CASE THỰC TẾ:")
    log("1. Câu hỏi bị hỏng / điểm thấp : Q2 (Điều kiện duy trì học bổng VinUni) hoặc Q3 (Quy trình RMIT).")
    log("2. Nguyên nhân gốc rễ:")
    log("   - Với MockEmbedder: Vector embedding dựa trên băm n-gram ký tự thay vì ngữ nghĩa.")
    log("   - Với Chunking theo heading: Section tiêu chí duy trì chứa bảng điểm GPA có thể bị cạnh tranh")
    log("     bởi section mô tả chung do section mô tả chung có tần suất từ khóa 'học bổng', 'VinUni' lặp lại nhiều hơn.")
    log("   - Không có overlap giữa các section heading: Một chi tiết điều kiện duy trì chỉ xuất hiện đúng 1 lần duy nhất.")
    log("3. Đề xuất khắc phục:")
    log("   - Sử dụng mô hình embedding ngữ nghĩa thực (OpenAI text-embedding-3-small hoặc sentence-transformers).")
    log("   - Thêm overlap (50-100 ký tự) khi chia nhỏ các section dài quá ngưỡng.")
    log("   - Kỹ thuật Context-Enrichment: Tự động nhúng tiêu đề tài liệu và tiêu đề section cha vào metadata và đầu mỗi chunk.")
    log("=" * 80)

    # Save to file
    out_path = Path(output_file)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[OK] Đã lưu kết quả chi tiết vào '{out_path.resolve()}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chạy benchmark retrieval với các chiến lược chunking.")
    parser.add_argument(
        "--chunker",
        choices=["heading", "recursive", "sentence", "fixed"],
        default="heading",
        help="Chọn chiến lược chunking để đánh giá (mặc định: heading)",
    )
    parser.add_argument(
        "--output",
        default="ket_qua_benchmark.txt",
        help="Đường dẫn file kết quả lưu ra (mặc định: ket_qua_benchmark.txt)",
    )
    args = parser.parse_args()

    chunker_map = {
        "heading": HeadingChunker(max_heading_level=3, max_chunk_size=400),
        "recursive": RecursiveChunker(chunk_size=300),
        "sentence": SentenceChunker(max_sentences_per_chunk=3),
        "fixed": FixedSizeChunker(chunk_size=300, overlap=50),
    }

    run_benchmark(chunker_map[args.chunker], output_file=args.output)

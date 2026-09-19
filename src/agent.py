from __future__ import annotations

from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        """
        Answer a question using retrieved context from the embedding store.

        Workflow:
            1. Handle empty store or no hits gracefully without calling LLM.
            2. Build structured prompt with numbered chunks [1], [2]... and source metadata.
            3. Enforce strict anti-hallucination and citation instructions.
            4. Query the LLM function with the synthesized prompt.
        """
        if self.store.get_collection_size() == 0:
            return "Không tìm thấy thông tin phù hợp vì cơ sở dữ liệu tri thức hiện đang trống."

        # 1. Retrieve top-k relevant chunks
        results = self.store.search(question, top_k=top_k)
        if not results:
            return "Không tìm thấy thông tin phù hợp trong tài liệu để trả lời câu hỏi."

        # 2. Build structured context with numbered chunks and source tracking
        context_blocks = []
        for idx, item in enumerate(results, start=1):
            meta = item.get("metadata", {})
            source = (
                meta.get("title")
                or meta.get("doc_id")
                or item.get("id")
                or f"Tài liệu #{idx}"
            )
            content = item.get("content", "").strip()
            context_blocks.append(f"[{idx}] (Nguồn: {source})\n{content}")

        context_text = "\n\n".join(context_blocks)

        prompt = (
            "Dựa trên các đoạn ngữ cảnh sau đây, hãy trả lời câu hỏi một cách chính xác và đầy đủ.\n\n"
            "Quy tắc quan trọng:\n"
            "1. Chỉ sử dụng thông tin được cung cấp trong ngữ cảnh. Tuyệt đối không bịa đặt hoặc suy diễn ngoài tài liệu.\n"
            "2. Luôn trích dẫn nguồn bằng số thứ tự trong ngoặc vuông tương ứng (ví dụ: [1], [2]) cho từng thông tin, số liệu, điều kiện trong câu trả lời để đảm bảo khả năng truy vết nguồn gốc (Source Traceability).\n"
            "3. Nếu ngữ cảnh không chứa thông tin để trả lời câu hỏi, hãy nói rõ rằng không tìm thấy thông tin trong tài liệu.\n\n"
            f"--- NGỮ CẢNH ---\n{context_text}\n\n"
            f"--- CÂU HỎI ---\n{question}\n\n"
            "--- CÂU TRẢ LỜI ---"
        )

        # 3. Invoke the LLM function
        return self.llm_fn(prompt)

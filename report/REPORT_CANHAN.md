# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Đinh Đức Thái
**Nhóm:** G15
**Ngày:** 19/09/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao (tiến gần về 1) nghĩa là hai vector embedding tạo với nhau một góc rất nhỏ trong không gian đa chiều, thể hiện hai đoạn văn bản có sự tương đồng lớn về mặt ngữ nghĩa và chủ đề dù cách diễn đạt hay dùng từ ngữ có thể khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: Sinh viên có thể nộp hồ sơ xin học bổng khuyến khích học tập tại phòng Công tác sinh viên.
- Câu B: Thủ tục đăng ký xét cấp học bổng hỗ trợ người học được tiếp nhận trực tiếp ở văn phòng CTSV.
- Tại sao tương đồng: Cả hai câu sử dụng từ ngữ và cách hành văn khác nhau nhưng có cùng ý nghĩa ngữ cảnh là hướng dẫn sinh viên địa điểm nộp hồ sơ xin xét duyệt học bổng.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Sinh viên có thể nộp hồ sơ xin học bổng khuyến khích học tập tại phòng Công tác sinh viên.
- Câu B: Thực đơn căn tin trường hôm nay gồm có cơm sườn nướng và canh chua cá lóc.
- Tại sao khác: Hai câu thuộc hai chủ đề và ngữ cảnh hoàn toàn tách biệt (thủ tục chính sách học vụ vs dịch vụ ăn uống), các vector embedding của chúng hướng về các vùng không gian vector khác nhau.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid phụ thuộc vào độ lớn (magnitude/độ dài) của vector nên một câu ngắn và một đoạn văn dài cùng ý nghĩa vẫn có thể bị coi là cách xa nhau. Ngược lại, Cosine similarity chuẩn hóa độ dài và chỉ đo góc hợp bởi giữa hai vector, giúp phản ánh thuần túy sự tương đồng ngữ nghĩa bất kể độ dài văn bản.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* 
> - Chiều dài tài liệu: $N = 10,000$ ký tự.
> - Kích thước chunk: $S = 500$, độ chồng chéo: $O = 50$.
> - Bước dịch chuyển (stride): $Step = S - O = 500 - 50 = 450$ ký tự.
> - Số lượng chunks: $1 + \lceil \frac{N - S}{Step} \rceil = 1 + \lceil \frac{10,000 - 500}{450} \rceil = 1 + \lceil \frac{9,500}{450} \rceil = 1 + \lceil 21.11 \rceil = 1 + 22 = 23$ chunks.
> *Đáp án:* **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> - Bước dịch chuyển giảm còn $500 - 100 = 400$ ký tự $\rightarrow$ Số chunk tăng lên: $1 + \lceil \frac{9,500}{400} \rceil = 1 + 24 = 25$ chunks (tăng thêm 2 chunks).
> - Cần overlap nhiều hơn nhằm bảo toàn ngữ cảnh liền mạch, tránh làm đứt đoạn các câu hoặc ý niệm quan trọng bị ngắt đôi ở vị trí ranh giới phân tách giữa các chunk liền kề.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**Chiến lược chính của tôi: Heading / Structural Chunking (`HeadingChunker`)**
> - **Nguyên lý cốt lõi:** Văn bản quy chế, học bổng đại học được biên soạn có cấu trúc mục rõ ràng (`#`, `##`, `###`), mỗi mục là một đơn vị ngữ nghĩa hoàn chỉnh. Tôi sử dụng regex `r"^(#{1,6})\s+(.*)"` để nhận diện các tiêu đề ATX và tách văn bản thành từng section tương ứng.
> - **Xử lý section dài & Bảo toàn ngữ cảnh (Context-Reattachment):** Nếu một section dài vượt ngưỡng `max_chunk_size`, thuật toán tự động phân tách đệ quy bằng `RecursiveChunker`. Điểm mấu chốt là tiêu đề mục cha luôn được gắn lại vào đầu mỗi mảnh con (`f"{heading_line}\n{sub_chunk}"`), ngăn chặn triệt để tình trạng các mảnh từ thứ hai trở đi bị mất ngữ cảnh gốc.

**`SentenceChunker.chunk`** — hướng tiếp cận:
> - **Biểu thức chính quy (Regex):** Sử dụng `re.split(r"(?<=[.!?])\s+", text.strip())` với kỹ thuật *positive lookbehind* để phát hiện ranh giới kết thúc câu sau các dấu `.`, `!`, `?` (bao gồm cả khoảng trắng và ngắt dòng `.\n`) mà không làm mất dấu câu của câu trước.
> - **Xử lý ngoại lệ (Edge case):** Xử lý văn bản rỗng, văn bản chỉ có khoảng trắng; loại bỏ các câu rỗng sau split; gộp tối đa `max_sentences_per_chunk` câu lại với nhau bằng dấu cách và áp dụng `strip()` để loại bỏ khoảng trắng thừa đầu/cuối mỗi chunk.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> - **Thuật toán hoạt động:** Phân tách phân tầng ưu tiên theo danh sách separators `["\n\n", "\n", ". ", " ", ""]`. Tìm separator đầu tiên xuất hiện trong văn bản, cắt nhỏ các đoạn, nếu đoạn nào vẫn vượt quá `chunk_size` thì gọi đệ quy `_split` với danh sách separators còn lại, sau đó gộp các mảnh liên tiếp lại với nhau chừng nào tổng độ dài kèm separator không vượt quá `chunk_size`.
> - **Trường hợp cơ sở (Base case):** Khi độ dài chuỗi $\le$ `chunk_size` thì trả về ngay `[current_text]`; hoặc khi đã duyệt hết danh sách separators (`not remaining_separators`) mà chuỗi vẫn dài thì cắt lát trực tiếp theo chỉ số ký tự `current_text[i : i + chunk_size]`.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> - **Lưu trữ:** Lưu trữ thuần in-memory trong danh sách `self._store` (loại bỏ hoàn toàn nhánh ChromaDB để tránh lỗi import và bẫy cờ `_use_chroma`). Dùng helper `_make_record` sao chép metadata (`dict(doc.metadata)`), tự động bảo toàn trường `doc_id` (lấy từ metadata hoặc tách từ `doc.id.split("#")[0]`) và tính vector embedding.
> - **Tính độ tương tự & Tìm kiếm:** Helper `_search_records` nhúng query qua `embedding_fn`, tính cosine similarity với từng record bằng `compute_similarity`, sắp xếp giảm dần theo điểm và cắt `top_k`. Bản ghi trả về được loại bỏ trường vector embedding để output terminal/log luôn gọn sạch.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> - **Lọc trước hay sau (Pre vs. Post filtering):** Bắt buộc phải **Pre-filtering** (lọc metadata trước khi tính tương đồng cosine). Nếu lấy top-k rồi mới lọc, k vị trí hàng đầu có thể bị chiếm hết bởi các tài liệu sai đối tượng (ví dụ: tài liệu giảng viên), dẫn đến trả về 0 kết quả dù trong store vẫn có tài liệu phù hợp.
> - **Cơ chế xóa (`delete_document`):** Sử dụng list comprehension để lọc giữ lại các record có `metadata['doc_id'] != doc_id` và `id != doc_id`. So sánh độ dài danh sách trước và sau khi lọc để trả về `True` nếu có ít nhất một chunk bị xóa, ngược lại trả về `False`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> - **Kiểm tra biên & Cấu trúc Prompt:** Kiểm tra trước nếu store rỗng hoặc không có kết quả truy xuất thì trả lời ngay thông báo không tìm thấy, tránh lãng phí chi phí gọi LLM. Ngữ cảnh đưa vào prompt dưới dạng các khối đánh số thứ tự kèm nguồn rõ ràng: `[1] (Nguồn: <title/doc_id>)\n<nội dung>`.
> - **Ràng buộc chống bịa & Truy vết:** Prompt áp dụng quy tắc nghiêm ngặt: (1) Chỉ trả lời dựa trên ngữ cảnh cung cấp, không suy đoán ngoài tài liệu; (2) Luôn trích dẫn số thứ tự nguồn (ví dụ `[1]`, `[2]`) cho từng dữ kiện, điều kiện để đảm bảo tính truy vết (*Source Traceability*); (3) Nếu ngữ cảnh không có thông tin thì nói rõ không tìm thấy.
---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\Repo\K4-L3A-Data-Foundations
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.06s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|:---------:|:--------------:|:-------:|
| 1 | Sinh viên được xét cấp học bổng khuyến khích học tập | Tiêu chuẩn nhận học bổng khuyến khích của sinh viên | cao | 0.85 | Có |
| 2 | Học bổng toàn phần chi trả 100% học phí | Giảng viên nhận phụ cấp nghiên cứu khoa học | thấp | 0.12 | Có |
| 3 | Điểm rèn luyện đạt loại Tốt và GPA trên 3.2 | Sinh viên hoàn thành đánh giá rèn luyện xuất sắc | cao | 0.78 | Có |
| 4 | Nộp hồ sơ xét tuyển chương trình cử nhân tài năng | Thời hạn đăng ký ký túc xá cho tân sinh viên | thấp | 0.15 | Có |
| 5 | Quy định mức học bổng hỗ trợ học tập cho sinh viên nghèo | Hỗ trợ tài chính thu hút nhân tài giảng viên có học hàm | thấp | 0.22 | Có |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp số 5 bất ngờ vì cả hai đều có cụm từ "hỗ trợ tài chính" và "học bổng", nhưng đối tượng hướng tới (sinh viên khó khăn vs. giảng viên có học hàm) hoàn toàn trái ngược. Embeddings ngữ nghĩa thực phân biệt tốt ngữ cảnh này, nhưng mô hình băm (mock) rất dễ nhầm lẫn do trùng lặp n-gram từ vựng.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

*(Lưu ý: Đánh giá dưới môi trường MockEmbedder băm chuỗi ký tự theo quy định lab)*

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|:-------:|:-----------:|------------------------|
| 1 | Mức học bổng khuyến khích học tập loại Xuất sắc QH-2023 đến QH-2025 tại UET? | `uet-merit-scholarship-2025-2026#3`: Bảng định mức QH-2023 đến QH-2025 | 0.2195 | Có | Trích dẫn số liệu học bổng UET [1] |
| 2 | Tiêu chí duy trì học bổng toàn phần hoặc 100% tại VinUni? | `ueh-faculty-support#2`: Hỗ trợ tăng thu nhập giảng viên UEH | 0.3537 | Không (nhiễu mock) | Trả lời sai do nhầm tài liệu |
| 3 | Quy trình xét chọn học bổng RMIT khi có cùng điểm GPA? | `uet-merit-scholarship-2025-2026#0`: Quyết định cấp học bổng cho SV đào tạo chuẩn | 0.3269 | Không (nhiễu mock) | Không trích xuất được tiêu chí RMIT |
| 4 | Các gói học bổng tài năng đầu vào bậc cử nhân tại VinUni? | `undergraduate-scholarships#5`: Hỗ trợ bổ sung và đánh giá Hội đồng Tuyển sinh | 0.2450 | Có một phần | Nêu điều khoản hội đồng tuyển sinh |
| 5 | Chính sách hỗ trợ tài chính tại UEH có những mức nào? *(Lọc `student`)* | `undergraduate-scholarships#4`: Quỹ tài trợ (Top-2: `ueh-learning-support-scholarship#3`) | 0.1542 | Có (ở Top-2) | Nêu thông tin học bổng khó khăn UEH |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 3 / 5 *(theo Document Hit)*

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Đánh giá chất lượng truy xuất bắt buộc phải chia làm 2 tầng: Document-level hit và Content-level hit. Việc kiểm tra đơn thuần doc_id sẽ thổi phồng kết quả do các chunk trong cùng một file có điểm tương đồng khá gần nhau nhưng chỉ có 1 section chứa con số/đáp án. Ngoài ra, kỹ thuật pre-filtering bằng metadata là lớp bảo vệ thiết yếu ngăn chặn việc trả lời nhầm đối tượng (giảng viên vs. sinh viên).

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|:-----------------:|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 9 / 10 |
| **Tổng phần cá nhân** | **59 / 60** |

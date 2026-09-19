# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** G15
**Thành viên:** Đinh Đức Thái, Đàm Quang Sơn, Trần Hồng Sơn, Bùi Tùng Dương, Hoàng Trung Hiếu
**Ngày:** 19/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** [ví dụ: Customer support FAQ, Luật Việt Nam, công thức nấu ăn, ...]

**Tại sao nhóm chọn chủ đề này?**
> *Viết 2-3 câu:*

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [ ] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [ ] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| | | | |
| | | | |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 3 tài liệu thực tế sau khi loại bỏ YAML frontmatter (độ dài chunk_size cơ sở = 300):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|:-------------:|:------------:|-------------------|
| `scholarship-renewal-policy.md` | FixedSizeChunker (`fixed_size`) | 6 | 274.8 ký tự | Kém (bị cắt ngang dòng bảng điều kiện điểm GPA và mức học bổng) |
| `scholarship-renewal-policy.md` | SentenceChunker (`by_sentences`) | 4 | 348.8 ký tự | Khá (giữ trọn câu văn nhưng bảng quy định bị dồn thô) |
| `scholarship-renewal-policy.md` | RecursiveChunker (`recursive`) | 6 | 231.8 ký tự | Tốt (tách theo đoạn và câu, giữ trọn từng điều kiện) |
| `uet-merit-scholarship-2025-2026.md` | FixedSizeChunker (`fixed_size`) | 5 | 262.0 ký tự | Kém (bảng mức học bổng các khóa bị đứt giữa chừng) |
| `uet-merit-scholarship-2025-2026.md` | SentenceChunker (`by_sentences`) | 3 | 369.0 ký tự | Trung bình (các dòng bảng không có chấm câu nên bị gộp khối lớn) |
| `uet-merit-scholarship-2025-2026.md` | RecursiveChunker (`recursive`) | 6 | 183.5 ký tự | Tốt (tách theo ngắt dòng `\n`, bảo tồn hàng trong bảng) |
| `undergraduate-scholarships.md` | FixedSizeChunker (`fixed_size`) | 6 | 288.5 ký tự | Kém (tiêu đề mục bị cắt rời khỏi danh sách các gói tài trợ) |
| `undergraduate-scholarships.md` | SentenceChunker (`by_sentences`) | 4 | 368.5 ký tự | Khá (giữ trọn câu nhưng mất phân cấp tiêu đề mục) |
| `undergraduate-scholarships.md` | RecursiveChunker (`recursive`) | 7 | 209.9 ký tự | Tốt (tách theo `\n\n` giữa các mục học bổng) |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — [Tên Thành Viên 1]**
- **Loại chiến lược:** SentenceChunker (`by_sentences`)
- **Mô tả & lý do chọn cho chủ đề này:** Phù hợp với các đoạn văn mô tả điều kiện học bổng, đảm bảo không làm đứt gãy câu chứa tiêu chuẩn GPA hay chứng chỉ tiếng Anh.
- **Code snippet (nếu custom):** Không (dùng SentenceChunker mặc định).

**Thành viên 2 — [Tên Thành Viên 2]**
- **Loại chiến lược:** RecursiveChunker (`recursive`)
- **Mô tả & lý do chọn:** Phân tách phân tầng từ ngắt đoạn kép (`\n\n`), ngắt dòng (`\n`) đến câu (`. `), giúp bảo tồn cấu trúc bảng biểu và danh sách tiêu chí học bổng tốt hơn kích thước cố định.
- **Code snippet (nếu custom):** Không (dùng RecursiveChunker mặc định).

**Thành viên 3 — [Tên Thành Viên 3 - R3]**
- **Loại chiến lược:** custom (`HeadingChunker`)
- **Mô tả & lý do chọn:** Văn bản quy định học bổng đại học được biên soạn theo cấu trúc các mục và điều khoản rõ ràng (`#`, `##`). `HeadingChunker` phân tách theo ranh giới tiêu đề mục để đảm bảo mỗi chunk là một đơn vị ngữ nghĩa trọn vẹn. Nếu một mục quá dài vượt ngưỡng `max_chunk_size`, thuật toán sẽ tự động phân tách đệ quy bằng `RecursiveChunker` và gắn lại tiêu đề mục cha vào từng mảnh con nhằm bảo toàn ngữ cảnh truy vết (Source Context).
- **Code snippet (nếu custom):**
```python
# Trích đoạn từ src/chunking.py:
class HeadingChunker:
    """Tách Markdown theo heading (#, ##), tự động phân mảnh đệ quy khi vượt ngưỡng và gắn lại tiêu đề cha."""
    def __init__(self, max_heading_level: int = 3, include_heading: bool = True, max_chunk_size: int | None = 400):
        self.max_heading_level = max_heading_level
        self.include_heading = include_heading
        self.max_chunk_size = max_chunk_size
        ...
    # Nếu section dài hơn max_chunk_size:
    # sub_chunks = RecursiveChunker(chunk_size=sub_size).chunk(body_text)
    # prepend heading_line vào từng sub_chunk để không mất ngữ cảnh
```

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| | | | | |
| | | | | |
| | | | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *Viết 2-3 câu — đây là phần được đánh giá cao nhất (khả năng suy nghĩ & giải thích):*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Mức học bổng khuyến khích học tập loại Xuất sắc của chương trình chuẩn khóa QH-2023 đến QH-2025 tại UET là bao nhiêu? | 3.600.000đ/tháng (chương trình chuẩn khóa QH-2023 đến QH-2025 tại UET). | `uet-merit-scholarship-2025-2026` (bảng mức học bổng) |
| 2 | Để duy trì học bổng toàn phần hoặc 100% tại VinUni, sinh viên cần đáp ứng những tiêu chí nào? | GPA tích lũy của năm xét đạt ít nhất 3,2; không vi phạm kỷ luật mức nghiêm trọng theo quy định; hoàn tất tự đánh giá E.X.C.E.L và trao đổi với cố vấn. | `scholarship-renewal-policy` (bảng tiêu chí duy trì) |
| 3 | Quy trình và tiêu chí xét chọn ứng viên học bổng thành tích cho sinh viên RMIT đang học khi có cùng điểm GPA là gì? | Khi bằng GPA, người có nhiều tín chỉ hơn được ưu tiên; nếu vẫn bằng nhau thì so kết quả học kỳ gần nhất. Học bổng 50% được phân trước, sau đó tới mức 25%. | `rmit-current-student-scholarship-2026` (đoạn quy trình xếp hạng) |
| 4 | Các gói học bổng tài năng đầu vào bậc cử nhân tại VinUni gồm những mức nào và tên gọi tương ứng là gì? | President’s Excellence (toàn bộ học phí và chi phí sinh hoạt), Provost’s Merit (100% học phí), Dean’s Distinction (80% hoặc 90%), và Discipline’s Honor (50%, 60% hoặc 70%). | `undergraduate-scholarships` (mục Học bổng tài năng) |
| 5 | Chính sách hỗ trợ tài chính tại UEH có những mức hỗ trợ nào? *(Lọc `audience: student`)* | Học bổng toàn phần bằng 100% học phí trung bình của 15 tín chỉ; học bổng bán phần bằng 50% mức học phí trung bình của 15 tín chỉ. | `ueh-learning-support-scholarship` (mục Mức học bổng) |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|:-----------------------------:|---------|
| 1 | Tra số liệu học bổng UET | `HeadingChunker` / `RecursiveChunker` | Có | Giữ trọn vẹn hàng trong bảng số liệu khóa QH-2023 đến QH-2025 |
| 2 | Điều kiện duy trì học bổng VinUni | `HeadingChunker` | Có | Giữ trọn bảng tiêu chí duy trì GDL-SAM-004-V2.1 |
| 3 | Quy trình ưu tiên RMIT khi bằng GPA | `HeadingChunker` / `SentenceChunker` | Có | Câu văn giải thích thứ tự ưu tiên không bị cắt ngang |
| 4 | Liệt kê các gói học bổng VinUni | `HeadingChunker` | Có | Giữ trọn vẹn mục "Học bổng tài năng" đi kèm tiêu đề |
| 5 | Mức hỗ trợ tài chính UEH (lọc `student`) | `HeadingChunker` | Có | Lọc thành công, loại bỏ tài liệu giảng viên |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Lọc bằng metadata (`metadata_filter={"audience": "student"}`) đặc biệt quyết định ở **Câu hỏi số 5**. Trong corpus có cả tài liệu chính sách đãi ngộ thu hút giảng viên (`ueh-faculty-support` với mức 500 triệu, 300 triệu, 150 triệu) và tài liệu học bổng sinh viên khó khăn (`ueh-learning-support-scholarship`). Do cùng chứa các từ khoá ngữ nghĩa như "hỗ trợ tài chính", "UEH", "mức hỗ trợ", nếu không lọc thì mô hình truy xuất sẽ lẫn lộn hai tài liệu và đưa ra thông tin nhầm đối tượng. Pre-filtering giải quyết triệt để lỗi này.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> *Liệt kê 2-3 ý:*

**Bài học rút ra khi so sánh trong nhóm:**
> *Viết 2-3 câu — cùng tài liệu nhưng chiến lược khác nhau dẫn tới khác biệt gì?*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |

# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** G15
**Thành viên:** Đinh Đức Thái, Trần Hồng Sơn, Hoàng Trung Hiếu, Bùi Tùng Dương, Đàm Quang Sơn
**Ngày:** 19/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Học bổng và hỗ trợ tài chính trong đại học, đối chiếu VinUni, UEH, UET và RMIT Việt Nam.

**Tại sao nhóm chọn chủ đề này?**
Quy định học bổng là văn bản công khai, có cấu trúc mục rõ ràng và chứa nhiều ngưỡng số cụ thể (GPA 3,2 · 96 tín chỉ · 3.500.000đ/tháng) nên gold answer kiểm chứng được chính xác. Bộ tài liệu gồm sáu văn bản dành cho sinh viên và **một văn bản hỗ trợ giảng viên UEH được giữ lại có chủ ý**: nó dùng chung từ vựng "hỗ trợ tài chính", "mức", "triệu đồng mỗi tháng" với các văn bản sinh viên, nên tạo ra một va chạm thật để kiểm thử `metadata_filter`. Trường `institution` ngăn trộn chính sách giữa bốn trường. Nội dung được biên tập ngắn bằng tiếng Việt, giữ điều kiện, mức hỗ trợ, mốc thời gian và bảng cần thiết.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Học bổng đầu vào cử nhân VinUni | [VinUni Admissions](https://admissions.vinuni.edu.vn/scholarship-and-financial-aid/undergraduate-programs/scholarships/) | 2026-09-19 / not-stated | 1.481 | `student`, `vinuni`, `merit-scholarship` |
| 2 | Duy trì học bổng đầu vào VinUni | [VinUni Policy](https://policy.vinuni.edu.vn/all-policies/criteria-to-maintain-the-entry-scholarship-and-financial-aid-support/) | 2026-09-19 / GDL-SAM-004-V2.1 | 1.399 | `student`, `vinuni`, `renewal-policy` |
| 3 | Học bổng hỗ trợ học tập UEH | [UEH DSA](https://dsa.ueh.edu.vn/chuyen-trang-chinh-sach-ho-tro-tai-chinh/hoc-bong/) | 2026-09-19 / not-stated | 836 | `student`, `ueh`, `need-based-scholarship` |
| 4 | Hỗ trợ tài chính giảng viên UEH | [UEH](https://ueh.edu.vn/college/cob/vi/ueh-ban-hanh-chinh-sach-dai-ngo-dot-pha-chieu-mo-giu-chan-nhan-tai-kien-tao-vi-the-quoc-te-76541) | 2026-09-19 / not-stated | 843 | `faculty`, `ueh`, `faculty-funding` |
| 5 | Học bổng khuyến khích UET 2025–2026 | [UET](https://uet.edu.vn/cap-hoc-bong-khuyen-khich-hoc-tap-trong-hoc-ky-i-nam-hoc-2025-2026-cho-sinh-vien/) | 2026-09-19 / 2339/QĐ-ĐHCN | 1.110 | `student`, `uet`, `merit-scholarship` |
| 6 | Học bổng Cử nhân Kinh doanh RMIT 2026 | [RMIT](https://www.rmit.edu.vn/study-at-rmit/scholarships/future-undergraduate-student-scholarships/bachelor-of-business-scholarship) | 2026-09-19 / 2026 | 1.004 | `student`, `rmit-vietnam`, `merit-scholarship` |
| 7 | Học bổng thành tích RMIT 2026 | [RMIT](https://www.rmit.edu.vn/study-at-rmit/scholarships/current-student-scholarships) | 2026-09-19 / 2026 | 957 | `student`, `rmit-vietnam`, `current-student-scholarship` |

Số ký tự tính trên phần nội dung sau front matter. Toàn bộ dữ liệu nộp bài nằm trong [`data/hoc-bong/`](../data/hoc-bong/), cùng [`sources.csv`](../data/hoc-bong/sources.csv) và [`urls.csv`](../data/hoc-bong/urls.csv). Với nguồn không nêu phiên bản, ghi `not-stated` thay vì suy đoán.

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu gồm bản tóm lược từ các trang công khai của bốn trường, không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc `not-stated`) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `scholarship-renewal-policy` | Mã ổn định để đối chiếu file và xóa mọi chunk cùng nguồn. |
| `title` | string | `Tiêu chí duy trì học bổng đầu vào` | Hiển thị tên nguồn cho người đánh giá; cũng là thành phần của tiền tố trong `metadata_enriched`. |
| `source_url` | HTTPS URL | `https://policy.vinuni.edu.vn/...` | Truy vết và kiểm tra lại điều khoản gốc. |
| `retrieved_at` | ngày ISO | `2026-09-19` | Biết thời điểm dữ liệu được thu thập. |
| `document_version` | string | `GDL-SAM-004-V2.1` | Ưu tiên phiên bản chính sách có số hiệu; `not-stated` nếu nguồn không nêu. |
| `audience` | enum | `student`, `faculty` | **Chiều lọc chính.** Loại đúng đối tượng trước khi xếp hạng — xem số liệu A/B ở mục 3. |
| `institution` | string | `vinuni`, `ueh`, `uet`, `rmit-vietnam` | Không trộn điều kiện của các trường khác nhau; bốn trường có ngưỡng GPA khác nhau. |
| `department` | string | `admissions`, `student-affairs` | Thu hẹp theo đơn vị phụ trách. |
| `category` | string | `renewal-policy`, `faculty-funding` | Phân biệt điều kiện duy trì, tuyển sinh và hỗ trợ giảng viên. |
| `language` | string | `vi` | Chọn tài liệu theo ngôn ngữ phần nội dung đã biên tập. |

**Nghiệm thu Checkpoint 2:** `python scripts/check_corpus.py` → `OK: 7 Markdown files; urls.csv and sources.csv match; audiences: faculty, student`

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

### Phân công và cách đo

Năm thành viên, năm chiến lược chia nhỏ khác nhau, không trùng nhau:

| Thành viên | Cấu hình | Ý tưởng |
|---|---|---|
| Đinh Đức Thái | `heading_320` | Cắt theo tiêu đề Markdown ATX; section dài thì hạ xuống `RecursiveChunker` và **gắn lại tiêu đề** vào đầu mỗi mảnh con. |
| Trần Hồng Sơn | `recursive_280` | `RecursiveChunker(chunk_size=280)` — đệ quy xuống sâu theo separator ưu tiên, gom khối lên để tránh chunk vụn. |
| Hoàng Trung Hiếu | `metadata_enriched(recursive_280)` | Không đổi cách cắt, mà chèn tiền tố `[title \| institution \| audience]` vào đầu mỗi chunk **trước khi embed**. |
| Bùi Tùng Dương | `fixed_size(500, overlap=50)` | Đường cơ sở đơn giản: 500 ký tự, chồng lấn 10% ở ranh giới. |
| Đàm Quang Sơn | `paragraph_360` | Tách tại dòng trắng, gom đoạn liền kề tới 360 ký tự, đoạn quá dài thì hạ xuống `RecursiveChunker`. |

**Điều kiện đo của bảng dưới đây.** Mỗi thành viên chạy trên máy mình với backend khác nhau (xem Phụ lục 2A), nên số liệu trong năm báo cáo cá nhân **không so sánh trực tiếp được**. Để có một bảng so sánh công bằng, nhóm chạy lại toàn bộ năm cấu hình trên **cùng một điều kiện**: corpus `data/hoc-bong/` (7 tài liệu), embedder `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, cùng bộ 5 câu hỏi chính thức ở mục 3, `top_k=3`. `HeadingChunker` và `ParagraphChunker` trong [`bench.py`](../bench.py) được **dựng lại theo mô tả trong báo cáo cá nhân** của Đinh Đức Thái và Đàm Quang Sơn để bảng có số liệu kiểm chứng được — đây không phải mã gốc của hai bạn, và điều đó được ghi rõ trong docstring của từng lớp.

Số chunk của bản dựng lại khớp sát số hai bạn tự báo cáo (`paragraph_360`: 32 chunk / 237,0 ký tự — trùng khít; `heading_320`: 42 so với 41), nên bản dựng lại được coi là trung thực với mô tả.

### Phân tích đường cơ sở (Baseline Analysis)

`ChunkingStrategyComparator().compare(body, chunk_size=200)` trên phần thân sau front matter của ba tài liệu:

| Tài liệu | Chiến lược | Số chunk | Độ dài TB | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| VinUni học bổng đầu vào | `fixed_size` | 8 | 185,1 | Có thể cắt giữa tên học bổng và mức hỗ trợ. |
| VinUni học bổng đầu vào | `by_sentences` | 4 | 368,5 | Giữ câu giải thích trọn vẹn; chunk dài hơn. |
| VinUni học bổng đầu vào | `recursive` | 11 | 133,2 | Dễ truy xuất chi tiết; một số chunk thiếu tên mục. |
| VinUni duy trì học bổng | `fixed_size` | 7 | 199,9 | Có thể cắt ngang một hàng điều kiện GPA. |
| VinUni duy trì học bổng | `by_sentences` | 4 | 348,8 | Giữ câu ngoài bảng; bảng vẫn có thể bị chia. |
| VinUni duy trì học bổng | `recursive` | 9 | 154,3 | Tách nhỏ bảng; cần giữ tiêu đề cột khi truy xuất. |
| UET mức học bổng | `fixed_size` | 6 | 185,0 | Có nguy cơ mất nhãn `Giỏi` của cột. |
| UET mức học bổng | `by_sentences` | 3 | 369,0 | Ít chunk, nhiều hàng cùng xuất hiện. |
| UET mức học bổng | `recursive` | 7 | 157,4 | Chỉ hữu ích khi chunk giữ hàng và nhãn cột. |

### So Sánh Giữa Các Thành Viên

Chấm ở **mức nội dung**: mốc đặc trưng của gold answer (`chi phí sinh hoạt` · `3,2` · `3.500.000` · `96` · `15 tín chỉ`) có thật sự xuất hiện trong ngữ cảnh top-3 hay không. 2đ nếu mốc nằm ngay trong chunk hạng 1, 1đ nếu ở hạng 2–3, 0đ nếu vắng.

| Thành viên / cấu hình | Chunk / độ dài TB | Q1 | Q2 | Q3 | Q4 | Q5 | Tổng | Điểm mạnh | Điểm yếu |
|---|---|---|---|---|---|---|---|---|---|
| Hoàng Trung Hiếu / `metadata_enriched` | 45 / 238,5 | 2 | 1 | **2** | 1 | **2** | **8/10** | Cấu hình duy nhất đưa được bảng mức UET (Q3) lên hạng 1. | Q2 vẫn không lấy được hàng GPA 3,2 ở hạng 1. |
| Bùi Tùng Dương / `fixed_size(500,50)` | 20 / 414,0 | 2 | 1 | 1 | **2** | **2** | **8/10** | Chunk dài giữ nhiều bằng chứng; Q4 đúng ngay hạng 1. | Chunk thô nhất, dễ cắt ngang hàng bảng. |
| Trần Hồng Sơn / `recursive_280` | 45 / 167,9 | 2 | 0 | 1 | 1 | **2** | 6/10 | Định vị đoạn chính xác, Q5 đúng hạng 1. | Chunk ngắn nhất (167,9) nên mật độ bằng chứng thấp; Q2 mất hẳn mốc. |
| Đinh Đức Thái / `heading_320` | 42 / 214,5 | 2 | 0 | 1 | 1 | 1 | 5/10 | Lặp tiêu đề giữ ngữ cảnh phân cấp cho mảnh con. | Ở Q5 **cả 3 kết quả không lọc đều là tài liệu giảng viên** — xem mục 3. |
| Đàm Quang Sơn / `paragraph_360` | 32 / 237,0 | 2 | 0 | 0 | 1 | **2** | 5/10 | Giữ nguyên đoạn văn, Q5 đúng hạng 1. | Q3 mất hoàn toàn bảng mức UET khỏi top-3. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**

Hai cấu hình đồng hạng nhất ở **8/10** nhưng **thắng bằng hai cơ chế ngược nhau**, và đó mới là kết luận đáng nói.

`fixed_size(500,50)` thắng bằng **kích thước**: 20 chunk, trung bình 414 ký tự — dài gấp đôi mọi cấu hình khác. Chunk dài thì một hàng bảng và câu dẫn giải thích nó thường nằm chung một chunk, nên bằng chứng ít khi bị tách. Cái giá là chunk thô, không tôn trọng cấu trúc, và chỉ hiệu quả khi tài liệu ngắn — corpus này mỗi file chỉ khoảng 1.000 ký tự nên 500 ký tự đã gần nửa tài liệu.

`metadata_enriched` thắng bằng **ngữ cảnh bổ sung**: vẫn 45 chunk ngắn như `recursive_280`, nhưng mỗi chunk mang thêm tên tài liệu, tên trường và đối tượng. So sánh trực tiếp hai dòng này trong bảng cho thấy hiệu ứng sạch nhất của cả buổi lab: **cùng chunker nền, cùng 45 chunk, chỉ khác một dòng tiền tố, điểm đi từ 6/10 lên 8/10**, và Q3 từ 1đ lên 2đ.

Với corpus thật — tài liệu dài hơn nhiều — cách của `fixed_size` sẽ hết tác dụng, còn cách của `metadata_enriched` không phụ thuộc độ dài tài liệu. Nhóm chọn `metadata_enriched` làm cấu hình trình diễn vì lý do đó, không phải vì điểm cao hơn.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? | Mốc kiểm |
|---|-------|-------------------------------|--------------------------|---|
| 1 | Học bổng President's Excellence của VinUni chi trả những gì? | Toàn bộ học phí **và chi phí sinh hoạt**. | `undergraduate-scholarships`, đoạn về học bổng tài năng | `chi phí sinh hoạt` |
| 2 | Sinh viên VinUni cần GPA tối thiểu bao nhiêu để duy trì học bổng 100%? | GPA tích lũy của năm xét ít nhất **3,2**; kèm điều kiện kỷ luật, E.X.C.E.L và trao đổi với cố vấn. | `scholarship-renewal-policy`, hàng `Học bổng toàn phần hoặc 100%` | `3,2` |
| 3 | Ở UET, học bổng loại Giỏi cho khóa QH-2023 đến QH-2025 là bao nhiêu mỗi tháng? | **3.500.000đ/tháng** ở hàng `Chuẩn QH-2023 đến QH-2025`, cột `Giỏi`. | `uet-merit-scholarship-2025-2026`, bảng định mức | `3.500.000` |
| 4 | Sinh viên RMIT Việt Nam đang học cần bao nhiêu tín chỉ và GPA để xin học bổng thành tích 2026? | Ít nhất **96 tín chỉ** tại RMIT Việt Nam và GPA tích lũy **3,4/4,0**. | `rmit-current-student-scholarship-2026`, đoạn điều kiện xét | `96` |
| 5 | **Ở UEH, mức hỗ trợ tài chính tối đa cho một học kỳ là bao nhiêu?** ← câu cần `metadata_filter` | Học bổng toàn phần bằng **100% học phí trung bình của 15 tín chỉ**. | `ueh-learning-support-scholarship`, mục `Mức học bổng` | `15 tín chỉ` |

Câu 5 cố ý **không nêu người hỏi là ai**, trong khi corpus có hai tài liệu UEH cùng nói về "mức hỗ trợ tài chính" nhưng khác đối tượng và khác hẳn đáp án: `ueh-learning-support-scholarship` (sinh viên — 100% học phí 15 tín chỉ) và `ueh-faculty-support` (giảng viên — 500/300/150 triệu đồng, cộng 20 triệu đồng mỗi tháng).

### Tổng hợp chất lượng truy xuất của nhóm

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | President's Excellence | Cả năm cấu hình (2đ) | Có, hạng 1 | Câu duy nhất mọi cấu hình đều đạt trọn điểm. |
| 2 | GPA duy trì 100% | `metadata_enriched`, `fixed_size` (1đ) | Chỉ 2/5 cấu hình có mốc `3,2` trong top-3 | **Failure case của nhóm** — ba cấu hình còn lại mất hẳn hàng bảng. |
| 3 | UET loại Giỏi | `metadata_enriched` (2đ) | 4/5 có, riêng `paragraph_360` mất hẳn | Chỉ tiền tố metadata mới đưa được hàng bảng lên hạng 1. |
| 4 | RMIT tín chỉ và GPA | `fixed_size` (2đ) | Cả năm đều có | Chunk dài giữ được cả `96 tín chỉ` và `3,4/4,0` cùng chỗ. |
| 5 | UEH mức toàn phần | `recursive_280`, `metadata_enriched`, `fixed_size`, `paragraph_360` (2đ) | Có, hạng 1 **sau khi lọc** | Không lọc thì tài liệu giảng viên chiếm đầu bảng ở **cả năm** cấu hình. |

**Phát hiện quan trọng nhất về cách chấm: `doc_id` cho 10/10 với mọi cấu hình.**

Nếu chấm theo "tài liệu gold có nằm trong top-3 không", **cả năm cấu hình đều đạt 5/5 câu**, tức 10/10 điểm tuyệt đối, và bảng so sánh sẽ hoàn toàn phẳng — không phân biệt được chiến lược nào tốt hơn. Chấm ở mức nội dung thì điểm trải ra 5, 5, 6, 8, 8. Chênh lệch giữa hai cách chấm là **từ 2 đến 5 điểm tuỳ cấu hình**, và cách chấm ngây thơ xoá sạch mọi khác biệt mà cả buổi lab đang cố đo.

Nguyên nhân: các section trong cùng một tài liệu nói về cùng chủ đề nên điểm cosine gần bằng nhau, việc section nào lọt top-3 gần như ngẫu nhiên. Đúng tài liệu là điều kiện cần, không phải điều kiện đủ.

### A/B bắt buộc — câu 5, trên cả năm chiến lược

`python bench.py` và `python bench.py --no-filter`, `top_k=3`:

| Cấu hình | Sai đối tượng — KHÔNG lọc | Sai đối tượng — CÓ `audience=student` |
|---|---|---|
| `heading_320` | **3/3** | 0/3 |
| `recursive_280` | **2/3** | 0/3 |
| `metadata_enriched` | **2/3** | 0/3 |
| `paragraph_360` | **2/3** | 0/3 |
| `fixed_size(500,50)` | **1/3** | 0/3 |

Chi tiết nhánh không lọc:

- `heading_320`: `ueh-faculty-support` (+0,7686) — `ueh-faculty-support` (+0,7412) — `ueh-faculty-support` (+0,7105). **Cả ba vị trí đều là tài liệu giảng viên.**
- `recursive_280`: `ueh-faculty-support` (+0,7428) — `ueh-faculty-support` (+0,6840) — `ueh-learning-support-scholarship` (+0,6432)
- `metadata_enriched`: `ueh-faculty-support` (+0,7228) — `ueh-faculty-support` (+0,7158) — `ueh-learning-support-scholarship` (+0,7112)
- `paragraph_360`: `ueh-faculty-support` (+0,7428) — `ueh-learning-support-scholarship` (+0,7203) — `ueh-faculty-support` (+0,6958)
- `fixed_size(500,50)`: `ueh-faculty-support` (+0,7603) — `ueh-learning-support-scholarship` (+0,7057) — `uet-merit-scholarship-2025-2026` (+0,6604)

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**

Có, ở câu 5, và hiệu ứng **không phụ thuộc chiến lược chia nhỏ**: cả năm cấu hình đều đi từ có tài liệu sai đối tượng trong top-3 xuống còn 0/3. Ở **cả năm**, tài liệu giảng viên chiếm **hạng 1** khi không lọc — nghĩa là agent sẽ trả lời "500 triệu đồng cho Giáo sư" cho một sinh viên hỏi về học bổng.

Điểm đáng chú ý: điểm cosine của tài liệu giảng viên (0,72–0,77) **cao hơn** tài liệu đúng (0,64–0,72) ở mọi cấu hình. Filter không làm kết quả "giống chủ đề hơn" — nó loại bỏ **sai đối tượng**, thứ mà similarity một mình không phân biệt được, vì hai tài liệu thật sự nói về cùng chủ đề "hỗ trợ tài chính của UEH".

**Kết quả âm: đưa `audience` vào chính text KHÔNG thay thế được filter.**

Cấu hình `metadata_enriched` chèn tiền tố `[title | institution | audience]` vào đầu mỗi chunk trước khi embed, tức thông tin đối tượng đã nằm ngay trong chuỗi được mã hoá. Giả thuyết là retrieval sẽ tự phân biệt được và filter thành thừa. Đo ra vẫn **2/3 sai đối tượng** khi không lọc — không tốt hơn `recursive_280` trần, và tệ hơn `fixed_size`.

Lý do: tiền tố của tài liệu giảng viên là `[Hỗ trợ tài chính thu hút và phát triển giảng viên UEH | ueh | faculty]`, chứa cụm "hỗ trợ tài chính" **trùng từ vựng với câu hỏi**. Nó vừa thêm tín hiệu đúng (đây là tài liệu UEH) vừa thêm nhiễu (đây là tài liệu về hỗ trợ tài chính), và token `faculty` đơn lẻ quá yếu để cân lại.

Cùng tiền tố đó lại **rất hiệu quả cho việc định vị đoạn**: 6/10 lên 8/10 so với chunker trần cùng tham số. Kết luận: chèn metadata vào text và lọc metadata bằng filter giải **hai bài toán khác nhau** — tiền tố tìm đúng *đoạn*, filter loại đúng *đối tượng* — và không thay thế được nhau.

### Phụ lục 2A — Đối chiếu với năm báo cáo cá nhân

Cả năm báo cáo cá nhân đã nộp. **Ba backend nhúng khác nhau được dùng**, nên điểm trong báo cáo cá nhân không so sánh trực tiếp với nhau, và cũng không trùng bảng đo đồng nhất ở mục 2.

| Thành viên | Cấu hình | Backend trong báo cáo cá nhân | Điểm tự báo cáo | Đo lại đồng nhất (mục 2) |
|---|---|---|---|---|
| Đinh Đức Thái | `heading_320` | MockEmbedder | 3/5 document hit | 5/10 |
| Trần Hồng Sơn | `recursive_280` | MockEmbedder | 2/10 (45 chunk) | 6/10 |
| Hoàng Trung Hiếu | `metadata_enriched` | `paraphrase-multilingual-MiniLM-L12-v2` | 8/10 | 8/10 |
| Bùi Tùng Dương | `fixed_size(500,50)` | TF-IDF chuẩn hoá | 8/10 evidence-rank | 8/10 |
| Đàm Quang Sơn | `paragraph_360` | `TfidfEmbedder` | 6/10 | 5/10 |

**Đây là phát hiện về phương pháp, không chỉ là lỗi hành chính.** Cùng cấu hình `recursive_280` cho **2/10 với MockEmbedder** và **6/10 với embedder ngữ nghĩa** — chênh gấp ba, trong khi cách chia nhỏ không đổi một tham số nào. Nghĩa là thứ hạng giữa các chiến lược phụ thuộc vào backend nhúng nhiều hơn phụ thuộc vào chính chiến lược. Một bảng so sánh không ghi rõ backend thì gần như vô nghĩa — đó là lý do bảng ở mục 2 nêu điều kiện đo ngay trước khi nêu số.

Đàm Quang Sơn và Bùi Tùng Dương đều **ghi rõ** máy không có `sentence-transformers` nên phải dùng TF-IDF; đây là lựa chọn hợp lệ theo Phụ lục B của lab, miễn là nêu rõ trong báo cáo, điều cả hai đã làm.

**Điểm nhất quán qua mọi backend.** Có đúng một kết luận không đổi dù đo bằng Mock, TF-IDF hay embedder ngữ nghĩa: **lọc `audience` loại được tài liệu sai đối tượng**. Trần Hồng Sơn, Bùi Tùng Dương và Đàm Quang Sơn đều độc lập ghi nhận tài liệu giảng viên UEH chiếm hạng 1 ở câu 5 khi bỏ filter. Vì kết luận này sống sót qua ba cách mã hoá hoàn toàn khác nhau **và** năm cách chia nhỏ khác nhau, nó là phát hiện vững nhất của nhóm.

**Còn một điểm cần thống nhất trước khi nộp:** báo cáo cá nhân của Đinh Đức Thái dùng bộ 5 câu hỏi khác với bộ chính thức ở mục 3 (hỏi về mức Xuất sắc UET, gói học bổng VinUni, quy trình xếp hạng RMIT). Lab yêu cầu cả nhóm chạy chung một bộ câu hỏi, nên phần này cần chạy lại.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**

- Demo `python scripts/check_corpus.py`, rồi `python bench.py` và `python bench.py --no-filter`; mở câu 5 trong log để thấy tài liệu giảng viên chiếm hạng 1 khi bỏ lọc và biến mất khi thêm `audience=student`.
- Đối chiếu `recursive_280` với `metadata_enriched`: cùng chunker nền, cùng 45 chunk, chỉ khác một dòng tiền tố, điểm đi từ 6/10 lên 8/10.
- Chấm bằng `doc_id` cho **10/10 với cả năm cấu hình**; chấm ở mức nội dung mới trải ra 5–8/10. Cách chấm ngây thơ xoá sạch mọi khác biệt giữa các chiến lược.
- Câu 2 hỏng ở 3/5 cấu hình: hàng GPA `3,2` có trong corpus nhưng không lọt top-3, vì bảng Markdown bị mọi bộ chia cắt ngang.

**Bài học rút ra khi so sánh trong nhóm:**
Cùng 7 tài liệu, vị trí bằng chứng thay đổi vì các bộ chia giữ tiêu đề, câu và hàng bảng theo cách khác nhau. Chia nhỏ giúp tìm một điều kiện ngắn nhưng làm loãng mật độ bằng chứng trong mỗi chunk; chia to giữ được bằng chứng nhưng thô và chỉ hiệu quả với tài liệu ngắn. Vì vậy phải xem chính chunk và câu trả lời, không chỉ nhìn `doc_id` hay điểm cosine. Metadata `audience` giải quyết nhầm đối tượng ở câu 5 **trước** khi xếp hạng, ở tầng mà similarity không với tới được.

**Failure case chi tiết — Câu 2, bảng GPA VinUni**

- *Câu hỏi nào hỏng:* Câu 2 — "Sinh viên VinUni cần GPA tối thiểu bao nhiêu để duy trì học bổng 100%?". Đáp án đúng (`3,2`) nằm trong corpus nhưng **3/5 cấu hình** (`heading_320`, `recursive_280`, `paragraph_360`) không đưa được chunk chứa nó vào top-3; hai cấu hình còn lại chỉ đạt 1đ, tức mốc có trong top-3 nhưng không ở hạng 1.
- *Vì sao — hai nguyên nhân chồng lên nhau:*
  1. **Bảng Markdown bị mọi bộ chia cắt ngang.** Quan hệ giữa nhãn hàng `Học bổng toàn phần hoặc 100%` và giá trị `3,2` bị đứt — chunk giữ được con số thì mất nhãn, chunk giữ nhãn thì mất con số.
  2. **Bốn hàng của bảng có khuôn câu gần như trùng nhau** ("mức học bổng X yêu cầu GPA ít nhất Y" với Y = 3,2 / 2,5 / 2,0). Đo trên embedder ngữ nghĩa, hai câu chỉ khác con số đạt similarity **0,7338** — cao hơn hẳn hai câu diễn đạt cùng một ý (**0,5955**). Embedding mã hoá chủ đề và khuôn câu, không mã hoá giá trị số, nên retrieval không phân biệt được hàng nào ứng với mức học bổng nào.
- *Đề xuất sửa:* bộ chia riêng cho bảng Markdown — mỗi hàng thành một chunk độc lập, lặp lại dòng tiêu đề cột và tên bảng vào đầu mỗi chunk, để chunk tự mang đủ ngữ cảnh `100% → 3,2`. Đây là cùng một cơ chế đã giúp `metadata_enriched` thắng ở câu 3 (bơm ngữ cảnh vào chunk), chỉ áp dụng xuống mức hàng bảng. **Đổi embedder sẽ không cứu được câu này** — nguyên nhân nằm ở tầng chia nhỏ, không phải tầng mã hoá.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
Ba việc, theo thứ tự ưu tiên. (1) Viết bộ chia nhận diện bảng Markdown như trên — đây là nguyên nhân của failure case duy nhất còn lại. (2) Thống nhất **một** backend nhúng cho cả nhóm ngay từ đầu, và ghi tên backend cạnh mọi con số; việc năm người dùng ba backend làm mất gần hết giá trị so sánh của lần chạy đầu. (3) Khai báo mốc kiểm nội dung cho mỗi câu hỏi **trước** khi chạy, thay vì chấm bằng `doc_id` — nếu không, mọi cấu hình đều 10/10 và bảng so sánh không nói lên điều gì. Ngoài ra cần đối chiếu lại các bản tóm lược với trang nguồn trước khi dùng cho tư vấn học bổng thực tế.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá | Căn cứ |
|----------|-------------------|--------|
| Lựa chọn tài liệu (Document Set Quality) | 9 / 10 | 7 tài liệu từ 4 nguồn chính thức, metadata đủ và kiểm tự động được bằng `scripts/check_corpus.py`; tài liệu `faculty` được giữ có chủ ý để filter có việc thật. Trừ 1 vì corpus lệch 6 student / 1 faculty, chỉ có đúng một tài liệu để filter loại ra. |
| Thiết kế chiến lược (Strategy Design) | 14 / 15 | Năm chiến lược khác nhau, đo lại đồng nhất trên một backend; một so sánh có kiểm soát (tiền tố metadata: 6/10 → 8/10 với cùng chunker nền); một kết quả âm được nêu giả thuyết rồi bác bỏ bằng số liệu. Trừ 1 vì hai chunker phải dựng lại thay vì dùng mã gốc. |
| Chất lượng truy xuất (Retrieval Quality) | 8 / 10 | Cấu hình tốt nhất đạt 8/10 khi chấm ở mức nội dung. A/B chạy đủ trên cả năm chiến lược. Câu 2 vẫn hỏng ở 3/5 cấu hình. |
| Thuyết trình (Demo) | — / 5 | Cập nhật sau buổi demo. |
| **Tổng phần nhóm, trước thuyết trình** | **31 / 35** | |

Điểm chất lượng truy xuất lấy cấu hình tốt nhất, không cộng điểm của nhiều cấu hình. Mọi số liệu trong báo cáo này tái chạy được bằng `python bench.py` trên `data/hoc-bong/` với `EMBEDDING_PROVIDER=local`.

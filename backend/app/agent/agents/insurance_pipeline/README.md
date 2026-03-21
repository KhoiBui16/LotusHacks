# Insurance Claim Verification Pipeline

Pipeline dùng để hỗ trợ xác thực hồ sơ bồi thường bảo hiểm xe cơ giới từ nhiều nguồn dữ liệu khác nhau, bao gồm:

1. **Document claim/policy**  
   Trích xuất thông tin từ file văn bản như đơn yêu cầu bồi thường, mô tả sự cố, thông tin hợp đồng bảo hiểm.

2. **Accident Image API**  
   Phân tích ảnh hiện trường hoặc ảnh hư hỏng xe để nhận diện các vùng tổn thất.

3. **Driver License Image API**  
   Đọc và chuẩn hóa thông tin từ ảnh giấy phép lái xe.

4. **Verification & Scoring**  
   So khớp thông tin giữa văn bản, ảnh tai nạn và GPLX để đưa ra kết quả xác thực và điểm tin cậy.

---

## 1. Mục tiêu hệ thống

Hệ thống được thiết kế để:

- tự động đọc và chuẩn hóa dữ liệu đầu vào từ nhiều nguồn
- giảm thao tác kiểm tra thủ công trong quy trình xử lý claim
- hỗ trợ phát hiện sai lệch giữa hồ sơ khai báo và bằng chứng thực tế
- trả về **verification result** và **matching score** để phục vụ bước đánh giá tiếp theo

---

## 2. Quy trình xử lý

### Bước 1 — Extract document
Hệ thống đọc file claim hoặc policy và trích xuất các trường thông tin quan trọng như:

- số hợp đồng
- tên người được bảo hiểm / người yêu cầu bồi thường
- biển số xe
- thời gian hiệu lực bảo hiểm
- thời gian và địa điểm tai nạn
- mô tả tổn thất khai báo
- loại sự cố

### Bước 2 — Analyze accident image
API phân tích ảnh hiện trường hoặc ảnh hư hỏng xe để xác định:

- có xe hay không
- loại phương tiện
- vùng hư hỏng quan sát được
- mức độ khớp với tổn thất được khai báo

### Bước 3 — Analyze driver license image
API đọc ảnh giấy phép lái xe và chuẩn hóa các thông tin như:

- họ tên
- số giấy phép lái xe
- hạng bằng
- ngày sinh
- ngày cấp / ngày hết hạn
- cơ quan cấp

### Bước 4 — Compare and score
Rules Engine thực hiện đối chiếu giữa các nguồn dữ liệu:

- thông tin văn bản claim
- kết quả phân tích ảnh tai nạn
- kết quả trích xuất từ giấy phép lái xe

Sau đó hệ thống trả về:

- danh sách rule checks
- trạng thái pass / fail / warning
- lý do giải thích
- **verification score** hoặc **confidence score**

---

## 3. Cấu trúc file

- `file_reader.py`  
  Đọc file đầu vào và chuẩn hóa text.

- `text_extractor.py`  
  Trích xuất thông tin từ document claim/policy.

- `image_analyzer.py`  
  Gọi model hoặc API để phân tích ảnh tai nạn.

- `extract_driver.py`  
  Phân tích ảnh giấy phép lái xe và trả về dữ liệu có cấu trúc.

- `rules_engine.py`  
  So khớp dữ liệu từ nhiều nguồn và tính score xác thực.

- `schemas.py`  
  Định nghĩa schema đầu vào / đầu ra cho toàn pipeline.

- `claim_pipeline.py`  
  Gom toàn bộ flow xử lý end-to-end.

- `app.py`  
  FastAPI app để expose các API endpoint.

- `test_claim_verify.py`  
  File test nhanh toàn pipeline với dữ liệu mẫu.

---

## 4. Cài đặt

```bash
pip install -r requirements.txt
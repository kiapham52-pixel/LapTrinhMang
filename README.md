# DAU Online Exam — Lập trình mạng

Đồ án xây dựng hệ thống thi trắc nghiệm desktop theo mô hình **Client–Server** bằng Python. Client dùng Tkinter; client và server giao tiếp qua TCP Socket với thông điệp JSON; SQLite lưu dữ liệu.

## Chức năng chính

- **Mạng / Server:** nhận kết nối TCP, xử lý request–response JSON và phục vụ nhiều client đồng thời.
- **Quản trị:** quản lý sinh viên, môn học, câu hỏi, kỳ thi và phòng thi.
- **Làm bài:** sinh viên chọn kỳ thi, trả lời câu hỏi, theo dõi thời gian, đánh dấu câu phân vân và dùng trợ giúp loại phương án.
- **Kết quả:** chấm điểm, lưu lịch sử thi và cung cấp kết quả, thống kê cho sinh viên/quản trị viên.

## Chạy nhanh

Cần Python 3 có Tkinter. Tại thư mục gốc repository, mở terminal thứ nhất:

```powershell
cd DAU_Online_Exam
python run_server.py
```

Mở terminal thứ hai tại `DAU_Online_Exam`:

```powershell
python -m client.main
```

Database SQLite được khởi tạo và nạp dữ liệu mẫu khi server chạy lần đầu. Có thể chạy nhiều client cùng kết nối đến server.

### Tài khoản mẫu

| Vai trò | Tên đăng nhập | Mật khẩu |
|---|---|---|
| Quản trị viên | `admin` | `admin123` |
| Sinh viên | `SV001` | `123456` |

Tài khoản chỉ phục vụ demo, không sử dụng trong môi trường thật.

## Kiểm thử

```powershell
python -m unittest discover -s DAU_Online_Exam/tests -v
```

## Tài liệu dự án

README đầy đủ về phạm vi theo đề bài, kiến trúc, luồng hoạt động, hướng dẫn LAN, kiểm thử và cấu trúc mã nguồn: [DAU_Online_Exam/README.md](DAU_Online_Exam/README.md).

## Lưu ý bảo mật

Giao tiếp hiện dùng TCP không mã hóa và tài khoản mẫu có mật khẩu cố định. Chỉ dùng trong môi trường học tập đáng tin cậy; không công khai server ra Internet hoặc dùng cho dữ liệu thật.

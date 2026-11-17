# DAU Online Exam

Hệ thống thi trắc nghiệm trực tuyến theo mô hình **Client–Server**, xây dựng bằng Python. Client cung cấp giao diện desktop Tkinter; server nhận và xử lý yêu cầu qua TCP Socket, trao đổi dữ liệu JSON và lưu dữ liệu bằng SQLite.

## Mục lục

- [Mục tiêu và phạm vi](#mục-tiêu-và-phạm-vi)
- [Chức năng](#chức-năng)
- [Kiến trúc và luồng hoạt động](#kiến-trúc-và-luồng-hoạt-động)
- [Công nghệ sử dụng](#công-nghệ-sử-dụng)
- [Yêu cầu](#yêu-cầu)
- [Cài đặt và chạy](#cài-đặt-và-chạy)
- [Tài khoản dùng thử](#tài-khoản-dùng-thử)
- [Kết nối qua mạng LAN](#kết-nối-qua-mạng-lan)
- [Kiểm thử](#kiểm-thử)
- [Cấu trúc thư mục](#cấu-trúc-thư-mục)
- [Lưu ý](#lưu-ý)

## Mục tiêu và phạm vi

Dự án minh họa các nội dung lập trình mạng trong một ứng dụng thi trực tuyến:

1. **Server / Mạng:** khởi động server, lắng nghe và chấp nhận kết nối TCP, nhận request, xử lý và gửi response; mỗi client được phục vụ đồng thời bằng một thread.
2. **Admin / Quản lý dữ liệu:** quản lý tài khoản sinh viên, môn học, câu hỏi; tìm kiếm và lọc câu hỏi.
3. **Kỳ thi / Phòng thi:** tạo và quản lý kỳ thi, tạo phòng, mở hoặc đóng phòng, theo dõi sinh viên tham gia và trạng thái kết nối.
4. **Sinh viên / Làm bài:** xem kỳ thi, làm bài trắc nghiệm, theo dõi thời gian, đánh dấu câu cần xem lại và sử dụng trợ giúp loại phương án.
5. **Kết quả / Thống kê:** nhận bài nộp, chấm điểm, lưu kết quả; hỗ trợ xem lịch sử, kết quả và thống kê.

## Chức năng

### Quản trị viên

- Đăng nhập vào giao diện quản trị.
- Xem, thêm, sửa và xóa tài khoản sinh viên.
- Quản lý môn học và câu hỏi; tìm kiếm câu hỏi và lọc theo môn.
- Tạo, sửa, xóa kỳ thi và quản lý câu hỏi của kỳ thi.
- Tạo, cập nhật, mở, bắt đầu, kết thúc hoặc đóng phòng thi.
- Xem danh sách sinh viên trong phòng và trạng thái online/offline.
- Xem kết quả của sinh viên, kết quả theo kỳ thi và số liệu thống kê.

### Sinh viên

- Đăng nhập và xem danh sách kỳ thi.
- Bắt đầu làm bài, chọn đáp án, chuyển giữa các câu và theo dõi thời gian.
- Đánh dấu câu hỏi phân vân để nhận biết câu cần kiểm tra lại.
- Dùng trợ giúp **Giảm áp lực kỳ thi**: hệ thống chỉ hiển thị đáp án đúng và một phương án sai; chức năng có giới hạn lượt sử dụng.
- Nộp bài và xem điểm, kết quả hoặc lịch sử thi.

## Kiến trúc và luồng hoạt động

```text
Giao diện Tkinter (Client)
        │
        │ TCP Socket: JSON UTF-8 có tiền tố độ dài 4 byte
        ▼
Server đa luồng ─── Các service nghiệp vụ
        │
        ▼
SQLite (database/exam_system.db)
```

Client gửi request có trường `action` và dữ liệu cần xử lý. Server đọc request, chuyển đến service tương ứng, rồi trả response JSON. Gói tin được đóng khung bằng độ dài thông điệp 4 byte theo byte order big-endian, tiếp theo là nội dung JSON UTF-8. Server mặc định lắng nghe trên cổng `5000`.

Luồng thi tổng quát:

```text
Đăng nhập → Chọn kỳ thi → Bắt đầu làm bài → Trả lời / đánh dấu / dùng trợ giúp
          → Nộp bài → Server chấm điểm và lưu kết quả → Xem kết quả
```

Luồng phòng thi:

```text
Tạo kỳ thi → Tạo phòng → Mở phòng → Sinh viên tham gia
           → Theo dõi trạng thái → Kết thúc hoặc đóng phòng
```

## Công nghệ sử dụng

- **Python** cho client, server và xử lý nghiệp vụ.
- **Tkinter** cho giao diện desktop.
- **TCP Socket** và **JSON** cho giao tiếp client–server.
- **SQLite** để lưu tài khoản, môn học, câu hỏi, kỳ thi, phòng thi và kết quả.
- **unittest** cho kiểm thử.

## Yêu cầu

- Python 3 có cài Tkinter.
- Hệ điều hành desktop có giao diện đồ họa để chạy client.
- Mạng TCP giữa client và server nếu chạy trên nhiều máy.

Dự án hiện không yêu cầu cài thêm thư viện bên thứ ba; `requirements.txt` được giữ để thuận tiện bổ sung phụ thuộc sau này.

## Cài đặt và chạy

Mở terminal tại thư mục `DAU_Online_Exam`.

### Windows (PowerShell)

```powershell
cd DAU_Online_Exam
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Linux / macOS

```bash
cd DAU_Online_Exam
python3 -m venv .venv
source .venv/bin/activate
```

Không cần cài gói bổ sung cho phiên bản hiện tại. Mở **terminal thứ nhất** và chạy server:

```bash
python run_server.py
```

Mở **terminal thứ hai**, cũng tại thư mục `DAU_Online_Exam`, rồi chạy client:

```bash
python -m client.main
```

Server khởi tạo cấu trúc SQLite và dữ liệu mẫu ở lần chạy đầu tiên. Cơ sở dữ liệu mặc định nằm tại `database/exam_system.db`. Có thể mở nhiều client để thử kết nối đồng thời.

## Tài khoản dùng thử

| Vai trò | Tên đăng nhập | Mật khẩu |
|---|---|---|
| Quản trị viên | `admin` | `admin123` |
| Sinh viên | `SV001` | `123456` |
| Sinh viên | `SV002` | `123456` |
| Sinh viên | `SV003` | `123456` |

Đây là thông tin mẫu do server tạo khi cơ sở dữ liệu chưa có tài khoản. Chỉ dùng để chạy thử; không sử dụng các thông tin này trong môi trường thật.

## Kết nối qua mạng LAN

1. Chạy server trên máy chủ. Server mặc định bind `0.0.0.0:5000`.
2. Trên máy chủ Windows, dùng `ipconfig` để tìm địa chỉ IPv4 nội bộ, ví dụ `192.168.1.10`.
3. Cho phép kết nối TCP đến cổng `5000` qua firewall của máy chủ nếu cần.
4. Mở client trên máy khác, nhập địa chỉ IP của máy chủ vào ô **Server IP** trên màn hình đăng nhập.
5. Đảm bảo hai máy có thể kết nối trong cùng mạng và server vẫn đang chạy.

## Kiểm thử

Từ thư mục gốc repository:

```bash
python -m unittest discover -s DAU_Online_Exam/tests -v
```

Các kiểm thử hiện có bao gồm luồng câu hỏi–kỳ thi–phòng thi–nộp bài, chấm điểm, thống kê, môn học và một số hành vi giao diện quản trị.

## Cấu trúc thư mục

```text
DAU_Online_Exam/
├── client/
│   ├── main.py                 # Điểm khởi chạy giao diện client
│   ├── network/                # Kết nối TCP từ client
│   └── screens/                # Giao diện sinh viên và quản trị
├── database/
│   └── database.py             # Khởi tạo schema và dữ liệu mẫu
├── server/
│   ├── server.py               # TCP server đa luồng
│   ├── client_handler.py       # Nhận request và điều phối action
│   ├── server_config.py        # Cấu hình host, port, database
│   └── services/               # Xác thực, kỳ thi, câu hỏi, kết quả, phòng, môn học
├── shared/
│   └── protocol.py             # Gửi/nhận JSON qua socket
├── tests/                      # Kiểm thử unittest
├── requirements.txt
└── run_server.py
```

## Lưu ý

- Server dùng TCP không mã hóa và tài khoản mẫu có mật khẩu cố định. Chỉ chạy trong môi trường học tập đáng tin cậy; không công khai server trực tiếp ra Internet hoặc dùng cho dữ liệu thật.
- Tắt server bằng `Ctrl+C`.
- Nếu client không kết nối được, kiểm tra server đã chạy chưa, địa chỉ IP, cổng `5000` và cấu hình firewall.

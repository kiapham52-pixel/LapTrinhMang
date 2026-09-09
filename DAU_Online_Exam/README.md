# DAU Online Exam System

Hệ thống thi trắc nghiệm trực tuyến Client-Server bằng Python, TCP Socket, SQLite, JSON và Tkinter.

## Cài đặt

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Khởi tạo database

Database được tạo tự động khi chạy server đầu tiên.

```bash
python run_server.py
```

## Chạy Server

```bash
python run_server.py
```

## Chạy Client

```bash
python client/main.py
```

## Tài khoản mẫu

- Admin: username `admin`, password `admin123`
- Student: username `sv001`, password `sv001`

## Demo

Mở nhiều client tại cùng lúc bằng lệnh:

```bash
python client/main.py
```

## Kết nối qua LAN

Trên máy chủ, lấy IP nội bộ bằng `ipconfig`, ví dụ `192.168.1.10`. Trên client, nhập IP đó và port `5000`.

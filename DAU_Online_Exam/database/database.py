import sqlite3
import os
import hashlib
import json
import random
from datetime import datetime


class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.connect()
        try:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_code TEXT UNIQUE,
                    full_name TEXT NOT NULL,
                    email TEXT,
                    class_name TEXT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('admin','student')),
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    option_a TEXT NOT NULL,
                    option_b TEXT NOT NULL,
                    option_c TEXT NOT NULL,
                    option_d TEXT NOT NULL,
                    correct_answer TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS exams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    duration INTEGER NOT NULL,
                    total_questions INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS exam_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exam_id INTEGER NOT NULL,
                    question_id INTEGER NOT NULL,
                    FOREIGN KEY(exam_id) REFERENCES exams(id) ON DELETE CASCADE,
                    FOREIGN KEY(question_id) REFERENCES questions(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    exam_id INTEGER NOT NULL,
                    score REAL NOT NULL DEFAULT 0,
                    correct_answers INTEGER NOT NULL DEFAULT 0,
                    wrong_answers INTEGER NOT NULL DEFAULT 0,
                    duration INTEGER NOT NULL DEFAULT 0,
                    started_at TEXT NOT NULL,
                    submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY(exam_id) REFERENCES exams(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS answers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    attempt_id INTEGER NOT NULL,
                    question_id INTEGER NOT NULL,
                    selected_answer TEXT,
                    correct_answer TEXT NOT NULL,
                    is_correct INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY(attempt_id) REFERENCES attempts(id) ON DELETE CASCADE,
                    FOREIGN KEY(question_id) REFERENCES questions(id) ON DELETE CASCADE
                );
            ''')
            conn.commit()
        finally:
            conn.close()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def seed_data(self):
        conn = self.connect()
        try:
            # Normalize sample students for username case and password alignment.
            conn.execute("UPDATE users SET username = UPPER(username), password_hash = ? WHERE LOWER(username) = 'sv001'", (self.hash_password('123456'),))
            conn.execute("UPDATE users SET username = UPPER(username), password_hash = ? WHERE LOWER(username) = 'sv002'", (self.hash_password('123456'),))
            conn.execute("UPDATE users SET username = UPPER(username), password_hash = ? WHERE LOWER(username) = 'sv003'", (self.hash_password('123456'),))

            user_count = conn.execute('SELECT COUNT(*) AS count FROM users').fetchone()['count']
            if user_count == 0:
                admin_hash = self.hash_password('admin123')
                conn.execute("INSERT INTO users (student_code, full_name, email, class_name, username, password_hash, role, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                             ('ADMIN', 'Administrator', 'admin@dau.edu.vn', 'System', 'admin', admin_hash, 'admin', 'active', datetime.now().isoformat()))

                student_data = [
                    ('SV001', 'Nguyễn Văn An', 'an@dau.edu.vn', 'CNTT-K17', 'SV001', self.hash_password('123456'), 'student', 'active', datetime.now().isoformat()),
                    ('SV002', 'Trần Văn Bình', 'binh@dau.edu.vn', 'CNTT-K17', 'SV002', self.hash_password('123456'), 'student', 'active', datetime.now().isoformat()),
                    ('SV003', 'Lê Minh Huy', 'huy@dau.edu.vn', 'CNTT-K17', 'SV003', self.hash_password('123456'), 'student', 'active', datetime.now().isoformat()),
                ]
                conn.executemany("INSERT INTO users (student_code, full_name, email, class_name, username, password_hash, role, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", student_data)

            question_count = conn.execute('SELECT COUNT(*) AS count FROM questions').fetchone()['count']
            if question_count == 0:
                sample_questions = [
                    ('TCP là gì?', 'Giao thức điều khiển truyền nhận dữ liệu', 'Giao thức định tuyến', 'Giao thức truyền tải', 'Giao thức nén', 'A', 'Lập trình mạng', 'Dễ'),
                    ('UDP khác TCP ở điểm nào?', 'Đảm bảo tin cậy tốt hơn TCP', 'Không cần handshake và nhanh hơn', 'Dùng cho mặt phẳng ứng dụng', 'Chỉ hoạt động trên IPv6', 'B', 'Lập trình mạng', 'Dễ'),
                    ('Socket trong TCP dùng để?', 'Kết nối ổ cắm giữa client và server', 'Lưu file hệ thống', 'Quản lý bộ nhớ', 'Phân đoạn dữ liệu', 'A', 'Socket', 'Dễ'),
                    ('Client-Server mô hình có?', 'Server phục vụ, Client yêu cầu', 'Server không gửi dữ liệu', 'Client chỉ lưu dữ liệu', 'Không dùng socket', 'A', 'Client-Server', 'Dễ'),
                    ('Port số trong TCP?', 'Định danh tiến trình trên máy chủ', 'Địa chỉ nhà', 'Tên miền', 'Bộ nhớ cache', 'A', 'Lập trình mạng', 'Dễ'),
                    ('HTTP là gì?', 'Giao thức truyền web', 'Bộ nhớ tạm', 'Chuẩn IP', 'Ngôn ngữ lệnh', 'A', 'HTTP', 'Dễ'),
                    ('DNS dùng để?', 'Phân giải tên miền sang IP', 'Truyền dữ liệu bằng UDP', 'Nén dữ liệu', 'Sắp xếp câu hỏi', 'A', 'DNS', 'Dễ'),
                    ('OSI có bao nhiêu lớp?', '5', '6', '7', '8', 'C', 'OSI', 'Dễ'),
                    ('Multi-thread trên server giúp?', 'Xử lý nhiều client đồng thời', 'Chỉ nén hình ảnh', 'Giảm băng thông', 'Không có tác dụng', 'A', 'Multi-thread', 'Trung bình'),
                    ('IP address có chức năng?', 'Nhận diện máy tính trên mạng', 'Quản lý thời gian', 'Chỉ định file', 'Tạo socket', 'A', 'IP', 'Dễ'),
                    ('TCP handshake gồm?', 'SYN, SYN-ACK, ACK', 'ACK, DNS, HTTP', 'HTTP, UDP, TCP', 'ACK, FIN, HASH', 'A', 'TCP/UDP', 'Trung bình'),
                    ('Port 80 thường dùng cho?', 'HTTP', 'FTP', 'DNS', 'SSH', 'A', 'HTTP', 'Dễ'),
                    ('UDP không đảm bảo?', 'Độ tin cậy truyền dữ liệu hoàn toàn', 'Độ trễ thấp', 'Truyền nhanh', 'Truyền không cần kết nối', 'A', 'TCP/UDP', 'Trung bình'),
                    ('Câu hỏi Server trong socket thường?', 'Lắng nghe và chấp nhận kết nối', 'Mở cửa sổ UI', 'Phát video', 'Biên dịch Python', 'A', 'Socket', 'Dễ'),
                    ('TCP phân mảnh dữ liệu lúc?', 'Ở tầng transport', 'Ở tầng giao diện', 'Ở tầng ứng dụng', 'Ở tầng vật lý', 'A', 'TCP/UDP', 'Trung bình'),
                    ('JSON dùng để?', 'Đóng gói dữ liệu dạng text', 'Lưu hình ảnh', 'Tạo giao diện', 'Nén dữ liệu', 'A', 'JSON', 'Dễ'),
                    ('HTTP GET dùng để?', 'Yêu cầu dữ liệu', 'Gửi form', 'Tạo database', 'Đăng xuất server', 'A', 'HTTP', 'Dễ'),
                    ('Thread trong Python dùng cơ chế?', 'Đa luồng xử lý đồng thời', 'Lập trình song song không cần CPU', 'Không có gì', 'Tạo trình duyệt', 'A', 'Multi-thread', 'Trung bình'),
                    ('Server phải xử lý đóng kết nối?', 'Không để crash', 'Không cần gửi phản hồi', 'Không cần socket', 'Không cần kiểm tra dữ liệu', 'A', 'Exception Handling', 'Trung bình'),
                    ('Sự cố mất mạng trên client nên?', 'Thông báo rõ và đóng kết nối an toàn', 'Tắt server', 'Reset database', 'Mở thêm socket', 'A', 'Exception Handling', 'Dễ'),
                ]

                conn.executemany("INSERT INTO questions (content, option_a, option_b, option_c, option_d, correct_answer, subject, difficulty, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", [(q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7], datetime.now().isoformat()) for q in sample_questions])

            exam_count = conn.execute('SELECT COUNT(*) AS count FROM exams').fetchone()['count']
            if exam_count == 0:
                conn.execute("INSERT INTO exams (title, description, duration, total_questions, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                             ('Lập trình mạng cơ bản', 'Đề thi mẫu về TCP, Socket, HTTP và DNS.', 30, 20, 'active', datetime.now().isoformat()))
                exam_id = conn.execute("SELECT id FROM exams WHERE title = ?", ('Lập trình mạng cơ bản',)).fetchone()[0]
                questions = conn.execute("SELECT id FROM questions ORDER BY id LIMIT 20").fetchall()
                for row in questions:
                    conn.execute("INSERT INTO exam_questions (exam_id, question_id) VALUES (?, ?)", (exam_id, row['id']))

                conn.execute("INSERT INTO exams (title, description, duration, total_questions, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                             ('Mạng máy tính nâng cao', 'Đề thi mẫu về OSI, IP, TCP/UDP, Multi-thread.', 40, 20, 'active', datetime.now().isoformat()))
                exam2_id = conn.execute("SELECT id FROM exams WHERE title = ?", ('Mạng máy tính nâng cao',)).fetchone()[0]
                questions2 = conn.execute("SELECT id FROM questions ORDER BY id LIMIT 20").fetchall()
                for row in questions2:
                    conn.execute("INSERT INTO exam_questions (exam_id, question_id) VALUES (?, ?)", (exam2_id, row['id']))

            conn.commit()
        finally:
            conn.close()

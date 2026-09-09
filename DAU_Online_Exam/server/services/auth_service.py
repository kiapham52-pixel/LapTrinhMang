import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.database import DatabaseManager


class AuthService:
    def __init__(self, db_path):
        self.db = DatabaseManager(db_path)

    def login(self, username, password):
        try:
            conn = self.db.connect()
            password_hash = self.db.hash_password(password)
            input_username = (username or '').strip().lower()
            user = conn.execute("SELECT * FROM users WHERE LOWER(username) = ?", (input_username,)).fetchone()
            if user is None:
                return {'status': 'error', 'success': False, 'message': 'Sai tài khoản hoặc mật khẩu'}
            if user['password_hash'] != password_hash:
                return {'status': 'error', 'success': False, 'message': 'Sai tài khoản hoặc mật khẩu'}
            if user['status'] != 'active':
                return {'status': 'error', 'success': False, 'message': 'Tài khoản đã bị khóa'}
            return {
                'status': 'success',
                'success': True,
                'message': 'Đăng nhập thành công',
                'user': {
                    'id': user['id'],
                    'student_code': user['student_code'],
                    'full_name': user['full_name'],
                    'email': user['email'],
                    'class_name': user['class_name'],
                    'username': user['username'],
                    'role': user['role'],
                    'status': user['status'],
                }
            }
        except Exception as exc:
            return {'status': 'error', 'success': False, 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def get_profile(self, user_id):
        try:
            conn = self.db.connect()
            user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            if not user:
                return {'status': 'error', 'message': 'Không tìm thấy người dùng'}
            return {'status': 'success', 'user': dict(user)}
        except Exception as exc:
            return {'status': 'error', 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def get_students(self, payload=None):
        try:
            conn = self.db.connect()
            if payload and payload.get('role') != 'admin':
                return {'status': 'error', 'success': False, 'message': 'Không có quyền'}
            rows = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
            return {'status': 'success', 'success': True, 'students': [dict(r) for r in rows]}
        except Exception as exc:
            return {'status': 'error', 'success': False, 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def search_students(self, payload):
        try:
            conn = self.db.connect()
            if payload.get('role') != 'admin':
                return {'status': 'error', 'success': False, 'message': 'Không có quyền'}
            keyword = (payload.get('keyword') or '').strip()
            if not keyword:
                return self.get_students(payload)
            query = """
                SELECT * FROM users
                WHERE LOWER(student_code) LIKE ?
                   OR LOWER(full_name) LIKE ?
                   OR LOWER(username) LIKE ?
                   OR LOWER(class_name) LIKE ?
                ORDER BY id
            """
            pattern = f'%{keyword.lower()}%'
            rows = conn.execute(query, (pattern, pattern, pattern, pattern)).fetchall()
            return {'status': 'success', 'success': True, 'students': [dict(r) for r in rows]}
        except Exception as exc:
            return {'status': 'error', 'success': False, 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def create_student(self, payload):
        try:
            conn = self.db.connect()
            if payload.get('role') != 'admin':
                return {'status': 'error', 'success': False, 'message': 'Không có quyền'}
            student = payload.get('student', {})
            student_code = (student.get('student_code') or '').strip()
            username = (student.get('username') or '').strip()
            if not student_code or not username:
                return {'status': 'error', 'success': False, 'message': 'Thiếu mã sinh viên hoặc username'}
            existing_code = conn.execute("SELECT id FROM users WHERE LOWER(student_code) = ?", (student_code.lower(),)).fetchone()
            if existing_code:
                return {'status': 'error', 'success': False, 'message': 'Mã sinh viên đã tồn tại'}
            existing_user = conn.execute("SELECT id FROM users WHERE LOWER(username) = ?", (username.lower(),)).fetchone()
            if existing_user:
                return {'status': 'error', 'success': False, 'message': 'Username đã tồn tại'}
            password_hash = self.db.hash_password(student.get('password') or '123456')
            role = 'student'
            status = (student.get('status') or 'active').strip()
            if status not in ('active', 'inactive'):
                status = 'active'
            conn.execute("INSERT INTO users (student_code, full_name, email, class_name, username, password_hash, role, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                         (student_code, student.get('full_name'), student.get('email'), student.get('class_name'), username, password_hash, role, status))
            conn.commit()
            return {'status': 'success', 'success': True, 'message': 'Sinh viên được thêm'}
        except Exception as exc:
            return {'status': 'error', 'success': False, 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def update_student(self, payload):
        try:
            conn = self.db.connect()
            if payload.get('role') != 'admin':
                return {'status': 'error', 'success': False, 'message': 'Không có quyền'}
            student_id = payload.get('student_id')
            if not student_id:
                return {'status': 'error', 'success': False, 'message': 'Thiếu id sinh viên'}
            student = payload.get('student', {})
            username = (student.get('username') or '').strip()
            current = conn.execute("SELECT * FROM users WHERE id = ?", (student_id,)).fetchone()
            if not current:
                return {'status': 'error', 'success': False, 'message': 'Sinh viên không tồn tại'}
            if username and username.lower() != current['username'].lower():
                existing = conn.execute("SELECT id FROM users WHERE LOWER(username) = ? AND id != ?", (username.lower(), student_id)).fetchone()
                if existing:
                    return {'status': 'error', 'success': False, 'message': 'Username đã tồn tại'}
            student_code = (student.get('student_code') or current['student_code']).strip()
            if student_code.lower() != current['student_code'].lower():
                existing_code = conn.execute("SELECT id FROM users WHERE LOWER(student_code) = ? AND id != ?", (student_code.lower(), student_id)).fetchone()
                if existing_code:
                    return {'status': 'error', 'success': False, 'message': 'Mã sinh viên đã tồn tại'}
            fields = {
                'student_code': student_code,
                'full_name': student.get('full_name'),
                'email': student.get('email'),
                'class_name': student.get('class_name'),
                'username': username,
                'status': (student.get('status') or current['status']).strip(),
            }
            if student.get('password'):
                fields['password_hash'] = self.db.hash_password(student.get('password'))
            sets = []
            values = []
            for key, value in fields.items():
                if value is not None:
                    sets.append(f'{key} = ?')
                    values.append(value)
            values.append(student_id)
            sql = f"UPDATE users SET {', '.join(sets)} WHERE id = ?"
            conn.execute(sql, values)
            conn.commit()
            return {'status': 'success', 'success': True, 'message': 'Sinh viên được cập nhật'}
        except Exception as exc:
            return {'status': 'error', 'success': False, 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def delete_student(self, payload):
        try:
            conn = self.db.connect()
            if payload.get('role') != 'admin':
                return {'status': 'error', 'success': False, 'message': 'Không có quyền'}
            student_id = payload.get('student_id') or None
            student_code = payload.get('student_code')
            current_user_id = payload.get('user_id')
            if not student_id and student_code:
                row = conn.execute("SELECT id FROM users WHERE student_code = ?", (student_code,)).fetchone()
                if row:
                    student_id = row['id']
            if not student_id:
                return {'status': 'error', 'success': False, 'message': 'Thiếu sinh viên cần xóa'}
            if int(student_id) == int(current_user_id):
                return {'status': 'error', 'success': False, 'message': 'Không thể xóa tài khoản Admin đang đăng nhập'}
            # Soft delete is safer for history: mark inactive instead of hard delete.
            row = conn.execute("SELECT role, status FROM users WHERE id = ?", (student_id,)).fetchone()
            if row and row['role'] == 'student':
                conn.execute("UPDATE users SET status = 'inactive' WHERE id = ?", (student_id,))
                conn.commit()
                return {'status': 'success', 'success': True, 'message': 'Sinh viên chuyển trạng thái inactive'}
            conn.execute("DELETE FROM users WHERE id = ?", (student_id,))
            conn.commit()
            return {'status': 'success', 'success': True, 'message': 'Sinh viên được xóa'}
        except Exception as exc:
            return {'status': 'error', 'success': False, 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

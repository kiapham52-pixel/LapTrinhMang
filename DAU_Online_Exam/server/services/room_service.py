import os
import sys
import logging
import sqlite3
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.database import DatabaseManager


logger = logging.getLogger(__name__)


class RoomService:
    def __init__(self, db_path):
        self.db = DatabaseManager(db_path)

    def get_rooms(self, payload=None):
        try:
            conn = self.db.connect()
            rows = conn.execute("""
                SELECT r.*, e.title AS exam_title, e.duration AS exam_duration,
                       COUNT(DISTINCT rs.user_id) AS students_count,
                       COUNT(DISTINCT CASE WHEN s.status = 'ONLINE' THEN rs.user_id END) AS online_count,
                       COUNT(DISTINCT CASE WHEN rs.submitted_at IS NOT NULL THEN rs.user_id END) AS submitted_count
                FROM exam_rooms r
                LEFT JOIN exams e ON e.id = r.exam_id
                LEFT JOIN room_students rs ON rs.room_id = r.id
                LEFT JOIN sessions s ON s.user_id = rs.user_id
                GROUP BY r.id
                ORDER BY r.id DESC
            """).fetchall()
            rooms = [dict(row) for row in rows]
            return {'status': 'success', 'success': True, 'rooms': rooms}
        except Exception as exc:
            return {'status': 'error', 'success': False, 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def create_room(self, payload):
        conn = None
        try:
            logger.info('[REQUEST] action=create_room')
            conn = self.db.connect()
            if payload.get('role') != 'admin':
                return {'status': 'error', 'success': False, 'message': 'Không có quyền tạo phòng thi'}

            room = payload.get('room') or payload
            room_code = (room.get('room_code') or room.get('room_id') or '').strip().upper()
            if not room_code:
                return {'status': 'error', 'success': False, 'message': 'Mã phòng không được để trống'}

            name = (room.get('name') or '').strip()
            subject = (room.get('subject') or '').strip()
            if not name:
                return {'status': 'error', 'success': False, 'message': 'Tên phòng không được để trống'}
            if not subject:
                return {'status': 'error', 'success': False, 'message': 'Môn thi không được để trống'}
            try:
                exam_id = int(room.get('exam_id'))
            except (TypeError, ValueError):
                return {'status': 'error', 'success': False, 'message': 'ID đề thi phải là số nguyên'}
            try:
                duration = int(room.get('duration'))
            except (TypeError, ValueError):
                return {'status': 'error', 'success': False, 'message': 'Thời lượng phải là số nguyên'}
            if duration <= 0:
                return {'status': 'error', 'success': False, 'message': 'Thời lượng phải lớn hơn 0 phút'}

            time_format = '%Y-%m-%d %H:%M'
            try:
                start_value = (room.get('start_time') or '').strip()
                end_value = (room.get('end_time') or '').strip()
                start_time_value = datetime.strptime(start_value, time_format)
                end_time_value = datetime.strptime(end_value, time_format)
            except (TypeError, ValueError):
                return {'status': 'error', 'success': False, 'message': 'Thời gian phải có định dạng YYYY-MM-DD HH:MM'}
            if start_time_value <= datetime.now():
                return {'status': 'error', 'success': False, 'message': 'Thời gian bắt đầu đã ở trong quá khứ'}
            if end_time_value <= start_time_value:
                return {'status': 'error', 'success': False, 'message': 'Thời gian kết thúc phải sau thời gian bắt đầu'}
            start_time = start_time_value.strftime(time_format)
            end_time = end_time_value.strftime(time_format)
            status = (room.get('status') or 'DRAFT').upper()
            if status not in ('DRAFT', 'WAITING', 'RUNNING', 'FINISHED', 'CANCELLED'):
                return {'status': 'error', 'success': False, 'message': 'Trạng thái phòng không hợp lệ'}

            duplicate = conn.execute('SELECT 1 FROM exam_rooms WHERE room_code = ?', (room_code,)).fetchone()
            if duplicate:
                return {'status': 'error', 'success': False, 'message': f'Mã phòng {room_code} đã tồn tại'}
            password = (room.get('password') or '').strip()
            auto_submit = 1 if room.get('auto_submit') is not False else 0
            shuffle_questions = 1 if room.get('shuffle_questions') is not False else 0
            shuffle_answers = 1 if room.get('shuffle_answers') is not False else 0
            max_attempts = int(room.get('max_attempts') or 1)
            allow_join = 1 if room.get('allow_join') is not False else 0

            exam = conn.execute("SELECT id FROM exams WHERE id = ?", (exam_id,)).fetchone()
            if not exam:
                return {'status': 'error', 'success': False, 'message': f'Đề thi ID {exam_id} không tồn tại'}

            logger.info('[ROOM] database insert room_code=%s exam_id=%s', room_code, exam_id)
            conn.execute("""
                INSERT INTO exam_rooms (room_code, name, exam_id, subject, duration, start_time, end_time,
                status, password, auto_submit, shuffle_questions, shuffle_answers, max_attempts, allow_join,
                created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (room_code, name, exam_id, subject, duration, start_time, end_time,
                  status, password, auto_submit, shuffle_questions, shuffle_answers, max_attempts,
                  allow_join, datetime.now().isoformat()))
            conn.commit()
            logger.info('[ROOM] create success room_code=%s', room_code)
            return {'status': 'success', 'success': True, 'message': 'Phòng thi được tạo'}
        except sqlite3.IntegrityError as exc:
            logger.exception('[ROOM ERROR] database constraint failed')
            return {'status': 'error', 'success': False, 'message': f'Không thể tạo phòng thi: {exc}'}
        except Exception as exc:
            logger.exception('[ROOM ERROR] create_room failed')
            return {'status': 'error', 'success': False, 'message': str(exc)}
        finally:
            if conn is not None:
                conn.close()

    def update_room(self, payload):
        try:
            conn = self.db.connect()
            if payload.get('role') != 'admin':
                return {'status': 'error', 'success': False, 'message': 'Không có quyền cập nhật phòng thi'}
            room = payload.get('room') or payload
            room_id = room.get('id') or payload.get('id')
            if not room_id:
                return {'status': 'error', 'success': False, 'message': 'Thiếu id phòng thi'}

            conn.execute("""
                UPDATE exam_rooms
                SET room_code = ?, name = ?, exam_id = ?, subject = ?, duration = ?,
                    start_time = ?, end_time = ?, status = ?, password = ?, auto_submit = ?,
                    shuffle_questions = ?, shuffle_answers = ?, max_attempts = ?, allow_join = ?
                WHERE id = ?
            """, (
                (room.get('room_code') or '').strip().upper(),
                (room.get('name') or '').strip(),
                room.get('exam_id'),
                (room.get('subject') or '').strip(),
                int(room.get('duration') or 60),
                room.get('start_time') or '',
                room.get('end_time') or '',
                (room.get('status') or 'DRAFT').upper(),
                (room.get('password') or '').strip(),
                int(room.get('auto_submit') or 0),
                int(room.get('shuffle_questions') or 0),
                int(room.get('shuffle_answers') or 0),
                int(room.get('max_attempts') or 1),
                int(room.get('allow_join') or 0),
                room_id,
            ))
            conn.commit()
            return {'status': 'success', 'success': True, 'message': 'Phòng thi được cập nhật'}
        except Exception as exc:
            return {'status': 'error', 'success': False, 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def delete_room(self, payload):
        try:
            conn = self.db.connect()
            if payload.get('role') != 'admin':
                return {'status': 'error', 'success': False, 'message': 'Không có quyền xóa phòng thi'}
            room_id = payload.get('room_id') or payload.get('id')
            if not room_id:
                return {'status': 'error', 'success': False, 'message': 'Thiếu room_id'}
            conn.execute("DELETE FROM exam_rooms WHERE id = ?", (room_id,))
            conn.commit()
            return {'status': 'success', 'success': True, 'message': 'Phòng thi được xóa'}
        except Exception as exc:
            return {'status': 'error', 'success': False, 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def open_room(self, payload):
        return self._set_status(payload, 'WAITING')

    def start_room(self, payload):
        return self._set_status(payload, 'RUNNING')

    def close_room(self, payload):
        return self._set_status(payload, 'CANCELLED')

    def finish_room(self, payload):
        return self._set_status(payload, 'FINISHED')

    def _set_status(self, payload, status):
        try:
            conn = self.db.connect()
            if payload.get('role') != 'admin':
                return {'status': 'error', 'success': False, 'message': 'Không có quyền'}
            room_id = payload.get('room_id') or payload.get('id')
            if not room_id:
                return {'status': 'error', 'success': False, 'message': 'Thiếu room_id'}
            if status == 'RUNNING':
                question_count = conn.execute('''
                    SELECT COUNT(*) AS count
                    FROM exam_questions eq
                    JOIN exam_rooms r ON r.exam_id = eq.exam_id
                    WHERE r.id = ?
                ''', (room_id,)).fetchone()['count']
                if question_count == 0:
                    return {'status': 'error', 'success': False, 'message': 'Đề thi chưa có câu hỏi'}
            conn.execute("UPDATE exam_rooms SET status = ? WHERE id = ?", (status, room_id))
            conn.commit()
            return {'status': 'success', 'success': True, 'message': f'Phòng thi chuyển sang {status}'}
        except Exception as exc:
            return {'status': 'error', 'success': False, 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def get_room_students(self, payload):
        try:
            conn = self.db.connect()
            room_id = payload.get('room_id') or payload.get('id')
            rows = conn.execute("""
                SELECT u.id, u.student_code, u.full_name, u.username, u.class_name,
                       rs.joined_at, rs.started_at, rs.submitted_at, rs.status,
                       s.last_seen, s.status AS session_status
                FROM room_students rs
                JOIN users u ON u.id = rs.user_id
                LEFT JOIN sessions s ON s.user_id = rs.user_id
                WHERE rs.room_id = ?
                ORDER BY u.full_name
            """, (room_id,)).fetchall()
            return {'status': 'success', 'success': True, 'room_students': [dict(r) for r in rows]}
        except Exception as exc:
            return {'status': 'error', 'success': False, 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def join_room(self, payload):
        try:
            conn = self.db.connect()
            room_id = payload.get('room_id')
            user_id = payload.get('user_id')
            if not room_id or not user_id:
                return {'status': 'error', 'success': False, 'message': 'Thiếu phòng hoặc sinh viên'}
            existing = conn.execute("SELECT id FROM room_students WHERE room_id = ? AND user_id = ?", (room_id, user_id)).fetchone()
            if existing:
                return {'status': 'success', 'success': True, 'message': 'Sinh viên đã ở trong phòng'}
            conn.execute("INSERT INTO room_students (room_id, user_id, joined_at, status) VALUES (?, ?, ?, ?)",
                         (room_id, user_id, datetime.now().isoformat(), 'JOINED'))
            conn.commit()
            return {'status': 'success', 'success': True, 'message': 'Sinh viên được thêm vào phòng'}
        except Exception as exc:
            return {'status': 'error', 'success': False, 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def get_online_students(self, payload):
        try:
            conn = self.db.connect()
            rows = conn.execute("""
                SELECT u.id, u.full_name, u.student_code, u.username, u.class_name,
                       s.status AS session_status, s.last_seen
                FROM users u
                LEFT JOIN sessions s ON s.user_id = u.id
                WHERE u.role = 'student'
                ORDER BY u.full_name
            """).fetchall()
            students = [dict(row) for row in rows]
            return {'status': 'success', 'success': True, 'students': students}
        except Exception as exc:
            return {'status': 'error', 'success': False, 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

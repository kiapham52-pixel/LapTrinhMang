import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.database import DatabaseManager


class ExamService:
    def __init__(self, db_path):
        self.db = DatabaseManager(db_path)

    def get_exams(self):
        try:
            conn = self.db.connect()
            exam_rows = conn.execute("SELECT * FROM exams ORDER BY id").fetchall()
            exams = []
            for exam in exam_rows:
                exam_dict = dict(exam)
                subject_rows = conn.execute("""
                    SELECT DISTINCT q.subject
                    FROM exam_questions eq
                    JOIN questions q ON q.id = eq.question_id
                    WHERE eq.exam_id = ?
                    ORDER BY q.subject
                """, (exam['id'],)).fetchall()
                subjects = [r['subject'] for r in subject_rows]
                exam_dict['subject'] = ', '.join(subjects) if subjects else 'Chưa có môn'
                exams.append(exam_dict)
            return {'status': 'success', 'exams': exams}
        except Exception as exc:
            return {'status': 'error', 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def start_exam(self, payload):
        try:
            conn = self.db.connect()
            user_id = payload.get('user_id')
            role = payload.get('role')
            exam_id = payload.get('exam_id')

            if role != 'student':
                return {'status': 'error', 'success': False, 'message': 'Chỉ sinh viên mới được vào thi'}
            if not user_id:
                return {'status': 'error', 'success': False, 'message': 'Chưa đăng nhập'}
            if not exam_id:
                return {'status': 'error', 'success': False, 'message': 'Thiếu exam_id'}

            exam = conn.execute("SELECT * FROM exams WHERE id = ?", (exam_id,)).fetchone()
            if not exam:
                return {'status': 'error', 'success': False, 'message': 'Kỳ thi không tồn tại'}
            if exam['status'] != 'active':
                return {'status': 'error', 'success': False, 'message': 'Kỳ thi đã đóng'}

            rows = conn.execute("""
                SELECT q.id, q.content AS question_text, q.option_a, q.option_b, q.option_c, q.option_d, q.subject
                FROM questions q
                JOIN exam_questions eq ON q.id = eq.question_id
                WHERE eq.exam_id = ?
                ORDER BY q.id
            """, (exam_id,)).fetchall()

            if not rows:
                return {'status': 'error', 'success': False, 'message': 'Kỳ thi không có câu hỏi'}

            exam_payload = dict(exam)
            exam_payload['questions'] = [dict(r) for r in rows]
            subjects = sorted({r['subject'] for r in rows})
            exam_payload['subject'] = subjects[0] if len(subjects) == 1 else ', '.join(subjects)
            return {'status': 'success', 'success': True, 'action': 'start_exam', 'exam': exam_payload}
        except Exception as exc:
            return {'status': 'error', 'success': False, 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def create_exam(self, payload):
        try:
            conn = self.db.connect()
            conn.execute("INSERT INTO exams (title, description, duration, total_questions, status) VALUES (?, ?, ?, ?, ?)",
                         (payload.get('title'), payload.get('description'), payload.get('duration'), payload.get('total_questions'), payload.get('status', 'active')))
            conn.commit()
            return {'status': 'success', 'message': 'Đề thi được tạo'}
        except Exception as exc:
            return {'status': 'error', 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def update_exam(self, payload):
        try:
            conn = self.db.connect()
            conn.execute("UPDATE exams SET title = ?, description = ?, duration = ?, total_questions = ?, status = ? WHERE id = ?",
                         (payload.get('title'), payload.get('description'), payload.get('duration'), payload.get('total_questions'), payload.get('status'), payload.get('id')))
            conn.commit()
            return {'status': 'success', 'message': 'Đề thi được cập nhật'}
        except Exception as exc:
            return {'status': 'error', 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def delete_exam(self, exam_id):
        try:
            conn = self.db.connect()
            conn.execute("DELETE FROM exams WHERE id = ?", (exam_id,))
            conn.commit()
            return {'status': 'success', 'message': 'Đề thi được xóa'}
        except Exception as exc:
            return {'status': 'error', 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

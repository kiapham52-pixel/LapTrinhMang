import os
import sys
import logging
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.database import DatabaseManager


logger = logging.getLogger(__name__)


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
                exam_dict['total_questions'] = conn.execute(
                    'SELECT COUNT(*) AS count FROM exam_questions WHERE exam_id = ?',
                    (exam['id'],)
                ).fetchone()['count']
                subject_rows = conn.execute("""
                    SELECT DISTINCT q.subject
                    FROM exam_questions eq
                    JOIN questions q ON q.id = eq.question_id
                    WHERE eq.exam_id = ?
                    ORDER BY q.subject
                """, (exam['id'],)).fetchall()
                subjects = [r['subject'] for r in subject_rows]
                exam_dict['subject'] = exam_dict.get('subject') or (', '.join(subjects) if subjects else 'Chưa có môn')
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
            logger.info('[EXAM] student=%s started exam=%s', user_id, exam_id)
            return {'status': 'success', 'success': True, 'action': 'start_exam', 'exam': exam_payload}
        except Exception as exc:
            return {'status': 'error', 'success': False, 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def use_lifeline(self, payload):
        conn = None
        try:
            if payload.get('role') != 'student':
                return {'status': 'error', 'success': False, 'message': 'Chỉ sinh viên được dùng hỗ trợ'}
            user_id = payload.get('user_id')
            exam_id = payload.get('exam_id')
            question_id = payload.get('question_id')
            if not user_id or not exam_id or not question_id:
                return {'status': 'error', 'success': False, 'message': 'Thiếu thông tin câu hỏi'}

            conn = self.db.connect()
            student = conn.execute("SELECT id FROM users WHERE id = ? AND role = 'student'", (user_id,)).fetchone()
            if not student:
                return {'status': 'error', 'success': False, 'message': 'Tài khoản sinh viên không hợp lệ'}
            question = conn.execute("""
                SELECT q.id, q.correct_answer
                FROM questions q
                JOIN exam_questions eq ON eq.question_id = q.id
                WHERE eq.exam_id = ? AND q.id = ?
            """, (exam_id, question_id)).fetchone()
            if not question:
                return {'status': 'error', 'success': False, 'message': 'Câu hỏi không thuộc kỳ thi'}

            letters = ['A', 'B', 'C', 'D']
            wrong_answers = [letter for letter in letters if letter != question['correct_answer']]
            visible_options = [question['correct_answer'], random.choice(wrong_answers)]
            random.shuffle(visible_options)
            logger.info('[EXAM] lifeline student=%s exam=%s question=%s', user_id, exam_id, question_id)
            return {'status': 'success', 'success': True, 'action': 'use_lifeline_result', 'visible_options': visible_options}
        except Exception as exc:
            logger.exception('[EXAM] lifeline_error')
            return {'status': 'error', 'success': False, 'message': str(exc)}
        finally:
            if conn is not None:
                conn.close()

    def create_exam(self, payload):
        try:
            conn = self.db.connect()
            if payload.get('role') != 'admin':
                return {'status': 'error', 'success': False, 'message': 'Không có quyền tạo đề thi'}
            title = (payload.get('title') or '').strip()
            if not title:
                return {'status': 'error', 'success': False, 'message': 'Tên đề không được để trống'}
            subject = (payload.get('subject') or '').strip()
            if not subject:
                return {'status': 'error', 'success': False, 'message': 'Vui lòng chọn môn học'}
            conn.execute("INSERT INTO exams (title, description, duration, total_questions, subject, status) VALUES (?, ?, ?, ?, ?, ?)",
                         (title, payload.get('description'), int(payload.get('duration') or 30), 0, subject, payload.get('status', 'active')))
            conn.commit()
            exam_id = conn.execute('SELECT last_insert_rowid() AS id').fetchone()['id']
            return {'status': 'success', 'success': True, 'exam_id': exam_id, 'message': 'Đề thi được tạo'}
        except Exception as exc:
            return {'status': 'error', 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def get_exam_questions(self, payload):
        conn = None
        try:
            exam_id = payload.get('exam_id')
            if not exam_id:
                return {'status': 'error', 'success': False, 'message': 'Thiếu exam_id'}
            conn = self.db.connect()
            rows = conn.execute('''
                SELECT q.* FROM questions q
                JOIN exam_questions eq ON eq.question_id = q.id
                WHERE eq.exam_id = ? ORDER BY q.id
            ''', (exam_id,)).fetchall()
            return {'status': 'success', 'success': True, 'questions': [dict(row) for row in rows]}
        except Exception as exc:
            return {'status': 'error', 'success': False, 'message': str(exc)}
        finally:
            if conn is not None:
                conn.close()

    def add_questions(self, payload):
        conn = None
        try:
            if payload.get('role') != 'admin':
                return {'status': 'error', 'success': False, 'message': 'Không có quyền quản lý đề thi'}
            exam_id = payload.get('exam_id')
            question_ids = payload.get('question_ids') or []
            if not exam_id or not question_ids:
                return {'status': 'error', 'success': False, 'message': 'Chưa chọn câu hỏi hoặc đề thi'}
            conn = self.db.connect()
            if not conn.execute('SELECT 1 FROM exams WHERE id = ?', (exam_id,)).fetchone():
                return {'status': 'error', 'success': False, 'message': 'Đề thi không tồn tại'}
            added = 0
            skipped = 0
            for question_id in question_ids:
                if not conn.execute('SELECT 1 FROM questions WHERE id = ?', (question_id,)).fetchone():
                    return {'status': 'error', 'success': False, 'message': f'Câu hỏi ID {question_id} không tồn tại'}
                exists = conn.execute('SELECT 1 FROM exam_questions WHERE exam_id = ? AND question_id = ?', (exam_id, question_id)).fetchone()
                if exists:
                    skipped += 1
                    continue
                conn.execute('INSERT INTO exam_questions (exam_id, question_id) VALUES (?, ?)', (exam_id, question_id))
                added += 1
            conn.commit()
            return {'status': 'success', 'success': True, 'added': added, 'skipped': skipped, 'message': f'Đã thêm {added} câu hỏi'}
        except Exception as exc:
            if conn is not None:
                conn.rollback()
            return {'status': 'error', 'success': False, 'message': str(exc)}
        finally:
            if conn is not None:
                conn.close()

    def remove_question(self, payload):
        conn = None
        try:
            if payload.get('role') != 'admin':
                return {'status': 'error', 'success': False, 'message': 'Không có quyền quản lý đề thi'}
            conn = self.db.connect()
            cursor = conn.execute('DELETE FROM exam_questions WHERE exam_id = ? AND question_id = ?', (payload.get('exam_id'), payload.get('question_id')))
            if cursor.rowcount == 0:
                return {'status': 'error', 'success': False, 'message': 'Câu hỏi không thuộc đề thi'}
            conn.commit()
            return {'status': 'success', 'success': True, 'message': 'Đã xóa câu hỏi khỏi đề'}
        except Exception as exc:
            if conn is not None:
                conn.rollback()
            return {'status': 'error', 'success': False, 'message': str(exc)}
        finally:
            if conn is not None:
                conn.close()

    def update_exam(self, payload):
        try:
            conn = self.db.connect()
            if payload.get('role') != 'admin':
                return {'status': 'error', 'success': False, 'message': 'Không có quyền sửa đề thi'}
            title = (payload.get('title') or '').strip()
            if not title:
                return {'status': 'error', 'success': False, 'message': 'Tên đề không được để trống'}
            duration = int(payload.get('duration') or 30)
            if duration <= 0:
                return {'status': 'error', 'success': False, 'message': 'Thời lượng phải lớn hơn 0'}
            conn.execute("UPDATE exams SET title = ?, description = ?, duration = ?, total_questions = ?, subject = COALESCE(NULLIF(?, ''), subject), status = ? WHERE id = ?",
                         (title, payload.get('description'), duration,
                          conn.execute('SELECT COUNT(*) FROM exam_questions WHERE exam_id = ?', (payload.get('id'),)).fetchone()[0],
                          payload.get('subject') or '', payload.get('status') or 'active', payload.get('id')))
            conn.commit()
            return {'status': 'success', 'message': 'Đề thi được cập nhật'}
        except Exception as exc:
            return {'status': 'error', 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def delete_exam(self, exam_id, role='admin'):
        try:
            conn = self.db.connect()
            if role != 'admin':
                return {'status': 'error', 'success': False, 'message': 'Không có quyền xóa đề thi'}
            if not exam_id:
                return {'status': 'error', 'success': False, 'message': 'Thiếu exam_id'}
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

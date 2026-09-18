import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.database import DatabaseManager


class QuestionService:
    def __init__(self, db_path):
        self.db = DatabaseManager(db_path)

    def get_questions(self, exam_id=None, payload=None):
        try:
            conn = self.db.connect()
            if payload and payload.get('role') != 'admin' and not exam_id:
                return {'status': 'error', 'success': False, 'message': 'Không có quyền'}

            rows = []
            if exam_id:
                rows = conn.execute('''
                    SELECT q.* FROM questions q
                    JOIN exam_questions eq ON q.id = eq.question_id
                    WHERE eq.exam_id = ?
                    ORDER BY q.id
                ''', (exam_id,)).fetchall()
            else:
                rows = conn.execute('''
                    SELECT q.*, COUNT(DISTINCT eq.exam_id) AS exam_count
                    FROM questions q LEFT JOIN exam_questions eq ON eq.question_id = q.id
                    GROUP BY q.id ORDER BY q.id
                ''').fetchall()

            questions = [dict(r) for r in rows]
            return {'status': 'success', 'success': True, 'questions': questions}
        except Exception as exc:
            return {'status': 'error', 'success': False, 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def search_questions(self, payload):
        try:
            conn = self.db.connect()
            if payload.get('role') != 'admin':
                return {'status': 'error', 'success': False, 'message': 'Không có quyền'}

            keyword = (payload.get('keyword') or '').strip().lower()
            if not keyword:
                return self.get_questions(None, payload)

            rows = conn.execute("""
                SELECT q.*, COUNT(DISTINCT eq.exam_id) AS exam_count
                FROM questions q LEFT JOIN exam_questions eq ON eq.question_id = q.id
                WHERE LOWER(content) LIKE ?
                   OR LOWER(subject) LIKE ?
                   OR LOWER(difficulty) LIKE ?
                GROUP BY q.id
                ORDER BY id
            """, (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%')).fetchall()
            return {'status': 'success', 'success': True, 'questions': [dict(r) for r in rows]}
        except Exception as exc:
            return {'status': 'error', 'success': False, 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def create_question(self, payload):
        try:
            conn = self.db.connect()
            if payload.get('role') != 'admin':
                return {'status': 'error', 'success': False, 'message': 'Không có quyền'}

            question = payload.get('question', {}) or {}
            question_text = (question.get('question_text') or '').strip()
            option_a = (question.get('option_a') or '').strip()
            option_b = (question.get('option_b') or '').strip()
            option_c = (question.get('option_c') or '').strip()
            option_d = (question.get('option_d') or '').strip()
            correct_answer = (question.get('correct_answer') or '').strip().upper()
            subject = (question.get('subject') or '').strip()
            difficulty = (question.get('difficulty') or '').strip()

            if not question_text or not all([option_a, option_b, option_c, option_d]):
                return {'status': 'error', 'success': False, 'message': 'Nội dung và 4 đáp án không được rỗng'}
            if correct_answer not in ('A', 'B', 'C', 'D'):
                return {'status': 'error', 'success': False, 'message': 'Đáp án đúng phải là A/B/C/D'}
            if not subject:
                return {'status': 'error', 'success': False, 'message': 'Môn học không được rỗng'}
            if difficulty not in ('Dễ', 'Trung bình', 'Khó', 'easy', 'medium', 'hard'):
                return {'status': 'error', 'success': False, 'message': 'Độ khó không hợp lệ'}

            difficulty_map = {'Dễ': 'Dễ', 'Trung bình': 'Trung bình', 'Khó': 'Khó', 'easy': 'Dễ', 'medium': 'Trung bình', 'hard': 'Khó'}
            difficulty = difficulty_map.get(difficulty, difficulty)

            conn.execute("""
                INSERT INTO questions (content, option_a, option_b, option_c, option_d, correct_answer, subject, difficulty, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (question_text, option_a, option_b, option_c, option_d, correct_answer, subject, difficulty))
            conn.commit()
            return {'status': 'success', 'success': True, 'message': 'Câu hỏi được thêm'}
        except Exception as exc:
            return {'status': 'error', 'success': False, 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def update_question(self, payload):
        try:
            conn = self.db.connect()
            if payload.get('role') != 'admin':
                return {'status': 'error', 'success': False, 'message': 'Không có quyền'}

            question_id = payload.get('question_id')
            if not question_id:
                return {'status': 'error', 'success': False, 'message': 'Thiếu question_id'}

            question = payload.get('question', {}) or {}
            question_text = (question.get('question_text') or '').strip()
            option_a = (question.get('option_a') or '').strip()
            option_b = (question.get('option_b') or '').strip()
            option_c = (question.get('option_c') or '').strip()
            option_d = (question.get('option_d') or '').strip()
            correct_answer = (question.get('correct_answer') or '').strip().upper()
            subject = (question.get('subject') or '').strip()
            difficulty = (question.get('difficulty') or '').strip()

            if not question_text or not all([option_a, option_b, option_c, option_d]):
                return {'status': 'error', 'success': False, 'message': 'Nội dung và 4 đáp án không được rỗng'}
            if correct_answer not in ('A', 'B', 'C', 'D'):
                return {'status': 'error', 'success': False, 'message': 'Đáp án đúng phải là A/B/C/D'}
            if not subject:
                return {'status': 'error', 'success': False, 'message': 'Môn học không được rỗng'}
            if difficulty not in ('Dễ', 'Trung bình', 'Khó', 'easy', 'medium', 'hard'):
                return {'status': 'error', 'success': False, 'message': 'Độ khó không hợp lệ'}

            difficulty_map = {'Dễ': 'Dễ', 'Trung bình': 'Trung bình', 'Khó': 'Khó', 'easy': 'Dễ', 'medium': 'Trung bình', 'hard': 'Khó'}
            difficulty = difficulty_map.get(difficulty, difficulty)

            conn.execute("""
                UPDATE questions
                SET content = ?, option_a = ?, option_b = ?, option_c = ?, option_d = ?,
                    correct_answer = ?, subject = ?, difficulty = ?
                WHERE id = ?
            """, (question_text, option_a, option_b, option_c, option_d, correct_answer, subject, difficulty, question_id))
            conn.commit()
            return {'status': 'success', 'success': True, 'message': 'Câu hỏi được cập nhật'}
        except Exception as exc:
            return {'status': 'error', 'success': False, 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def delete_question(self, payload):
        try:
            conn = self.db.connect()
            if payload.get('role') != 'admin':
                return {'status': 'error', 'success': False, 'message': 'Không có quyền'}

            question_id = payload.get('question_id')
            if not question_id:
                return {'status': 'error', 'success': False, 'message': 'Thiếu question_id'}

            used = conn.execute("SELECT id FROM exam_questions WHERE question_id = ?", (question_id,)).fetchone()
            if used:
                return {'status': 'error', 'success': False, 'message': 'Không thể xóa câu hỏi đang được sử dụng trong kỳ thi.'}

            conn.execute("DELETE FROM questions WHERE id = ?", (question_id,))
            conn.commit()
            return {'status': 'success', 'success': True, 'message': 'Câu hỏi được xóa'}
        except Exception as exc:
            return {'status': 'error', 'success': False, 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

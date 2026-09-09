import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.database import DatabaseManager


class ResultService:
    def __init__(self, db_path):
        self.db = DatabaseManager(db_path)

    def get_all_results(self, payload):
        try:
            conn = self.db.connect()
            role = payload.get('role') if isinstance(payload, dict) else None
            if role != 'admin':
                return {'status': 'error', 'success': False, 'message': 'Chỉ admin được xem toàn bộ kết quả'}

            rows = conn.execute("""
                SELECT a.id, a.user_id, a.exam_id, a.score, a.correct_answers, a.wrong_answers,
                       a.duration, a.started_at, a.submitted_at,
                       e.title AS exam_title, e.description AS exam_description,
                       u.full_name, u.student_code, u.class_name, u.username
                FROM attempts a
                JOIN exams e ON e.id = a.exam_id
                JOIN users u ON u.id = a.user_id
                ORDER BY a.submitted_at DESC
            """).fetchall()

            return {
                'status': 'success',
                'success': True,
                'action': 'get_all_results',
                'results': [dict(r) for r in rows],
                'message': 'Danh sách toàn bộ kết quả thi'
            }
        except Exception as exc:
            return {'status': 'error', 'success': False, 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def get_result(self, payload):
        try:
            conn = self.db.connect()
            attempt_id = payload.get('attempt_id') if isinstance(payload, dict) else payload
            role = payload.get('role') if isinstance(payload, dict) else None
            user_id = payload.get('user_id') if isinstance(payload, dict) else None

            if role not in ('student', 'admin'):
                return {'status': 'error', 'success': False, 'message': 'Chỉ sinh viên hoặc admin được xem kết quả'}
            if not attempt_id:
                return {'status': 'error', 'success': False, 'message': 'Thiếu attempt_id'}

            attempt = conn.execute("SELECT * FROM attempts WHERE id = ?", (attempt_id,)).fetchone()
            if not attempt:
                return {'status': 'error', 'success': False, 'message': 'Không tìm thấy kết quả'}
            if role == 'student' and user_id and int(attempt['user_id']) != int(user_id):
                return {'status': 'error', 'success': False, 'message': 'Bạn chỉ xem được lịch sử kết quả của mình'}

            return {'status': 'success', 'success': True, 'result': dict(attempt)}
        except Exception as exc:
            return {'status': 'error', 'success': False, 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def submit_exam(self, payload):
        try:
            conn = self.db.connect()
            user_id = payload.get('user_id')
            exam_id = payload.get('exam_id')
            role = payload.get('role')
            answers = payload.get('answers', []) or []

            if role != 'student':
                return {'status': 'error', 'success': False, 'message': 'Chỉ sinh viên được nộp bài'}
            if not user_id:
                return {'status': 'error', 'success': False, 'message': 'Chưa xác định người thi'}
            if not exam_id:
                return {'status': 'error', 'success': False, 'message': 'Thiếu exam_id'}

            questions = conn.execute('''SELECT q.id, q.correct_answer FROM questions q
                JOIN exam_questions eq ON q.id = eq.question_id
                WHERE eq.exam_id = ?''', (exam_id,)).fetchall()
            correct_ids = {r['id']: r['correct_answer'] for r in questions}
            total_questions = len(correct_ids)

            correct_count = 0
            wrong_count = 0
            answers_rows = []

            for item in answers:
                qid = int(item.get('question_id'))
                selected = item.get('answer')
                correct_answer = correct_ids.get(qid)
                is_correct = 1 if correct_answer == selected else 0
                if is_correct:
                    correct_count += 1
                else:
                    wrong_count += 1
                answers_rows.append((qid, selected, correct_answer, is_correct))

            answered_questions = correct_count + wrong_count
            unanswered_questions = total_questions - answered_questions
            score = round((correct_count / total_questions) * 10, 2) if total_questions else 0
            duration = int(payload.get('duration', 0))
            now = datetime.now().isoformat()

            conn.execute("INSERT INTO attempts (user_id, exam_id, score, correct_answers, wrong_answers, duration, started_at, submitted_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                         (user_id, exam_id, score, correct_count, wrong_count, duration, now, now))
            attempt_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()['id']

            for qid, selected, correct_answer, is_correct in answers_rows:
                conn.execute("INSERT INTO answers (attempt_id, question_id, selected_answer, correct_answer, is_correct) VALUES (?, ?, ?, ?, ?)",
                             (attempt_id, qid, selected, correct_answer, is_correct))

            conn.commit()
            return {
                'status': 'success',
                'success': True,
                'action': 'submit_exam_result',
                'message': 'Bài thi đã nộp',
                'attempt_id': attempt_id,
                'result': {
                    'total_questions': total_questions,
                    'answered_questions': answered_questions,
                    'correct_answers': correct_count,
                    'wrong_answers': wrong_count,
                    'unanswered_questions': unanswered_questions,
                    'score': score,
                }
            }
        except Exception as exc:
            return {'status': 'error', 'success': False, 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def get_history(self, payload):
        try:
            conn = self.db.connect()
            if isinstance(payload, dict):
                role = payload.get('role')
                user_id = payload.get('user_id')
            else:
                role = None
                user_id = payload

            if role != 'student':
                return {'status': 'error', 'success': False, 'message': 'Chỉ sinh viên được xem lịch sử'}
            if not user_id:
                return {'status': 'error', 'success': False, 'message': 'Thiếu user_id'}

            rows = conn.execute("SELECT a.*, e.title FROM attempts a JOIN exams e ON e.id = a.exam_id WHERE a.user_id = ? ORDER BY a.submitted_at DESC", (user_id,)).fetchall()
            return {'status': 'success', 'success': True, 'history': [dict(r) for r in rows]}
        except Exception as exc:
            return {'status': 'error', 'success': False, 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

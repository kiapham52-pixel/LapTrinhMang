import os
import sys
import logging
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.database import DatabaseManager


logger = logging.getLogger(__name__)


class ResultService:
    def __init__(self, db_path):
        self.db = DatabaseManager(db_path)

    def get_dashboard_statistics(self, payload=None):
        try:
            conn = self.db.connect()
            if isinstance(payload, dict) and payload.get('role') != 'admin':
                return {'status': 'error', 'success': False, 'message': 'Chỉ admin được xem thống kê dashboard'}

            total_students = conn.execute("SELECT COUNT(*) AS c FROM users WHERE role = 'student'").fetchone()['c']
            online_students = conn.execute("""
                SELECT COUNT(*) AS c
                FROM sessions s
                JOIN users u ON u.id = s.user_id
                WHERE u.role = 'student' AND s.status = 'ONLINE'
            """).fetchone()['c']
            total_exams = conn.execute("SELECT COUNT(*) AS c FROM exams").fetchone()['c']
            total_subjects = conn.execute("SELECT COUNT(*) AS c FROM subjects").fetchone()['c']
            total_questions = conn.execute("SELECT COUNT(*) AS c FROM questions").fetchone()['c']
            total_rooms = conn.execute("SELECT COUNT(*) AS c FROM exam_rooms").fetchone()['c']
            total_attempts = conn.execute("SELECT COUNT(*) AS c FROM attempts").fetchone()['c']
            completed_attempts = conn.execute("SELECT COUNT(*) AS c FROM attempts WHERE submitted_at IS NOT NULL").fetchone()['c']
            avg_score = conn.execute("SELECT COALESCE(ROUND(AVG(score), 2), 0) AS c FROM attempts").fetchone()['c']
            highest_score = conn.execute("SELECT COALESCE(MAX(score), 0) AS c FROM attempts").fetchone()['c']
            lowest_score = conn.execute("SELECT COALESCE(MIN(score), 0) AS c FROM attempts").fetchone()['c']

            active_rooms = conn.execute("""
                SELECT r.id, r.room_code, r.name, r.status, e.title AS exam_title,
                       COUNT(rs.user_id) AS students_count,
                       COALESCE((SELECT COUNT(*) FROM sessions s JOIN users u ON u.id = s.user_id WHERE u.role = 'student' AND s.status = 'ONLINE'), 0) AS online_count,
                       COALESCE((SELECT COUNT(*) FROM attempts a WHERE a.exam_id = r.exam_id), 0) AS attempts_count
                FROM exam_rooms r
                JOIN exams e ON e.id = r.exam_id
                LEFT JOIN room_students rs ON rs.room_id = r.id
                WHERE r.status IN ('WAITING', 'RUNNING')
                GROUP BY r.id
                ORDER BY r.id DESC
            """).fetchall()

            running_exam_rows = []
            for row in active_rooms:
                running_exam_rows.append({
                    'id': row['id'],
                    'room_code': row['room_code'],
                    'name': row['name'],
                    'exam_title': row['exam_title'],
                    'students_count': row['students_count'],
                    'online_count': row['online_count'],
                    'attempts_count': row['attempts_count'],
                    'status': row['status'],
                })

            return {
                'status': 'success',
                'success': True,
                'action': 'get_dashboard_statistics',
                'statistics': {
                    'total_students': total_students,
                    'online_students': online_students,
                    'total_exams': total_exams,
                    'total_subjects': total_subjects,
                    'total_questions': total_questions,
                    'total_rooms': total_rooms,
                    'total_attempts': total_attempts,
                    'completed_attempts': completed_attempts,
                    'active_attempts': 0,
                    'average_score': avg_score,
                    'highest_score': highest_score,
                    'lowest_score': lowest_score,
                },
                'active_rooms': running_exam_rows,
                'message': 'Dashboard statistics loaded'
            }
        except Exception as exc:
            return {'status': 'error', 'success': False, 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def get_statistics(self, payload=None):
        try:
            conn = self.db.connect()
            if isinstance(payload, dict) and payload.get('role') != 'admin':
                return {'status': 'error', 'success': False, 'message': 'Chỉ admin được xem thống kê'}

            total_students = conn.execute("SELECT COUNT(*) AS c FROM users WHERE role = 'student'").fetchone()['c']
            total_exams = conn.execute("SELECT COUNT(*) AS c FROM exams").fetchone()['c']
            total_rooms = conn.execute("SELECT COUNT(*) AS c FROM exam_rooms").fetchone()['c']
            total_attempts = conn.execute("SELECT COUNT(*) AS c FROM attempts").fetchone()['c']
            completed_attempts = conn.execute("SELECT COUNT(*) AS c FROM attempts WHERE submitted_at IS NOT NULL").fetchone()['c']
            active_attempts = conn.execute("SELECT COUNT(*) AS c FROM room_students WHERE status IN ('JOINED', 'IN_PROGRESS') AND submitted_at IS NULL").fetchone()['c']
            avg_score = conn.execute("SELECT COALESCE(ROUND(AVG(score), 2), 0) AS c FROM attempts").fetchone()['c']
            highest_score = conn.execute("SELECT COALESCE(MAX(score), 0) AS c FROM attempts").fetchone()['c']
            lowest_score = conn.execute("SELECT COALESCE(MIN(score), 0) AS c FROM attempts").fetchone()['c']

            exam_rows = conn.execute("""
                SELECT e.id, e.title,
                       COUNT(DISTINCT u.id) AS student_count,
                       COUNT(DISTINCT CASE WHEN a.id IS NOT NULL THEN a.id END) AS attempts_count,
                       COALESCE(ROUND(AVG(a.score), 2), 0) AS average_score,
                       COALESCE(MAX(a.score), 0) AS highest_score,
                       COALESCE(MIN(a.score), 0) AS lowest_score
                FROM exams e
                LEFT JOIN exam_questions eq ON eq.exam_id = e.id
                LEFT JOIN questions q ON q.id = eq.question_id
                LEFT JOIN attempts a ON a.exam_id = e.id
                LEFT JOIN users u ON u.id = a.user_id AND u.role = 'student'
                GROUP BY e.id
                ORDER BY e.id
            """).fetchall()

            per_exam = []
            for row in exam_rows:
                completed = conn.execute("SELECT COUNT(*) AS c FROM attempts WHERE exam_id = ?", (row['id'],)).fetchone()['c']
                # Per exam measure: students with an attempt and students without an attempt.
                total_for_exam = conn.execute("SELECT COUNT(*) AS c FROM users WHERE role = 'student'").fetchone()['c']
                per_exam.append({
                    'exam_id': row['id'],
                    'title': row['title'],
                    'student_count': row['student_count'],
                    'attempts_count': row['attempts_count'],
                    'average_score': row['average_score'],
                    'highest_score': row['highest_score'],
                    'lowest_score': row['lowest_score'],
                    'completed': completed,
                    'not_completed': max(0, total_for_exam - completed),
                })

            pass_threshold = conn.execute("SELECT COUNT(*) AS c FROM attempts WHERE score >= 5").fetchone()['c']
            fail_threshold = conn.execute("SELECT COUNT(*) AS c FROM attempts WHERE score < 5").fetchone()['c']

            return {
                'status': 'success',
                'success': True,
                'action': 'get_statistics',
                'statistics': {
                    'total_students': total_students,
                    'total_exams': total_exams,
                    'total_rooms': total_rooms,
                    'total_attempts': total_attempts,
                    'completed_attempts': completed_attempts,
                    'active_attempts': active_attempts,
                    'average_score': avg_score,
                    'highest_score': highest_score,
                    'lowest_score': lowest_score,
                    'pass_count': pass_threshold,
                    'fail_count': fail_threshold,
                },
                'per_exam': per_exam,
                'message': 'Statistics loaded'
            }
        except Exception as exc:
            return {'status': 'error', 'success': False, 'message': str(exc)}
        finally:
            try:
                conn.close()
            except Exception:
                pass

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
                       COALESCE(er.room_code, 'PH001') AS room_code,
                       u.full_name, u.student_code, u.class_name, u.username,
                       CASE WHEN a.submitted_at IS NOT NULL THEN 'Hoàn thành' ELSE 'Đang thi' END AS status
                FROM attempts a
                JOIN exams e ON e.id = a.exam_id
                JOIN users u ON u.id = a.user_id
                LEFT JOIN exam_rooms er ON er.exam_id = a.exam_id
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

            attempt = conn.execute("""
                SELECT a.*, e.title AS exam_title, u.full_name, u.student_code, u.class_name,
                       u.username
                FROM attempts a
                JOIN exams e ON e.id = a.exam_id
                JOIN users u ON u.id = a.user_id
                WHERE a.id = ?
            """, (attempt_id,)).fetchone()
            if not attempt:
                return {'status': 'error', 'success': False, 'message': 'Không tìm thấy kết quả'}
            if role == 'student' and user_id and int(attempt['user_id']) != int(user_id):
                return {'status': 'error', 'success': False, 'message': 'Bạn chỉ xem được lịch sử kết quả của mình'}

            answer_rows = conn.execute("""
                SELECT ans.question_id, ans.selected_answer, ans.correct_answer, ans.is_correct,
                       q.content AS question_text, q.option_a, q.option_b, q.option_c, q.option_d
                FROM answers ans
                JOIN questions q ON q.id = ans.question_id
                WHERE ans.attempt_id = ?
                ORDER BY ans.question_id
            """, (attempt_id,)).fetchall()
            answers = [dict(r) for r in answer_rows]

            return {
                'status': 'success',
                'success': True,
                'action': 'get_result',
                'result': dict(attempt),
                'answers': answers,
                'message': 'Chi tiết kết quả bài thi'
            }
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
            reason = payload.get('reason') or 'manual'
            submission_token = payload.get('submission_token')

            if role != 'student':
                return {'status': 'error', 'success': False, 'message': 'Chỉ sinh viên được nộp bài'}
            if not user_id:
                return {'status': 'error', 'success': False, 'message': 'Chưa xác định người thi'}
            if not exam_id:
                return {'status': 'error', 'success': False, 'message': 'Thiếu exam_id'}

            if reason != 'manual':
                logger.info('[EXAM] auto_submit reason=%s student=%s', reason, user_id)

            questions = conn.execute('''SELECT q.id, q.correct_answer FROM questions q
                JOIN exam_questions eq ON q.id = eq.question_id
                WHERE eq.exam_id = ?''', (exam_id,)).fetchall()
            correct_ids = {r['id']: r['correct_answer'] for r in questions}
            total_questions = len(correct_ids)

            if submission_token:
                existing = conn.execute('SELECT id, score, correct_answers, wrong_answers FROM attempts WHERE submission_token = ?', (submission_token,)).fetchone()
                if existing:
                    answered = existing['correct_answers'] + existing['wrong_answers']
                    return {
                        'status': 'success',
                        'success': True,
                        'action': 'submit_exam_result',
                        'message': 'Bài thi đã nộp',
                        'attempt_id': existing['id'],
                        'result': {
                            'total_questions': total_questions,
                            'answered_questions': answered,
                            'correct_answers': existing['correct_answers'],
                            'wrong_answers': existing['wrong_answers'],
                            'unanswered_questions': max(0, total_questions - answered),
                            'score': existing['score'],
                        }
                    }

            correct_count = 0
            wrong_count = 0
            answers_rows = []

            for item in answers:
                qid = int(item.get('question_id'))
                if qid not in correct_ids:
                    continue
                selected = item.get('selected_answer')
                if selected is None:
                    selected = item.get('answer')
                correct_answer = correct_ids.get(qid)
                if selected is None or selected == '':
                    is_correct = 0
                    selected = None
                else:
                    is_correct = 1 if correct_answer == selected else 0
                if is_correct:
                    correct_count += 1
                elif selected is not None:
                    wrong_count += 1
                answers_rows.append((qid, selected, correct_answer, is_correct))

            answered_questions = correct_count + wrong_count
            unanswered_questions = total_questions - answered_questions
            score = round((correct_count / total_questions) * 10, 2) if total_questions else 0
            duration = int(payload.get('duration', 0))
            now = datetime.now().isoformat()

            conn.execute("INSERT INTO attempts (user_id, exam_id, score, correct_answers, wrong_answers, duration, started_at, submitted_at, submission_token) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                         (user_id, exam_id, score, correct_count, wrong_count, duration, now, now, submission_token))
            attempt_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()['id']

            for qid, selected, correct_answer, is_correct in answers_rows:
                conn.execute("INSERT INTO answers (attempt_id, question_id, selected_answer, correct_answer, is_correct) VALUES (?, ?, ?, ?, ?)",
                             (attempt_id, qid, selected, correct_answer, is_correct))

            conn.commit()
            logger.info('[EXAM] submit_success student=%s attempt=%s', user_id, attempt_id)
            logger.info('[EXAM] score=%s student=%s', score, user_id)
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
            logger.exception('[EXAM] submit_error')
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

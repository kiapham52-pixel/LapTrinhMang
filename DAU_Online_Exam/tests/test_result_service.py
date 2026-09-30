import os
import sys
import tempfile
import threading
import tkinter as tk
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import DatabaseManager
from server.services.exam_service import ExamService
from server.services.result_service import ResultService
from server.services.question_service import QuestionService
from server.services.room_service import RoomService
from server.services.subject_service import SubjectService
from client.screens.student_manager import StudentManagementWindow
from client.screens.question_manager import QuestionManagementWindow
from datetime import datetime, timedelta


class ResultServiceSubmitExamTest(unittest.TestCase):
    def test_subject_catalog_migrates_and_validates_duplicates(self):
        db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db').name
        try:
            db = DatabaseManager(db_file)
            db.init_db()
            db.seed_data()
            subjects = SubjectService(db_file)
            catalog = subjects.get_subjects({'role': 'admin'})
            self.assertEqual(catalog['status'], 'success')
            self.assertTrue(catalog['subjects'])
            created = subjects.create_subject({'role': 'admin', 'code': 'QA', 'name': 'QA Test'})
            self.assertEqual(created['status'], 'success')
            duplicate = subjects.create_subject({'role': 'admin', 'code': 'QA', 'name': 'QA Test 2'})
            self.assertEqual(duplicate['status'], 'error')
        finally:
            try:
                os.unlink(db_file)
            except Exception:
                pass

    def test_question_exam_room_student_result_flow(self):
        db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db').name
        try:
            db = DatabaseManager(db_file)
            db.init_db()
            db.seed_data()
            questions = QuestionService(db_file)
            exams = ExamService(db_file)
            rooms = RoomService(db_file)
            results = ResultService(db_file)

            for index in range(5):
                response = questions.create_question({
                    'role': 'admin',
                    'question': {
                        'question_text': f'Flow question {index}',
                        'option_a': 'A', 'option_b': 'B', 'option_c': 'C', 'option_d': 'D',
                        'correct_answer': 'A', 'subject': 'QA Flow', 'difficulty': 'Dễ',
                    },
                })
                self.assertEqual(response['status'], 'success')

            conn = db.connect()
            question_ids = [row['id'] for row in conn.execute(
                'SELECT id FROM questions WHERE subject = ? ORDER BY id', ('QA Flow',)
            ).fetchall()]
            conn.close()
            created = exams.create_exam({'role': 'admin', 'title': 'Flow Exam', 'duration': 30, 'subject': 'QA Flow'})
            exam_id = created['exam_id']
            self.assertEqual(exams.add_questions({'role': 'admin', 'exam_id': exam_id, 'question_ids': question_ids})['added'], 5)
            duplicate = exams.add_questions({'role': 'admin', 'exam_id': exam_id, 'question_ids': question_ids})
            self.assertEqual(duplicate['skipped'], 5)
            self.assertEqual(len(exams.get_exam_questions({'exam_id': exam_id})['questions']), 5)

            start = (datetime.now() + timedelta(days=1)).replace(second=0, microsecond=0)
            room = rooms.create_room({'role': 'admin', 'room': {
                'room_code': 'FLOW_TEST', 'name': 'Flow Test', 'subject': 'QA Flow',
                'exam_id': exam_id, 'duration': 30,
                'start_time': start.strftime('%Y-%m-%d %H:%M'),
                'end_time': (start + timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M'),
                'status': 'DRAFT',
            }})
            self.assertEqual(room['status'], 'success')
            started = exams.start_exam({'role': 'student', 'user_id': 2, 'exam_id': exam_id})
            self.assertEqual(len(started['exam']['questions']), 5)
            submitted = results.submit_exam({
                'role': 'student', 'user_id': 2, 'exam_id': exam_id,
                'answers': [{'question_id': question['id'], 'selected_answer': 'A'} for question in started['exam']['questions']],
                'duration': 10, 'submission_token': 'FLOW_TEST_TOKEN',
            })
            self.assertEqual(submitted['status'], 'success')
            self.assertEqual(submitted['result']['correct_answers'], 5)
            self.assertEqual(results.get_result({'role': 'admin', 'attempt_id': submitted['attempt_id']})['status'], 'success')
            self.assertEqual(results.get_statistics({'role': 'admin'})['status'], 'success')
            self.assertEqual(exams.remove_question({'role': 'admin', 'exam_id': exam_id, 'question_id': question_ids[0]})['status'], 'success')
        finally:
            try:
                os.unlink(db_file)
            except Exception:
                pass

    def test_lifeline_returns_two_options_without_correct_answer(self):
        db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db').name
        try:
            db = DatabaseManager(db_file)
            db.init_db()
            db.seed_data()

            response = ExamService(db_file).use_lifeline({
                'role': 'student',
                'user_id': 2,
                'exam_id': 1,
                'question_id': 1,
            })

            self.assertEqual(response['status'], 'success')
            self.assertEqual(len(response['visible_options']), 2)
            self.assertIn('A', response['visible_options'])
            self.assertNotIn('correct_answer', response)
        finally:
            try:
                os.unlink(db_file)
            except Exception:
                pass

    def test_submit_exam_returns_nested_result_and_counts(self):
        db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db').name
        try:
            db = DatabaseManager(db_file)
            db.init_db()
            db.seed_data()

            service = ResultService(db_file)
            payload = {
                'user_id': 1,
                'exam_id': 1,
                'role': 'student',
                'answers': [
                    {'question_id': 1, 'answer': 'A'},
                    {'question_id': 2, 'answer': 'C'},
                ],
                'duration': 15,
            }

            resp = service.submit_exam(payload)
            self.assertEqual(resp['status'], 'success')
            self.assertEqual(resp['result']['correct_answers'], 1)
            self.assertEqual(resp['result']['wrong_answers'], 1)
            self.assertEqual(resp['result']['unanswered_questions'], 18)
            self.assertIn('score', resp['result'])

        finally:
            try:
                os.unlink(db_file)
            except Exception:
                pass

    def test_dashboard_and_statistics_services_exist_and_roll_up_data(self):
        db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db').name
        try:
            db = DatabaseManager(db_file)
            db.init_db()
            db.seed_data()

            service = ResultService(db_file)
            dashboard = service.get_dashboard_statistics({'role': 'admin'})
            self.assertEqual(dashboard['status'], 'success')
            stats = service.get_statistics({'role': 'admin'})
            self.assertEqual(stats['status'], 'success')

        finally:
            try:
                os.unlink(db_file)
            except Exception:
                pass

    def test_admin_form_panels_clear_previous_form_without_stacking(self):
        class DummyClient:
            def send_request(self, payload):
                return {'status': 'success', 'students': [], 'questions': [], 'subjects': []}

        root = tk.Tk()
        root.withdraw()
        root.client = DummyClient()
        root.current_user = {'role': 'admin', 'id': 1}
        try:
            student_parent = tk.Frame(root)
            student_parent.pack()
            student_window = StudentManagementWindow(student_parent)
            tk.Label(student_window.form_host, text='student form').pack()
            self.assertEqual(len(student_window.form_host.winfo_children()), 1)
            student_window._clear_form_panel()
            self.assertEqual(len(student_window.form_host.winfo_children()), 0)

            question_parent = tk.Frame(root)
            question_parent.pack()
            question_window = QuestionManagementWindow(question_parent)
            tk.Label(question_window.form_host, text='question form').pack()
            self.assertEqual(len(question_window.form_host.winfo_children()), 1)
            question_window._clear_form_panel()
            self.assertEqual(len(question_window.form_host.winfo_children()), 0)
        finally:
            root.destroy()


if __name__ == '__main__':
    unittest.main()

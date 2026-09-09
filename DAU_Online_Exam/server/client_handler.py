import json
import threading
import socket
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.protocol import recv_json, send_json
from server.services.auth_service import AuthService
from server.services.exam_service import ExamService
from server.services.question_service import QuestionService
from server.services.result_service import ResultService


class ClientHandler:
    def __init__(self, client_socket, db_path):
        self.client_socket = client_socket
        self.db_path = db_path
        self.auth_service = AuthService(db_path)
        self.exam_service = ExamService(db_path)
        self.question_service = QuestionService(db_path)
        self.result_service = ResultService(db_path)
        self.lock = threading.Lock()

    def handle(self):
        try:
            while True:
                request = recv_json(self.client_socket)
                if not request:
                    break

                action = request.get('action')
                response = self.dispatch(action, request)
                send_json(self.client_socket, response)

        except socket.timeout:
            send_json(self.client_socket, {'status': 'error', 'message': 'Connection timed out'})
        except ConnectionResetError:
            print('Client disconnected unexpectedly')
        except BrokenPipeError:
            print('Broken pipe while communicating with client')
        except Exception as exc:
            print(f'Handler error: {exc}')
            try:
                send_json(self.client_socket, {'status': 'error', 'message': str(exc)})
            except Exception:
                pass
        finally:
            try:
                self.client_socket.close()
            except Exception:
                pass

    def dispatch(self, action, payload):
        if action == 'login':
            return self.auth_service.login(payload.get('username'), payload.get('password'))

        if action == 'get_exams':
            return self.exam_service.get_exams()

        if action == 'start_exam':
            return self.exam_service.start_exam(payload)

        if action == 'get_my_results':
            return self.result_service.get_history(payload)

        if action == 'get_all_results':
            return self.result_service.get_all_results(payload)

        if action == 'get_questions':
            return self.question_service.get_questions(payload.get('exam_id'), payload)

        if action == 'search_questions':
            return self.question_service.search_questions(payload)

        if action == 'create_question':
            return self.question_service.create_question(payload)

        if action == 'update_question':
            return self.question_service.update_question(payload)

        if action == 'delete_question':
            return self.question_service.delete_question(payload)

        if action == 'get_student_profile':
            return self.auth_service.get_profile(payload.get('user_id'))

        if action == 'submit_exam':
            return self.result_service.submit_exam(payload)

        if action == 'get_result':
            return self.result_service.get_result(payload)

        if action == 'get_history':
            return self.result_service.get_history(payload)

        if action == 'get_students':
            return self.auth_service.get_students(payload)

        if action == 'search_students':
            return self.auth_service.search_students(payload)

        if action == 'create_student':
            return self.auth_service.create_student(payload)

        if action == 'update_student':
            return self.auth_service.update_student(payload)

        if action == 'delete_student':
            return self.auth_service.delete_student(payload)

        if action == 'create_exam':
            return self.exam_service.create_exam(payload)

        if action == 'update_exam':
            return self.exam_service.update_exam(payload)

        if action == 'delete_exam':
            return self.exam_service.delete_exam(payload.get('id'))

        return {'status': 'error', 'message': 'Unknown action'}

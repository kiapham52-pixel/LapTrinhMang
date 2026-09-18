import json
import threading
import socket
import os
import sys
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.protocol import recv_json, send_json
from server.services.auth_service import AuthService
from server.services.exam_service import ExamService
from server.services.question_service import QuestionService
from server.services.result_service import ResultService
from server.services.room_service import RoomService
from server.services.subject_service import SubjectService


logger = logging.getLogger(__name__)


class ClientHandler:
    def __init__(self, client_socket, db_path):
        self.client_socket = client_socket
        self.db_path = db_path
        self.auth_service = AuthService(db_path)
        self.exam_service = ExamService(db_path)
        self.question_service = QuestionService(db_path)
        self.result_service = ResultService(db_path)
        self.room_service = RoomService(db_path)
        self.subject_service = SubjectService(db_path)
        self.lock = threading.Lock()

    def handle(self):
        try:
            while True:
                request = recv_json(self.client_socket)
                if not request:
                    logger.info('[EXAM] connection_lost')
                    break

                action = request.get('action')
                response = self.dispatch(action, request)
                send_json(self.client_socket, response)

        except socket.timeout:
            logger.exception('Client socket timed out')
            try:
                send_json(self.client_socket, {'status': 'error', 'message': 'Connection timed out'})
            except OSError:
                logger.exception('Could not send timeout response')
        except ConnectionResetError:
            logger.info('[EXAM] connection_lost')
        except BrokenPipeError:
            logger.info('[EXAM] connection_lost')
        except Exception as exc:
            logger.exception('Handler error: %s', exc)
            try:
                send_json(self.client_socket, {'status': 'error', 'message': str(exc)})
            except OSError:
                logger.exception('Could not send handler error response')
        finally:
            try:
                self.client_socket.close()
            except OSError:
                logger.exception('Could not close client socket')

    def dispatch(self, action, payload):
        if action == 'login':
            return self.auth_service.login(payload.get('username'), payload.get('password'))

        if action == 'heartbeat':
            return self.auth_service.heartbeat(payload)

        if action == 'logout':
            return self.auth_service.logout(payload)

        if action == 'get_exams':
            return self.exam_service.get_exams()

        if action == 'start_exam':
            return self.exam_service.start_exam(payload)

        if action == 'get_exam_questions':
            return self.exam_service.get_exam_questions(payload)

        if action == 'add_exam_questions':
            return self.exam_service.add_questions(payload)

        if action == 'remove_exam_question':
            return self.exam_service.remove_question(payload)

        if action == 'use_lifeline':
            return self.exam_service.use_lifeline(payload)

        if action == 'get_my_results':
            return self.result_service.get_history(payload)

        if action == 'get_dashboard_statistics':
            return self.result_service.get_dashboard_statistics(payload)

        if action == 'get_statistics':
            return self.result_service.get_statistics(payload)

        if action == 'get_all_results':
            return self.result_service.get_all_results(payload)

        if action == 'get_questions':
            return self.question_service.get_questions(payload.get('exam_id'), payload)

        if action == 'get_subjects':
            return self.subject_service.get_subjects(payload)

        if action == 'create_subject':
            return self.subject_service.create_subject(payload)

        if action == 'update_subject':
            return self.subject_service.update_subject(payload)

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
            return self.exam_service.delete_exam(payload.get('id'), payload.get('role'))

        if action == 'get_rooms':
            return self.room_service.get_rooms(payload)

        if action == 'create_room':
            return self.room_service.create_room(payload)

        if action == 'update_room':
            return self.room_service.update_room(payload)

        if action == 'delete_room':
            return self.room_service.delete_room(payload)

        if action == 'open_room':
            return self.room_service.open_room(payload)

        if action == 'start_room':
            return self.room_service.start_room(payload)

        if action == 'close_room':
            return self.room_service.close_room(payload)

        if action == 'finish_room':
            return self.room_service.finish_room(payload)

        if action == 'get_room_students':
            return self.room_service.get_room_students(payload)

        if action == 'join_room':
            return self.room_service.join_room(payload)

        if action == 'get_online_students':
            return self.room_service.get_online_students(payload)

        return {'status': 'error', 'message': 'Unknown action'}

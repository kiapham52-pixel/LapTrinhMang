import socket
import json
import os
import sys
import threading

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.protocol import send_json, recv_json


class SocketClient:
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.sock = None
        self.request_lock = threading.Lock()

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5)
            self.sock.connect((self.host, self.port))
            return True
        except Exception as exc:
            return False

    def send_request(self, payload):
        with self.request_lock:
            try:
                if not self.sock:
                    return {'status': 'error', 'message': 'Chưa kết nối server'}
                send_json(self.sock, payload)
                response = recv_json(self.sock)
                if response is None:
                    return {'status': 'error', 'message': 'Server đã đóng kết nối'}
                return response
            except Exception as exc:
                return {'status': 'error', 'message': str(exc)}

    def close(self):
        try:
            if self.sock:
                self.sock.close()
        except Exception:
            self.sock = None

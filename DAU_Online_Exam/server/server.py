import socket
import threading
import os
import sys
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.server_config import HOST, PORT, MAX_CONNECTIONS, DB_PATH
from server.client_handler import ClientHandler
from database.database import DatabaseManager


def run_server():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    db = DatabaseManager(DB_PATH)
    db.init_db()
    db.seed_data()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(MAX_CONNECTIONS)
    print(f'Server listening on {HOST}:{PORT}')

    while True:
        try:
            client_socket, address = server_socket.accept()
            client_socket.settimeout(60)
            print(f'Connection accepted: {address}')
            handler = ClientHandler(client_socket, DB_PATH)
            thread = threading.Thread(target=handler.handle, daemon=True)
            thread.start()
        except KeyboardInterrupt:
            print('Server shutdown requested')
            break
        except Exception as exc:
            print(f'Server accept error: {exc}')

    server_socket.close()


if __name__ == '__main__':
    run_server()

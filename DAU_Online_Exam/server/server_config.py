import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT_DIR, 'database', 'exam_system.db')
HOST = '0.0.0.0'
PORT = 5000
MAX_CONNECTIONS = 50
TIMEOUT_SECONDS = 5

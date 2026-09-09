import os
import sys

PROJECT_DIR = os.path.join(os.path.dirname(__file__), 'DAU_Online_Exam')
sys.path.insert(0, PROJECT_DIR)

from server.server import run_server

if __name__ == '__main__':
    run_server()

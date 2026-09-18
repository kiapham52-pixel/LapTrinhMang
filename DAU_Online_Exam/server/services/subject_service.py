import logging

from database.database import DatabaseManager


logger = logging.getLogger(__name__)


class SubjectService:
    def __init__(self, db_path):
        self.db = DatabaseManager(db_path)

    def get_subjects(self, payload=None):
        conn = None
        try:
            conn = self.db.connect()
            rows = conn.execute('''
                SELECT s.id, s.code, s.name, s.description, s.status,
                       COUNT(DISTINCT q.id) AS question_count,
                       COUNT(DISTINCT eq.exam_id) AS exam_count
                FROM subjects s
                LEFT JOIN questions q ON q.subject = s.name
                LEFT JOIN exam_questions eq ON eq.question_id = q.id
                GROUP BY s.id ORDER BY s.name
            ''').fetchall()
            return {'status': 'success', 'success': True, 'subjects': [dict(row) for row in rows]}
        except Exception as exc:
            logger.exception('[SUBJECT ERROR] get_subjects')
            return {'status': 'error', 'success': False, 'message': str(exc)}
        finally:
            if conn is not None:
                conn.close()

    def create_subject(self, payload):
        conn = None
        try:
            if payload.get('role') != 'admin':
                return {'status': 'error', 'success': False, 'message': 'Không có quyền quản lý môn học'}
            code = (payload.get('code') or '').strip().upper()
            name = (payload.get('name') or '').strip()
            if not code or not name:
                return {'status': 'error', 'success': False, 'message': 'Mã môn và tên môn không được để trống'}
            conn = self.db.connect()
            if conn.execute('SELECT 1 FROM subjects WHERE code = ? OR name = ?', (code, name)).fetchone():
                return {'status': 'error', 'success': False, 'message': 'Mã hoặc tên môn đã tồn tại'}
            conn.execute('INSERT INTO subjects (code, name, description, status) VALUES (?, ?, ?, ?)', (code, name, payload.get('description'), payload.get('status') or 'active'))
            conn.commit()
            return {'status': 'success', 'success': True, 'message': 'Đã thêm môn học'}
        except Exception as exc:
            logger.exception('[SUBJECT ERROR] create_subject')
            return {'status': 'error', 'success': False, 'message': 'Không thể lưu môn học'}
        finally:
            if conn is not None:
                conn.close()

    def update_subject(self, payload):
        conn = None
        try:
            if payload.get('role') != 'admin':
                return {'status': 'error', 'success': False, 'message': 'Không có quyền quản lý môn học'}
            subject_id = payload.get('id')
            code = (payload.get('code') or '').strip().upper()
            name = (payload.get('name') or '').strip()
            conn = self.db.connect()
            old = conn.execute('SELECT name FROM subjects WHERE id = ?', (subject_id,)).fetchone()
            if not old:
                return {'status': 'error', 'success': False, 'message': 'Môn học không tồn tại'}
            conn.execute('UPDATE subjects SET code = ?, name = ?, description = ?, status = ? WHERE id = ?', (code, name, payload.get('description'), payload.get('status') or 'active', subject_id))
            if old['name'] != name:
                conn.execute('UPDATE questions SET subject = ? WHERE subject = ?', (name, old['name']))
            conn.commit()
            return {'status': 'success', 'success': True, 'message': 'Đã cập nhật môn học'}
        except Exception as exc:
            logger.exception('[SUBJECT ERROR] update_subject')
            return {'status': 'error', 'success': False, 'message': 'Không thể cập nhật môn học'}
        finally:
            if conn is not None:
                conn.close()
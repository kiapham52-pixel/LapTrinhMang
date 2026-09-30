import tkinter as tk
from tkinter import messagebox
import os
import sys
import threading
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.network.socket_client import SocketClient
from client.screens.student_manager import StudentManagementWindow
from client.screens.question_manager import QuestionManagementWindow
from client.screens.admin_dashboard import AdminDashboardWindow
from client.screens.student_dashboard import StudentDashboard


class ExamClientApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('DAU ONLINE EXAM')
        self.attributes('-fullscreen', True)
        self.resizable(True, True)
        self.configure(bg='#eef3f6')
        self.current_user = None
        self.current_exam = None
        self.client = None
        self.request_lock = threading.Lock()
        self.heartbeat_thread = None
        self.heartbeat_stop = threading.Event()

        self.build_login_screen()

    def build_login_screen(self):
        self.clear_all_widgets()
        self.login_frame = tk.Frame(self, bg='#0f172a')
        self.login_frame.pack(fill='both', expand=True)

        left_panel = tk.Frame(self.login_frame, bg='#111827', padx=54, pady=54)
        left_panel.pack(side='left', fill='y', ipadx=24)
        left_panel.pack_propagate(False)

        brand = tk.Label(left_panel, text='DAU', font=('Arial', 42, 'bold'), fg='#ffffff', bg='#111827')
        brand.pack(anchor='w', pady=(10, 0))
        tk.Label(left_panel, text='ONLINE EXAM', font=('Arial', 14, 'bold'), fg='#fca5a5', bg='#111827').pack(anchor='w', pady=(6, 28))

        tk.Label(left_panel, text='Hệ thống thi trắc nghiệm hiện đại', font=('Arial', 18, 'bold'), fg='#ffffff', bg='#111827').pack(anchor='w')
        tk.Label(left_panel, text='Quản lý kỳ thi, giám sát phòng thi, theo dõi thống kê', font=('Arial', 11), fg='#cbd5e1', bg='#111827', justify='left', wraplength=360).pack(anchor='w', pady=(14, 26))

        feature_box = tk.Frame(left_panel, bg='#1f2937', padx=18, pady=18)
        feature_box.pack(fill='x', pady=(8, 10))
        tk.Label(feature_box, text='• Tối ưu trải nghiệm làm bài', font=('Arial', 11), bg='#1f2937', fg='#e2e8f0').pack(anchor='w', pady=4)
        tk.Label(feature_box, text='• Theo dõi tiến độ và kết quả real-time', font=('Arial', 11), bg='#1f2937', fg='#e2e8f0').pack(anchor='w', pady=4)
        tk.Label(feature_box, text='• Quản trị và thống kê chuyên nghiệp', font=('Arial', 11), bg='#1f2937', fg='#e2e8f0').pack(anchor='w', pady=4)

        right_panel = tk.Frame(self.login_frame, bg='#f8fafc', padx=56, pady=48)
        right_panel.pack(side='left', fill='both', expand=True)

        card = tk.Frame(right_panel, bg='#ffffff', padx=34, pady=34, highlightbackground='#e2e8f0', highlightthickness=1)
        card.pack(expand=True, padx=80, pady=60)

        tk.Label(card, text='Đăng nhập', font=('Arial', 28, 'bold'), fg='#111827', bg='#ffffff').pack(anchor='w')
        tk.Label(card, text='Truy cập hệ thống DAU Online Exam', font=('Arial', 11), fg='#64748b', bg='#ffffff').pack(anchor='w', pady=(5, 22))

        tk.Label(card, text='Username / Mã sinh viên', font=('Arial', 10, 'bold'), fg='#334155', bg='#ffffff').pack(anchor='w')
        self.username_entry = tk.Entry(card, width=40, font=('Arial', 12), bd=1, relief='solid', bg='#f8fafc', fg='#0f172a')
        self.username_entry.pack(fill='x', pady=(6, 14))

        tk.Label(card, text='Mật khẩu', font=('Arial', 10, 'bold'), fg='#334155', bg='#ffffff').pack(anchor='w')
        self.password_frame = tk.Frame(card, bg='#ffffff')
        self.password_frame.pack(fill='x', pady=(6, 14))
        self.password_entry = tk.Entry(self.password_frame, width=34, font=('Arial', 12), show='*', bd=1, relief='solid', bg='#f8fafc', fg='#0f172a')
        self.password_entry.pack(side='left', fill='x', expand=True)
        self.show_pass_btn = tk.Button(self.password_frame, text='Hiện', command=self.toggle_password, width=8, bg='#e2e8f0', fg='#0f172a', relief='flat', font=('Arial', 10, 'bold'))
        self.show_pass_btn.pack(side='right', padx=(8, 0))

        tk.Label(card, text='Server IP', font=('Arial', 10, 'bold'), fg='#334155', bg='#ffffff').pack(anchor='w')
        self.server_ip_entry = tk.Entry(card, width=40, font=('Arial', 12), bd=1, relief='solid', bg='#f8fafc', fg='#0f172a')
        self.server_ip_entry.insert(0, '127.0.0.1')
        self.server_ip_entry.pack(fill='x', pady=(6, 18))

        self.login_btn = tk.Button(card, text='Đăng nhập', command=self.login, bg='#b91c1c', fg='white', padx=18, pady=12, font=('Arial', 11, 'bold'), relief='flat')
        self.login_btn.pack(fill='x')

        self.server_status = tk.Label(card, text='Kết nối: Server chưa chạy', fg='#64748b', bg='#ffffff', font=('Arial', 10))
        self.server_status.pack(pady=(16, 0))

    def clear_all_widgets(self):
        for child in self.winfo_children():
            child.destroy()

    def toggle_password(self):
        if self.password_entry.cget('show') == '*':
            self.password_entry.config(show='')
            self.show_pass_btn.config(text='Ẩn')
        else:
            self.password_entry.config(show='*')
            self.show_pass_btn.config(text='Hiện')

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        server_ip = self.server_ip_entry.get().strip() or '127.0.0.1'

        if not username or not password:
            messagebox.showerror('Lỗi đăng nhập', 'Vui lòng nhập username và password.')
            return

        self.server_status.config(text='Đang kết nối đến Server...')
        self.login_btn.config(state='disabled')

        thread = threading.Thread(target=self.login_worker, args=(username, password, server_ip), daemon=True)
        thread.start()

    def login_worker(self, username, password, server_ip):
        try:
            client = SocketClient(host=server_ip, port=5000)
            if not client.connect():
                self.show_error_on_ui('Không thể kết nối đến Server.\nVui lòng kiểm tra Server đang chạy.')
                return

            response = client.send_request({'action': 'login', 'username': username, 'password': password})
            if response.get('success') is True or response.get('status') == 'success':
                user = response.get('user') or {}
                self.current_user = user
                self.client = client
                self.start_heartbeat()
                self.after(0, self.render_dashboard)
            else:
                message = response.get('message') or 'Sai tài khoản hoặc mật khẩu'
                client.close()
                self.show_error_on_ui(message)
        except Exception as exc:
            self.show_error_on_ui(str(exc))

    def show_error_on_ui(self, message):
        self.after(0, lambda: self.show_login_error(message))

    def show_login_error(self, message):
        self.login_btn.config(state='normal')
        self.server_status.config(text='Kết nối: Server không hợp lệ')
        messagebox.showerror('Lỗi đăng nhập', message)

    def show_dashboard(self):
        if self.client is None:
            return
        self.after(0, self.render_dashboard)

    def is_exam_in_progress(self):
        return bool(getattr(getattr(self, 'student_dashboard', None), 'exam_state', None) == 'IN_PROGRESS')

    def enter_exam_fullscreen(self):
        self.attributes('-fullscreen', True)
        self.resizable(False, False)
        self.update_idletasks()
        self.focus_force()

    def render_dashboard(self):
        self.clear_all_widgets()
        if self.current_user and self.current_user.get('role') == 'admin':
            self.admin_dashboard = AdminDashboardWindow(self)
            self.admin_dashboard.pack(fill='both', expand=True)
            return

        # New professional student dashboard
        self.student_dashboard = StudentDashboard(self, self.current_user, self.client)
        self.student_dashboard.pack(fill='both', expand=True)

    def open_student_manager(self):
        if self.client is None:
            messagebox.showerror('Lỗi', 'Chưa có kết nối server')
            return
        StudentManagementWindow(self)

    def open_question_manager(self):
        if self.client is None:
            messagebox.showerror('Lỗi', 'Chưa có kết nối server')
            return
        QuestionManagementWindow(self)

    def open_exam_manager(self):
        if self.is_exam_in_progress():
            return
        if self.client is None:
            messagebox.showerror('Lỗi', 'Chưa có kết nối server')
            return
        if self.current_user and self.current_user.get('role') == 'admin':
            self.render_dashboard()
        else:
            self.show_exam_list()

    def show_exam_list(self):
        if self.is_exam_in_progress():
            return
        if self.client is None:
            messagebox.showerror('Lỗi', 'Chưa có kết nối server')
            return
        # Do not open a new Toplevel and keep content inside this root application.
        if self.current_user and self.current_user.get('role') == 'student':
            self.render_dashboard()

    def show_results(self):
        if self.is_exam_in_progress():
            return
        if self.client is None:
            messagebox.showerror('Lỗi', 'Chưa có kết nối server')
            return

        role = self.current_user.get('role')
        if role == 'admin':
            response = self.client.send_request({'action': 'get_all_results', 'role': role})
            if response.get('status') == 'success' and response.get('results'):
                results = response.get('results', [])
                lines = []
                for r in results:
                    lines.append(f"{r.get('student_code') or r.get('username') or 'SV'} | {r.get('full_name') or 'Sinh viên'} | {r.get('exam_title') or 'Kỳ thi'} | Điểm: {r.get('score') or 0} | Đúng: {r.get('correct_answers') or 0} | Sai: {r.get('wrong_answers') or 0}")
                messagebox.showinfo('Toàn bộ kết quả thi', '\n'.join(lines))
            elif response.get('status') == 'success':
                messagebox.showinfo('Toàn bộ kết quả thi', 'Chưa có kết quả thi nào.')
            else:
                messagebox.showerror('Lỗi', response.get('message') or 'Không thể lấy toàn bộ kết quả.')
            return

        response = self.client.send_request({'action': 'get_my_results', 'role': role, 'user_id': self.current_user.get('id')})
        if response.get('status') == 'success' and response.get('history'):
            history = response.get('history', [])
            lines = []
            for h in history:
                lines.append(f"{h.get('title') or 'Kỳ thi'} | Tổng: {h.get('total_questions') or h.get('total')} | Đúng: {h.get('correct_answers') or 0} | Sai: {h.get('wrong_answers') or 0} | Bỏ trống: {h.get('unanswered_questions') or 0} | Điểm: {h.get('score') or 0}")
            messagebox.showinfo('Lịch sử thi', '\n'.join(lines))
        elif response.get('status') == 'success':
            messagebox.showinfo('Lịch sử thi', 'Chưa có lịch sử thi.')
        else:
            messagebox.showerror('Lỗi', response.get('message') or 'Không thể lấy kết quả.')

    def show_history(self):
        if self.is_exam_in_progress():
            return
        if self.client is None:
            messagebox.showerror('Lỗi', 'Chưa có kết nối server')
            return
        response = self.client.send_request({'action': 'get_history', 'role': self.current_user.get('role'), 'user_id': self.current_user.get('id')})
        if response.get('status') == 'success':
            history = response.get('history', [])
            msg = '\n'.join([f"{h.get('title')} | Điểm: {h.get('score')} | Câu đúng: {h.get('correct_answers')}" for h in history]) if history else 'Chưa có lịch sử thi.'
            messagebox.showinfo('Lịch sử thi', msg)
        else:
            messagebox.showerror('Lỗi', response.get('message'))

    def show_profile(self):
        if self.is_exam_in_progress():
            return
        user = self.current_user
        messagebox.showinfo('Thông tin cá nhân', f"Mã sinh viên: {user.get('student_code')}\nHọ tên: {user.get('full_name')}\nEmail: {user.get('email', '')}\nLớp: {user.get('class_name', '')}")

    def start_heartbeat(self):
        self.stop_heartbeat()
        self.heartbeat_stop = threading.Event()
        self.heartbeat_thread = threading.Thread(target=self.heartbeat_worker, daemon=True)
        self.heartbeat_thread.start()

    def stop_heartbeat(self):
        if getattr(self, 'heartbeat_stop', None) is not None:
            self.heartbeat_stop.set()

    def heartbeat_worker(self):
        while True:
            if self.heartbeat_stop.is_set() or self.client is None or self.current_user is None:
                break
            try:
                payload = {'action': 'heartbeat', 'user_id': self.current_user.get('id')}
                self.client.send_request(payload)
            except Exception:
                pass
            self.heartbeat_stop.wait(5)

    def logout(self):
        if self.is_exam_in_progress():
            exam_window = getattr(self.student_dashboard, 'exam_window', None)
            if exam_window is not None:
                exam_window.submit_exam(reason='logout', source='logout')
            return
        if self.client and self.current_user:
            try:
                self.client.send_request({'action': 'logout', 'user_id': self.current_user.get('id')})
            except Exception:
                pass
            try:
                self.client.close()
            except Exception:
                pass
        self.stop_heartbeat()
        self.current_user = None
        self.client = None
        self.build_login_screen()


if __name__ == '__main__':
    app = ExamClientApp()
    app.mainloop()

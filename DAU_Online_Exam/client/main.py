import tkinter as tk
from tkinter import messagebox
import os
import sys
import threading

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.network.socket_client import SocketClient
from client.screens.student_manager import StudentManagementWindow
from client.screens.question_manager import QuestionManagementWindow
from client.screens.exam_screen import ExamListWindow


class ExamClientApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('DAU ONLINE EXAM')
        self.geometry('960x680')
        self.configure(bg='#eef3f6')
        self.current_user = None
        self.current_exam = None
        self.client = None
        self.request_lock = threading.Lock()

        self.build_login_screen()

    def build_login_screen(self):
        self.clear_all_widgets()
        self.login_frame = tk.Frame(self, bg='#eef3f6')
        self.login_frame.pack(fill='both', expand=True)

        panel = tk.Frame(self.login_frame, bg='#ffffff', padx=30, pady=30)
        panel.pack(padx=70, pady=50, ipadx=30, ipady=30)

        title = tk.Label(panel, text='DAU ONLINE EXAM', font=('Arial', 26, 'bold'), fg='#102a43', bg='#ffffff')
        title.pack(pady=(0, 8))

        subtitle = tk.Label(panel, text='Hệ thống thi trắc nghiệm trực tuyến', font=('Arial', 12), fg='#58758a', bg='#ffffff')
        subtitle.pack(pady=(0, 25))

        tk.Label(panel, text='Username / Mã sinh viên', font=('Arial', 10, 'bold'), fg='#102a43', bg='#ffffff').pack(anchor='w')
        self.username_entry = tk.Entry(panel, width=40, font=('Arial', 12), bd=1)
        self.username_entry.pack(fill='x', pady=(5, 12))

        tk.Label(panel, text='Password', font=('Arial', 10, 'bold'), fg='#102a43', bg='#ffffff').pack(anchor='w')
        self.password_frame = tk.Frame(panel, bg='#ffffff')
        self.password_frame.pack(fill='x', pady=(5, 12))
        self.password_entry = tk.Entry(self.password_frame, width=34, font=('Arial', 12), show='*', bd=1)
        self.password_entry.pack(side='left', fill='x', expand=True)
        self.show_pass_btn = tk.Button(self.password_frame, text='Hiện', command=self.toggle_password, width=8)
        self.show_pass_btn.pack(side='right', padx=(8, 0))

        tk.Label(panel, text='Server IP', font=('Arial', 10, 'bold'), fg='#102a43', bg='#ffffff').pack(anchor='w')
        self.server_ip_entry = tk.Entry(panel, width=40, font=('Arial', 12), bd=1)
        self.server_ip_entry.insert(0, '127.0.0.1')
        self.server_ip_entry.pack(fill='x', pady=(5, 12))

        self.login_btn = tk.Button(panel, text='Đăng nhập', width=24, command=self.login, bg='#0d6efd', fg='white', padx=14, pady=8, font=('Arial', 11, 'bold'))
        self.login_btn.pack(pady=(10, 8))

        self.server_status = tk.Label(panel, text='Kết nối: Server chưa chạy', fg='#637381', bg='#ffffff', font=('Arial', 10))
        self.server_status.pack(pady=(8, 0))

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

    def render_dashboard(self):
        self.clear_all_widgets()
        self.dashboard = tk.Frame(self, bg='#eef3f6')
        self.dashboard.pack(fill='both', expand=True)

        tk.Label(self.dashboard, text=f'Xin chào, {self.current_user.get("full_name")}', font=('Arial', 22, 'bold'), fg='#102a43', bg='#eef3f6').pack(anchor='w', padx=20, pady=10)
        tk.Label(self.dashboard, text=f'Mã sinh viên: {self.current_user.get("student_code", self.current_user.get("username"))}', font=('Arial', 11), fg='#58758a', bg='#eef3f6').pack(anchor='w', padx=20)
        tk.Label(self.dashboard, text=f'Vai trò: {"Admin" if self.current_user.get("role") == "admin" else "Sinh viên"}', font=('Arial', 11), fg='#58758a', bg='#eef3f6').pack(anchor='w', padx=20)

        if self.current_user.get('role') == 'admin':
            admin_card = tk.Frame(self.dashboard, bg='#ffffff', padx=20, pady=20)
            admin_card.pack(fill='x', padx=20, pady=20)
            tk.Label(admin_card, text='Admin Dashboard', font=('Arial', 16, 'bold'), fg='#102a43', bg='#ffffff').pack(anchor='w')
            tk.Button(admin_card, text='Quản lý sinh viên', command=self.open_student_manager, width=22).pack(side='left', padx=5)
            tk.Button(admin_card, text='Quản lý câu hỏi', command=self.open_question_manager, width=22).pack(side='left', padx=5)
            tk.Button(admin_card, text='Quản lý kỳ thi', command=self.open_exam_manager, width=22).pack(side='left', padx=5)
            tk.Button(admin_card, text='Xem kết quả', command=self.show_results, width=22).pack(side='left', padx=5)
        else:
            student_card = tk.Frame(self.dashboard, bg='#ffffff', padx=20, pady=20)
            student_card.pack(fill='x', padx=20, pady=20)
            tk.Button(student_card, text='📝 Danh sách kỳ thi', command=self.show_exam_list, width=20).pack(side='left', padx=5)
            tk.Button(student_card, text='📊 Kết quả của tôi', command=self.show_results, width=20).pack(side='left', padx=5)
            tk.Button(student_card, text='📚 Lịch sử thi', command=self.show_history, width=20).pack(side='left', padx=5)
            tk.Button(student_card, text='👤 Thông tin cá nhân', command=self.show_profile, width=20).pack(side='left', padx=5)

        tk.Button(self.dashboard, text='🚪 Đăng xuất', command=self.logout, width=20, bg='#d9534f', fg='white').pack(anchor='e', padx=20, pady=20)

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
        if self.client is None:
            messagebox.showerror('Lỗi', 'Chưa có kết nối server')
            return
        ExamListWindow(self)

    def show_exam_list(self):
        if self.client is None:
            messagebox.showerror('Lỗi', 'Chưa có kết nối server')
            return
        ExamListWindow(self)

    def show_results(self):
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
        user = self.current_user
        messagebox.showinfo('Thông tin cá nhân', f"Mã sinh viên: {user.get('student_code')}\nHọ tên: {user.get('full_name')}\nEmail: {user.get('email', '')}\nLớp: {user.get('class_name', '')}")

    def logout(self):
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
        self.current_user = None
        self.client = None
        self.build_login_screen()


if __name__ == '__main__':
    app = ExamClientApp()
    app.mainloop()

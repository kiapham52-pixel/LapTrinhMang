import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from client.screens.room_manager import RoomManagementWindow
from client.screens.student_manager import StudentManagementWindow
from client.screens.question_manager import QuestionManagementWindow
from client.screens.exam_screen import ExamListWindow
from client.screens.subject_manager import SubjectManagementWindow


class AdminDashboardWindow(tk.Frame):
    def __init__(self, app):
        super().__init__(app, bg='#f5f5f5')
        self.app = app
        self.client = app.client
        self.current_user = app.current_user or {}
        self.configure(bg='#f5f5f5')
        self.pack(fill='both', expand=True)
        self.content_panel = None

        self.build_ui()
        self.load_dashboard_data()

    def build_ui(self):
        self.frame = tk.Frame(self, bg='#edf2f7')
        self.frame.pack(fill='both', expand=True)

        self.sidebar = tk.Frame(self.frame, bg='#0f172a', width=255)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)

        logo_frame = tk.Frame(self.sidebar, bg='#0f172a', pady=28)
        logo_frame.pack(fill='x')
        tk.Label(logo_frame, text='DAU', font=('Arial', 32, 'bold'), fg='#ffffff', bg='#0f172a').pack(anchor='center')
        tk.Label(logo_frame, text='ONLINE EXAM', font=('Arial', 12, 'bold'), fg='#fca5a5', bg='#0f172a').pack(anchor='center', pady=(8, 0))

        menu = tk.Frame(self.sidebar, bg='#0f172a')
        menu.pack(fill='x', pady=18)

        dashboard = tk.Button(menu, text='Dashboard', command=self.show_dashboard_content, bg='#1d4ed8', fg='#ffffff', font=('Arial', 11, 'bold'), bd=0, anchor='w', padx=20, pady=12)
        dashboard.pack(fill='x', padx=14, pady=(0, 12))

        tk.Label(menu, text='QUẢN LÝ THI', bg='#0f172a', fg='#cbd5e1', font=('Arial', 10, 'bold'), anchor='w').pack(fill='x', padx=20, pady=(8, 8))
        group_items = [
            ('Môn học', self.open_subject_manager),
            ('Phòng thi', self.open_room_manager),
            ('Giám sát phòng thi', self.open_room_manager),
            ('Đề thi', self.open_exam_manager),
            ('Ngân hàng câu hỏi', self.open_question_manager),
        ]
        for label, cmd in group_items:
            btn = tk.Button(menu, text=label, bg='#0f172a', fg='#e2e8f0', font=('Arial', 10), bd=0, anchor='w', padx=20, pady=10, command=cmd)
            btn.pack(fill='x', padx=14)

        tk.Label(menu, text='NGƯỜI DÙNG', bg='#0f172a', fg='#cbd5e1', font=('Arial', 10, 'bold'), anchor='w').pack(fill='x', padx=20, pady=(16, 8))
        for label, cmd in [('Sinh viên', self.open_student_manager), ('Trạng thái Online', self.open_online_monitor)]:
            btn = tk.Button(menu, text=label, bg='#0f172a', fg='#e2e8f0', font=('Arial', 10), bd=0, anchor='w', padx=20, pady=10, command=cmd)
            btn.pack(fill='x', padx=14)

        tk.Label(menu, text='KẾT QUẢ', bg='#0f172a', fg='#cbd5e1', font=('Arial', 10, 'bold'), anchor='w').pack(fill='x', padx=20, pady=(16, 8))
        btn_result = tk.Button(menu, text='Kết quả thi', bg='#0f172a', fg='#e2e8f0', font=('Arial', 10), bd=0, anchor='w', padx=20, pady=10, command=self.open_results_manager)
        btn_result.pack(fill='x', padx=14)
        btn_stats = tk.Button(menu, text='Thống kê', bg='#0f172a', fg='#e2e8f0', font=('Arial', 10), bd=0, anchor='w', padx=20, pady=10, command=self.open_statistics_manager)
        btn_stats.pack(fill='x', padx=14)

        tk.Label(menu, text='HỆ THỐNG', bg='#0f172a', fg='#cbd5e1', font=('Arial', 10, 'bold'), anchor='w').pack(fill='x', padx=20, pady=(16, 8))
        for label, cmd in [('Cài đặt', None), ('Đăng xuất', self.logout)]:
            btn = tk.Button(menu, text=label, bg='#0f172a', fg='#e2e8f0', font=('Arial', 10), bd=0, anchor='w', padx=20, pady=10, command=cmd if cmd is not None else lambda: None)
            btn.pack(fill='x', padx=14)

        content = tk.Frame(self.frame, bg='#edf2f7')
        content.pack(side='left', fill='both', expand=True)

        topbar = tk.Frame(content, bg='#ffffff', height=72)
        topbar.pack(fill='x')
        topbar.pack_propagate(False)
        tk.Label(topbar, text='Dashboard quản trị', font=('Arial', 18, 'bold'), fg='#0f172a', bg='#ffffff').pack(side='left', padx=24, pady=16)

        right = tk.Frame(topbar, bg='#ffffff')
        right.pack(side='right', fill='y', padx=20)
        tk.Label(right, text='🔔', font=('Arial', 12), bg='#ffffff', fg='#b91c1c').pack(side='left', padx=(0, 12))
        tk.Label(right, text='Administrator', font=('Arial', 12), fg='#111827', bg='#ffffff').pack(side='left', padx=(0, 6))
        tk.Label(right, text='Admin', font=('Arial', 11), fg='#b91c1c', bg='#ffffff').pack(side='left', padx=(0, 6))
        tk.Label(right, text='●', font=('Arial', 16), fg='#16a34a', bg='#ffffff').pack(side='left')

        dashboard_area = tk.Frame(content, bg='#edf2f7', padx=20, pady=20)
        dashboard_area.pack(fill='both', expand=True)
        self.content_panel = dashboard_area

        self.show_dashboard_content(load_data=False)

    def show_dashboard_content(self, load_data=True):
        for child in self.content_panel.winfo_children():
            child.destroy()

        self.dashboard_title = tk.Label(self.content_panel, text='Xin chào, Admin 👋', font=('Arial', 30, 'bold'), fg='#0f172a', bg='#edf2f7')
        self.dashboard_title.pack(anchor='w', pady=(0, 6))
        self.dashboard_subtitle = tk.Label(self.content_panel, text='Chào mừng bạn quay lại hệ thống thi trực tuyến DAU.', font=('Arial', 11), fg='#64748b', bg='#edf2f7')
        self.dashboard_subtitle.pack(anchor='w', pady=(0, 16))

        self.cards = tk.Frame(self.content_panel, bg='#edf2f7')
        self.cards.pack(fill='x', pady=(0, 18))

        self.activity_frame = tk.Frame(self.content_panel, bg='#ffffff', padx=18, pady=18, highlightbackground='#e2e8f0', highlightthickness=1)
        self.activity_frame.pack(fill='x', pady=(0, 0))
        tk.Label(self.activity_frame, text='KỲ THI ĐANG HOẠT ĐỘNG', font=('Arial', 16, 'bold'), bg='#ffffff', fg='#0f172a').pack(anchor='w')
        self.activity_body = tk.Frame(self.activity_frame, bg='#ffffff')
        self.activity_body.pack(fill='x', pady=(12, 0))
        if load_data:
            self.load_dashboard_data()

    def load_dashboard_data(self):
        if self.client is None:
            return
        try:
            response = self.client.send_request({'action': 'get_dashboard_statistics', 'role': self.current_user.get('role')})
            if response.get('status') == 'success':
                stats = response.get('statistics', {})
                self.render_dashboard_cards(stats)
                self.render_activity(response.get('active_rooms', []))
            else:
                self.render_dashboard_cards({})
                self.render_activity([])
                messagebox.showerror('Lỗi dashboard', response.get('message') or 'Không thể tải dữ liệu dashboard.')
        except Exception as exc:
            self.render_dashboard_cards({})
            self.render_activity([])
            messagebox.showerror('Lỗi dashboard', str(exc))

    def render_dashboard_cards(self, stats):
        for child in self.cards.winfo_children():
            child.destroy()
        data = [
            ('👨‍🎓', 'Sinh viên', stats.get('total_students', 0), '#2563eb'),
            ('🟢', 'Online', stats.get('online_students', 0), '#16a34a'),
            ('🚪', 'Phòng thi', stats.get('total_rooms', 0), '#8b5cf6'),
            ('📝', 'Kỳ thi', stats.get('total_exams', 0), '#f59e0b'),
            ('📚', 'Môn học', stats.get('total_subjects', 0), '#ec4899'),
            ('❓', 'Câu hỏi', stats.get('total_questions', 0), '#b91c1c'),
            ('📊', 'Bài đã nộp', stats.get('total_attempts', 0), '#0ea5e9'),
            ('⏱', 'Đang thi', stats.get('active_attempts', 0), '#14b8a6'),
            ('⭐', 'Điểm TB', stats.get('average_score', 0), '#f97316'),
        ]
        for i, (icon, label, value, color) in enumerate(data):
            row = i // 4
            col = i % 4
            card = tk.Frame(self.cards, bg='#ffffff', padx=18, pady=16, highlightbackground='#e2e8f0', highlightthickness=1)
            card.grid(row=row, column=col, padx=8, pady=8, sticky='nsew')
            tk.Label(card, text=icon, font=('Arial', 16), bg='#ffffff', fg=color).pack(anchor='w')
            tk.Label(card, text=str(value), font=('Arial', 22, 'bold'), bg='#ffffff', fg='#0f172a').pack(anchor='w')
            tk.Label(card, text=label, font=('Arial', 10), bg='#ffffff', fg='#64748b').pack(anchor='w')

    def render_activity(self, rooms):
        for child in self.activity_body.winfo_children():
            child.destroy()
        if not rooms:
            tk.Label(self.activity_body, text='Hiện không có kỳ thi đang diễn ra.', bg='#ffffff', fg='#6b7280', font=('Arial', 11)).pack(anchor='w', pady=10)
            return
        columns = ('Kỳ thi', 'Phòng', 'SV', 'Online', 'Đã nộp', 'Thời gian còn lại', 'Trạng thái')
        tree = ttk.Treeview(self.activity_body, columns=columns, show='headings', height=8)
        tree.heading('Kỳ thi', text='Kỳ thi')
        tree.heading('Phòng', text='Phòng')
        tree.heading('SV', text='SV')
        tree.heading('Online', text='Online')
        tree.heading('Đã nộp', text='Đã nộp')
        tree.heading('Thời gian còn lại', text='Thời gian còn lại')
        tree.heading('Trạng thái', text='Trạng thái')
        for c in columns:
            tree.column(c, width=120, anchor='center')
        for r in rooms:
            tree.insert('', 'end', values=(
                r.get('exam_title') or r.get('name') or '-',
                r.get('room_code') or '-',
                str(r.get('students_count') or 0),
                str(r.get('online_count') or 0),
                str(r.get('attempts_count') or 0),
                '-',
                r.get('status') or 'RUNNING',
            ))
        tree.pack(fill='x')

    def open_results_manager(self):
        if self.client is None:
            messagebox.showerror('Lỗi', 'Chưa có kết nối server')
            return
        from client.screens.result_management import ResultManagementScreen
        for child in self.content_panel.winfo_children():
            child.destroy()
        ResultManagementScreen(self.content_panel, self.client, self.current_user)

    def open_statistics_manager(self):
        if self.client is None:
            messagebox.showerror('Lỗi', 'Chưa có kết nối server')
            return
        from client.screens.statistics_screen import StatisticsScreen
        for child in self.content_panel.winfo_children():
            child.destroy()
        StatisticsScreen(self.content_panel, self.client, self.current_user)

    def open_room_manager(self):
        if self.client is None:
            messagebox.showerror('Lỗi', 'Chưa có kết nối server')
            return
        for child in self.content_panel.winfo_children():
            child.destroy()
        RoomManagementWindow(self.content_panel)

    def open_student_manager(self):
        if self.client is None:
            messagebox.showerror('Lỗi', 'Chưa có kết nối server')
            return
        for child in self.content_panel.winfo_children():
            child.destroy()
        StudentManagementWindow(self.content_panel)

    def open_question_manager(self):
        if self.client is None:
            messagebox.showerror('Lỗi', 'Chưa có kết nối server')
            return
        for child in self.content_panel.winfo_children():
            child.destroy()
        QuestionManagementWindow(self.content_panel)

    def open_subject_manager(self):
        if self.client is None:
            messagebox.showerror('Lỗi', 'Chưa có kết nối server')
            return
        for child in self.content_panel.winfo_children():
            child.destroy()
        SubjectManagementWindow(self.content_panel)

    def open_exam_manager(self):
        if self.client is None:
            messagebox.showerror('Lỗi', 'Chưa có kết nối server')
            return
        for child in self.content_panel.winfo_children():
            child.destroy()
        ExamListWindow(self.content_panel)

    def open_online_monitor(self):
        if self.client is None:
            messagebox.showerror('Lỗi', 'Chưa có kết nối server')
            return
        payload = {'action': 'get_online_students', 'role': self.current_user.get('role')}
        try:
            response = self.client.send_request(payload)
            if response.get('status') == 'success':
                students = response.get('students', [])
                lines = []
                for s in students:
                    lines.append(f"{s.get('full_name') or s.get('username')} | {s.get('student_code') or ''} | {s.get('class_name') or ''} | {s.get('session_status') or 'OFFLINE'}")
                messagebox.showinfo('Trạng thái Online', '\n'.join(lines) if lines else 'Chưa có sinh viên.')
            else:
                messagebox.showerror('Lỗi', response.get('message') or 'Không thể lấy danh sách online.')
        except Exception as exc:
            messagebox.showerror('Lỗi mạng', str(exc))

    def logout(self):
        if self.client:
            try:
                self.client.send_request({'action': 'logout', 'user_id': self.current_user.get('id')})
            except Exception:
                pass
        self.app.current_user = None
        self.app.client = None
        self.destroy()
        self.app.build_login_screen()


if __name__ == '__main__':
    pass

    def open_room_manager(self):
        if self.client is None:
            messagebox.showerror('Lỗi', 'Chưa có kết nối server')
            return
        for child in self.content_panel.winfo_children():
            child.destroy()
        RoomManagementWindow(self.content_panel)

    def open_student_manager(self):
        if self.client is None:
            messagebox.showerror('Lỗi', 'Chưa có kết nối server')
            return
        for child in self.content_panel.winfo_children():
            child.destroy()
        StudentManagementWindow(self.content_panel)

    def open_question_manager(self):
        if self.client is None:
            messagebox.showerror('Lỗi', 'Chưa có kết nối server')
            return
        for child in self.content_panel.winfo_children():
            child.destroy()
        QuestionManagementWindow(self.content_panel)

    def open_exam_manager(self):
        if self.client is None:
            messagebox.showerror('Lỗi', 'Chưa có kết nối server')
            return
        for child in self.content_panel.winfo_children():
            child.destroy()
        ExamListWindow(self.content_panel)

    def open_online_monitor(self):
        if self.client is None:
            messagebox.showerror('Lỗi', 'Chưa có kết nối server')
            return
        payload = {'action': 'get_online_students', 'role': self.current_user.get('role')}
        try:
            response = self.client.send_request(payload)
            if response.get('status') == 'success':
                students = response.get('students', [])
                lines = []
                for s in students:
                    lines.append(f"{s.get('full_name') or s.get('username')} | {s.get('student_code') or ''} | {s.get('class_name') or ''} | {s.get('session_status') or 'OFFLINE'}")
                messagebox.showinfo('Trạng thái Online', '\n'.join(lines) if lines else 'Chưa có sinh viên.')
            else:
                messagebox.showerror('Lỗi', response.get('message') or 'Không thể lấy danh sách online.')
        except Exception as exc:
            messagebox.showerror('Lỗi mạng', str(exc))

    def logout(self):
        if self.client:
            try:
                self.client.send_request({'action': 'logout', 'user_id': self.current_user.get('id')})
            except Exception:
                pass
        self.app.current_user = None
        self.app.client = None
        self.destroy()
        self.app.build_login_screen()


if __name__ == '__main__':
    pass

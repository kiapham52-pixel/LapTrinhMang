import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from client.screens.exam_screen import ExamWindow


class StudentDashboard(tk.Frame):
    def __init__(self, app, current_user, client):
        super().__init__(app, bg='#f5f5f5')
        self.app = app
        self.current_user = current_user
        self.client = client
        self.exams = []
        self.history = []
        self.exam_state = 'NOT_STARTED'
        self.exam_window = None
        self.build_ui()
        self.load_data()

    def build_ui(self):
        self.configure(bg='#f5f5f5')
        # Sidebar: only the requested student tabs.
        self.sidebar = tk.Frame(self, bg='#7F1D1D', width=250)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)

        logo = tk.Frame(self.sidebar, bg='#7F1D1D', padx=20, pady=26)
        logo.pack(fill='x')
        tk.Label(logo, text='DAU', font=('Arial', 30, 'bold'), fg='#ffffff', bg='#7F1D1D').pack(anchor='center')
        tk.Label(logo, text='ONLINE EXAM', font=('Arial', 11, 'bold'), fg='#FFD7D7', bg='#7F1D1D').pack(anchor='center', pady=(6, 0))

        menu_frame = tk.Frame(self.sidebar, bg='#7F1D1D')
        menu_frame.pack(fill='x', pady=16)

        menu = [
            ('📝 KỲ THI', 'exam'),
            ('👤 HỒ SƠ', 'profile'),
        ]
        for text, key in menu:
            btn = tk.Button(menu_frame, text=text, bg='#7F1D1D', fg='#ffffff', font=('Arial', 11, 'bold'), bd=0,
                            anchor='w', padx=22, pady=12, width=20,
                            command=lambda k=key: self.menu_action(k))
            btn.pack(fill='x', padx=16, pady=3)

        logout_frame = tk.Frame(self.sidebar, bg='#7F1D1D')
        logout_frame.pack(side='bottom', fill='x', pady=24)
        tk.Button(logout_frame, text='🚪 ĐĂNG XUẤT', command=self.handle_logout, bg='#B91C1C', fg='#ffffff', font=('Arial', 11, 'bold'), bd=0, padx=12, pady=12).pack(fill='x', padx=16)

        # Main content
        self.content = tk.Frame(self, bg='#f5f5f5')
        self.content.pack(side='left', fill='both', expand=True)

        # Topbar
        self.topbar = tk.Frame(self.content, bg='#ffffff', height=72)
        self.topbar.pack(fill='x')
        self.topbar.pack_propagate(False)

        tk.Label(self.topbar, text='🔴 DAU ONLINE EXAM', font=('Arial', 18, 'bold'), fg='#7F1D1D', bg='#ffffff').pack(side='left', padx=26, pady=16)

        top_right = tk.Frame(self.topbar, bg='#ffffff')
        top_right.pack(side='right', fill='y', padx=22)
        self.net_status = tk.Label(self.topbar, text='● Server Online', font=('Arial', 10, 'bold'), bg='#ffffff', fg='#15803d')
        self.net_status.pack(side='right', padx=(0, 20))
        tk.Label(top_right, text='🔔', font=('Arial', 15), bg='#ffffff', fg='#7F1D1D').pack(side='left', padx=(0, 8))
        tk.Label(top_right, text=self.current_user.get('full_name') or 'Sinh viên', font=('Arial', 11, 'bold'), bg='#ffffff', fg='#1f2937').pack(side='left', padx=(0, 4))
        tk.Label(top_right, text=self.current_user.get('student_code') or self.current_user.get('username') or 'SV', font=('Arial', 10), bg='#ffffff', fg='#6b7280').pack(side='left')

        # Dashboard main area
        self.main = tk.Frame(self.content, bg='#f5f5f5', padx=26, pady=24)
        self.main.pack(fill='both', expand=True)

        self.title_label = tk.Label(self.main, text='KỲ THI CỦA TÔI', font=('Arial', 24, 'bold'), bg='#f5f5f5', fg='#1f2937', justify='left')
        self.title_label.pack(anchor='w')

        self.subtitle_label = tk.Label(self.main, text='Các kỳ thi bạn được tham gia', font=('Arial', 11), bg='#f5f5f5', fg='#6b7280')
        self.subtitle_label.pack(anchor='w', pady=(4, 16))

        self.active_frame = tk.Frame(self.main, bg='#ffffff', padx=20, pady=20)
        self.active_frame.pack(fill='x', pady=(0, 16))
        tk.Label(self.active_frame, text='🔴 KỲ THI ĐANG DIỄN RA', font=('Arial', 14, 'bold'), bg='#ffffff', fg='#7F1D1D').pack(anchor='w')
        self.active_content = tk.Frame(self.active_frame, bg='#ffffff')
        self.active_content.pack(fill='x', pady=(10, 0))

        self.upcoming_frame = tk.Frame(self.main, bg='#ffffff', padx=20, pady=18)
        self.upcoming_frame.pack(fill='x', pady=(0, 16))
        tk.Label(self.upcoming_frame, text='KỲ THI SẮP DIỄN RA', font=('Arial', 14, 'bold'), bg='#ffffff', fg='#1f2937').pack(anchor='w')
        self.upcoming_content = tk.Frame(self.upcoming_frame, bg='#ffffff')
        self.upcoming_content.pack(fill='x', pady=(10, 0))

        self.completed_frame = tk.Frame(self.main, bg='#ffffff', padx=20, pady=18)
        self.completed_frame.pack(fill='x')
        tk.Label(self.completed_frame, text='KỲ THI ĐÃ HOÀN THÀNH', font=('Arial', 14, 'bold'), bg='#ffffff', fg='#1f2937').pack(anchor='w')
        self.completed_content = tk.Frame(self.completed_frame, bg='#ffffff')
        self.completed_content.pack(fill='x', pady=(10, 0))

    def menu_action(self, key):
        if self.exam_state == 'IN_PROGRESS' and self.exam_window is not None:
            self.exam_window.submit_exam(reason='navigation_attempt', source=key)
            return
        if key == 'exam':
            self.show_exam_home()
        elif key == 'profile':
            self.show_profile_screen()

    def handle_logout(self):
        if self.exam_state == 'IN_PROGRESS' and self.exam_window is not None:
            self.exam_window.submit_exam(reason='logout', source='logout')
            return
        self.app.logout()

    def show_exam_home(self):
        if self.exam_state == 'IN_PROGRESS':
            return
        self.clear_main_content()
        self.rebuild_exam_layout()
        self.load_data()

    def clear_main_content(self):
        for child in self.main.winfo_children():
            child.destroy()

    def rebuild_exam_layout(self):
        self.title_label = tk.Label(self.main, text='KỲ THI CỦA TÔI', font=('Arial', 24, 'bold'), bg='#f5f5f5', fg='#1f2937', justify='left')
        self.title_label.pack(anchor='w')

        self.subtitle_label = tk.Label(self.main, text='Các kỳ thi bạn được tham gia', font=('Arial', 11), bg='#f5f5f5', fg='#6b7280')
        self.subtitle_label.pack(anchor='w', pady=(4, 16))

        self.active_frame = tk.Frame(self.main, bg='#ffffff', padx=20, pady=20)
        self.active_frame.pack(fill='x', pady=(0, 16))
        tk.Label(self.active_frame, text='🔴 KỲ THI ĐANG DIỄN RA', font=('Arial', 14, 'bold'), bg='#ffffff', fg='#7F1D1D').pack(anchor='w')
        self.active_content = tk.Frame(self.active_frame, bg='#ffffff')
        self.active_content.pack(fill='x', pady=(10, 0))

        self.upcoming_frame = tk.Frame(self.main, bg='#ffffff', padx=20, pady=18)
        self.upcoming_frame.pack(fill='x', pady=(0, 16))
        tk.Label(self.upcoming_frame, text='KỲ THI SẮP DIỄN RA', font=('Arial', 14, 'bold'), bg='#ffffff', fg='#1f2937').pack(anchor='w')
        self.upcoming_content = tk.Frame(self.upcoming_frame, bg='#ffffff')
        self.upcoming_content.pack(fill='x', pady=(10, 0))

        self.completed_frame = tk.Frame(self.main, bg='#ffffff', padx=20, pady=18)
        self.completed_frame.pack(fill='x')
        tk.Label(self.completed_frame, text='KỲ THI ĐÃ HOÀN THÀNH', font=('Arial', 14, 'bold'), bg='#ffffff', fg='#1f2937').pack(anchor='w')
        self.completed_content = tk.Frame(self.completed_frame, bg='#ffffff')
        self.completed_content.pack(fill='x', pady=(10, 0))

    def show_profile_screen(self):
        if self.exam_state == 'IN_PROGRESS':
            return
        self.clear_main_content()
        profile = tk.Frame(self.main, bg='#ffffff', padx=30, pady=30)
        profile.pack(fill='both', expand=True)
        tk.Label(profile, text='HỒ SƠ SINH VIÊN', font=('Arial', 22, 'bold'), bg='#ffffff', fg='#7F1D1D').pack(anchor='w')
        avatar = tk.Label(profile, text='👤', font=('Arial', 48), bg='#ffffff', fg='#7F1D1D')
        avatar.pack(pady=(20, 10))
        user = self.current_user or {}
        tk.Label(profile, text=user.get('full_name') or 'Sinh viên', font=('Arial', 16, 'bold'), bg='#ffffff', fg='#1f2937').pack(anchor='center')
        tk.Label(profile, text=f"Mã sinh viên: {user.get('student_code') or user.get('username') or 'SV'}", bg='#ffffff', fg='#4b5563').pack(anchor='w', pady=(8, 4))
        tk.Label(profile, text=f"Lớp: {user.get('class_name') or '-'}", bg='#ffffff', fg='#4b5563').pack(anchor='w', pady=4)
        tk.Label(profile, text=f"Username: {user.get('username') or '-'}", bg='#ffffff', fg='#4b5563').pack(anchor='w', pady=4)
        tk.Label(profile, text=f"Email: {user.get('email') or '-'}", bg='#ffffff', fg='#4b5563').pack(anchor='w', pady=4)
        btn_row = tk.Frame(profile, bg='#ffffff')
        btn_row.pack(fill='x', pady=(20, 0))
        tk.Button(btn_row, text='CHỈNH SỬA', bg='#7F1D1D', fg='white', width=15, command=lambda: messagebox.showinfo('Thông báo', 'Tính năng chỉnh sửa hồ sơ đang được tích hợp.')).pack(side='left', padx=(0, 8))
        tk.Button(btn_row, text='ĐỔI MẬT KHẨU', bg='#ffffff', fg='#7F1D1D', width=15, borderwidth=1, relief='solid', command=lambda: messagebox.showinfo('Thông báo', 'Tính năng đổi mật khẩu đang được tích hợp.')).pack(side='left')

    def load_data(self):
        # Keep the student dashboard focused on the exam view, as requested.
        # Load exam list and attempt history from the backend service layer.
        response = self.client.send_request({'action': 'get_exams'})
        if response.get('status') == 'success':
            self.exams = response.get('exams', [])
        else:
            self.exams = []

        hist_response = self.client.send_request({'action': 'get_history', 'role': self.current_user.get('role'), 'user_id': self.current_user.get('id')})
        if hist_response.get('status') == 'success':
            self.history = hist_response.get('history', [])
        else:
            self.history = []

        self.render_exam_sections()

    def render_exam_sections(self):
        for child in self.active_content.winfo_children():
            child.destroy()
        for child in self.upcoming_content.winfo_children():
            child.destroy()
        for child in self.completed_content.winfo_children():
            child.destroy()

        # Active exam card from server data
        active_exam = None
        for exam in self.exams:
            if exam.get('status') == 'active':
                active_exam = exam
                break

        if active_exam:
            box = tk.Frame(self.active_content, bg='#fff7f7', highlightbackground='#7F1D1D', highlightthickness=1, padx=16, pady=16)
            box.pack(fill='x', pady=8)
            tk.Label(box, text='🔴 ĐANG DIỄN RA', bg='#fff7f7', fg='#7F1D1D', font=('Arial', 13, 'bold')).pack(anchor='w')
            tk.Label(box, text=(active_exam.get('title') or 'Kỳ thi'), bg='#fff7f7', fg='#1f2937', font=('Arial', 16, 'bold')).pack(anchor='w', pady=(14, 8))
            tk.Label(box, text=f"Phòng thi: {active_exam.get('room_code') or 'PH001'}", bg='#fff7f7', fg='#1f2937').pack(anchor='w')
            meta = tk.Label(box, text=f"{active_exam.get('total_questions') or 0} câu hỏi      {active_exam.get('duration') or 0} phút      10 điểm", bg='#fff7f7', fg='#4b5563')
            meta.pack(anchor='w', pady=(8, 8))
            tk.Label(box, text='Trạng thái: ● Đang mở', bg='#fff7f7', fg='#15803d').pack(anchor='w')
            tk.Button(box, text='🔴 VÀO THI', width=14, bg='#B91C1C', fg='#ffffff', command=lambda e=active_exam: self.open_exam_detail(e), font=('Arial', 11, 'bold')).pack(anchor='e', pady=(12, 0))
        else:
            tk.Label(self.active_content, text='Hiện tại không có kỳ thi đang diễn ra.', bg='#ffffff', fg='#6b7280', font=('Arial', 11)).pack(anchor='w', pady=10)

        # Upcoming exams from server by default.
        if self.exams:
            for exam in self.exams[:3]:
                frame = tk.Frame(self.upcoming_content, bg='#ffffff', highlightbackground='#e5e7eb', highlightthickness=1, padx=14, pady=12)
                frame.pack(fill='x', pady=(0, 8))
                tk.Label(frame, text=exam.get('title') or 'Kỳ thi', bg='#ffffff', fg='#1f2937', font=('Arial', 13, 'bold')).pack(anchor='w')
                tk.Label(frame, text=f"📅 {exam.get('start_time') or 'Chưa xác định'}", bg='#ffffff', fg='#6b7280').pack(anchor='w')
                tk.Label(frame, text=f"⏰ {exam.get('start_time') or '08:00'}", bg='#ffffff', fg='#6b7280').pack(anchor='w')
                meta = tk.Label(frame, text=f"{exam.get('total_questions') or 0} câu • {exam.get('duration') or 0} phút", bg='#ffffff', fg='#6b7280')
                meta.pack(anchor='w')
                tk.Label(frame, text='○ Chưa bắt đầu', bg='#ffffff', fg='#7F1D1D').pack(anchor='w')
                tk.Button(frame, text='XEM CHI TIẾT', width=14, command=lambda e=exam: self.open_exam_detail(e), bg='#7F1D1D', fg='#ffffff').pack(anchor='e')

        # Completed exams from history service, as requested it should be in the same tab.
        if self.history:
            for h in self.history:
                frame = tk.Frame(self.completed_content, bg='#fff', highlightbackground='#e5e7eb', highlightthickness=1, padx=14, pady=12)
                frame.pack(fill='x', pady=(0, 8))
                tk.Label(frame, text=h.get('title') or 'Kỳ thi', bg='#ffffff', fg='#1f2937', font=('Arial', 13, 'bold')).pack(anchor='w')
                tk.Label(frame, text=f"Phòng: {h.get('room_code') or 'PH001'}", bg='#ffffff', fg='#6b7280').pack(anchor='w')
                tk.Label(frame, text='✓ Đã hoàn thành', bg='#ffffff', fg='#15803d').pack(anchor='w')
                tk.Label(frame, text=f"Điểm: {h.get('score') or 0} / 10   Đúng: {h.get('correct_answers') or 0}/{h.get('total_questions') or 0}", bg='#ffffff', fg='#1f2937').pack(anchor='w')
                tk.Button(frame, text='XEM KẾT QUẢ', width=14, command=lambda h_item=h: self.show_result_popup(h_item), bg='#7F1D1D', fg='#ffffff').pack(anchor='e')
        else:
            tk.Label(self.completed_content, text='Chưa có kỳ thi đã hoàn thành.', bg='#ffffff', fg='#6b7280').pack(anchor='w', pady=10)

    def open_exam_list(self):
        self.clear_main_content()
        ExamListWindow(self.main)

    def show_result_popup(self, h_item):
        # Keep the popup within the one-window app and surface the stored result details.
        title = h_item.get('title') or 'Kỳ thi'
        score = h_item.get('score') or 0
        correct = h_item.get('correct_answers') or 0
        wrong = h_item.get('wrong_answers') or 0
        unanswered = h_item.get('unanswered_questions') or 0
        messagebox.showinfo('Kết quả bài thi', f'{title}\nĐiểm: {score} / 10\nĐúng: {correct}\nSai: {wrong}\nBỏ trống: {unanswered}')

    def open_exam_detail(self, exam):
        # Keep the flow inside the student dashboard root content.
        self.clear_main_content()
        ExamConfirmationFrame(self.main, exam, self.current_user, self.client, self)

    def show_history(self):
        # show old messagebox with history table
        payload = {'action': 'get_history', 'role': self.current_user.get('role'), 'user_id': self.current_user.get('id')}
        response = self.client.send_request(payload)
        if response.get('status') == 'success':
            history = response.get('history', [])
            if history:
                lines = []
                for h in history:
                    lines.append(f"{h.get('title')} | Điểm {h.get('score')} | Đúng {h.get('correct_answers')}")
                messagebox.showinfo('Lịch sử thi', '\n'.join(lines))
            else:
                messagebox.showinfo('Lịch sử thi', 'Chưa có lịch sử thi.')
        else:
            messagebox.showerror('Lỗi', response.get('message'))

    def show_results(self):
        payload = {'action': 'get_my_results', 'role': self.current_user.get('role'), 'user_id': self.current_user.get('id')}
        response = self.client.send_request(payload)
        if response.get('status') == 'success' and response.get('history'):
            history = response.get('history', [])
            lines = []
            for h in history:
                lines.append(f"{h.get('title')} | Điểm: {h.get('score')} | Đúng: {h.get('correct_answers')} | Sai: {h.get('wrong_answers')}")
            messagebox.showinfo('Kết quả của tôi', '\n'.join(lines))
        elif response.get('status') == 'success':
            messagebox.showinfo('Kết quả của tôi', 'Chưa có kết quả thi nào.')
        else:
            messagebox.showerror('Lỗi', response.get('message'))

    def show_profile(self):
        user = self.current_user
        messagebox.showinfo('Hồ sơ sinh viên', f"Mã sinh viên: {user.get('student_code')}\nHọ tên: {user.get('full_name')}\nLớp: {user.get('class_name')}\nUsername: {user.get('username')}\nEmail: {user.get('email')}")


class ExamConfirmationFrame(tk.Frame):
    def __init__(self, parent, exam, current_user, client, student_dashboard):
        super().__init__(parent, bg='#ffffff', padx=24, pady=24)
        self.parent = parent
        self.app = parent.winfo_toplevel()
        self.current_user = current_user
        self.client = client
        self.exam = exam
        self.student_dashboard = student_dashboard
        self.pack(fill='both', expand=True)
        self.build_ui()

    def build_ui(self):
        frame = tk.Frame(self, bg='#ffffff', padx=24, pady=24)
        frame.pack(fill='both', expand=True)

        tk.Label(frame, text='← QUAY LẠI', font=('Arial', 11, 'bold'), bg='#ffffff', fg='#7F1D1D', cursor='hand2').pack(anchor='w')
        tk.Label(frame, text='XÁC NHẬN THAM GIA THI', font=('Arial', 20, 'bold'), bg='#ffffff', fg='#7F1D1D').pack(anchor='w', pady=(12, 8))
        tk.Label(frame, text=self.exam.get('title') or 'Kỳ thi', font=('Arial', 16, 'bold'), bg='#ffffff', fg='#1f2937').pack(anchor='w', pady=(0, 8))
        tk.Label(frame, text=f"Phòng thi: {self.exam.get('room_code') or 'PH001'}", bg='#ffffff', fg='#4b5563').pack(anchor='w')
        tk.Label(frame, text=f"Sinh viên: {self.current_user.get('full_name') or 'Sinh viên'}", bg='#ffffff', fg='#4b5563').pack(anchor='w')
        tk.Label(frame, text=f"Mã SV: {self.current_user.get('student_code') or self.current_user.get('username') or 'SV'}", bg='#ffffff', fg='#4b5563').pack(anchor='w')
        tk.Label(frame, text=f"Lớp: {self.current_user.get('class_name') or '-'}", bg='#ffffff', fg='#4b5563').pack(anchor='w')
        tk.Label(frame, text=f"{self.exam.get('total_questions') or 0} câu hỏi", bg='#ffffff', fg='#4b5563').pack(anchor='w', pady=(12, 4))
        tk.Label(frame, text=f"{self.exam.get('duration') or 0} phút", bg='#ffffff', fg='#4b5563').pack(anchor='w')
        tk.Label(frame, text=f"{self.exam.get('score') or 10} điểm", bg='#ffffff', fg='#4b5563').pack(anchor='w')
        tk.Label(frame, text='⚠ Sau khi bắt đầu, thời gian sẽ được tính.\n⚠ Khi hết giờ hệ thống sẽ tự động nộp bài.', bg='#ffffff', fg='#7F1D1D', justify='left', wraplength=480).pack(anchor='w', pady=(20, 16))

        btn_frame = tk.Frame(frame, bg='#ffffff')
        btn_frame.pack(fill='x')
        tk.Button(btn_frame, text='HỦY', command=lambda: self.student_dashboard.show_exam_home(), width=12, bg='#6b7280', fg='white').pack(side='left')
        tk.Button(btn_frame, text='🔴 BẮT ĐẦU THI', command=self.start_exam, width=16, bg='#7F1D1D', fg='white').pack(side='left', padx=(8, 0))

    def start_exam(self):
        payload = {
            'action': 'start_exam',
            'exam_id': self.exam.get('id'),
            'user_id': self.current_user.get('id'),
            'role': self.current_user.get('role'),
        }
        thread = threading.Thread(target=self.start_exam_worker, args=(payload,), daemon=True)
        thread.start()

    def start_exam_worker(self, payload):
        try:
            response = self.client.send_request(payload)
            if response.get('status') == 'success' and response.get('exam'):
                self.student_dashboard.after(0, lambda: self.open_exam_frame(response))
            else:
                self.student_dashboard.after(0, lambda: messagebox.showerror('Lỗi thi', response.get('message') or 'Không thể bắt đầu kỳ thi'))
        except Exception as exc:
            self.student_dashboard.after(0, lambda: messagebox.showerror('Lỗi mạng', str(exc)))

    def open_exam_frame(self, response):
        self.student_dashboard.clear_main_content()
        self.destroy()
        self.student_dashboard.exam_state = 'IN_PROGRESS'
        self.student_dashboard.sidebar.pack_forget()
        self.student_dashboard.topbar.pack_forget()
        self.student_dashboard.main.pack_configure(side='left', fill='both', expand=True)
        exam_window = ExamWindow(self.student_dashboard.main, response.get('exam'), self.current_user, self.client, self.student_dashboard)
        self.student_dashboard.exam_window = exam_window


class ExamListWindow(tk.Frame):
    def __init__(self, parent, app=None, current_user=None, client=None):
        super().__init__(parent, bg='#f5f5f5')
        self.root = parent.winfo_toplevel()
        self.app = app or self.root
        self.client = client or getattr(self.app, 'client', None)
        self.current_user = current_user or getattr(self.app, 'current_user') or {}
        self.exams = []
        self.pack(fill='both', expand=True)
        self.build_ui()
        self.load_exams()

    def build_ui(self):
        main = tk.Frame(self, bg='#f5f5f5', padx=20, pady=20)
        main.pack(fill='both', expand=True)
        title = tk.Label(main, text='KỲ THI CỦA TÔI', font=('Arial', 20, 'bold'), fg='#7F1D1D', bg='#f5f5f5')
        title.pack(anchor='w')
        search = tk.Frame(main, bg='#f5f5f5')
        search.pack(fill='x', pady=12)
        self.search_var = tk.StringVar()
        tk.Entry(search, textvariable=self.search_var, width=40, font=('Arial', 11)).pack(side='left')
        tk.Button(search, text='Tìm kiếm', command=self.load_exams, bg='#7F1D1D', fg='#ffffff').pack(side='left', padx=10)

        canvas = tk.Frame(main, bg='#ffffff', padx=16, pady=16)
        canvas.pack(fill='both', expand=True)
        self.cards = tk.Frame(canvas, bg='#ffffff')
        self.cards.pack(fill='both', expand=True)

    def load_exams(self):
        thread = threading.Thread(target=self.worker, daemon=True)
        thread.start()

    def worker(self):
        try:
            response = self.client.send_request({'action': 'get_exams'})
            self.root.after(0, lambda: self.render(response))
        except Exception as exc:
            self.root.after(0, lambda: messagebox.showerror('Lỗi mạng', str(exc)))

    def render(self, response):
        if response.get('status') != 'success':
            messagebox.showerror('Lỗi', response.get('message') or 'Không lấy được kỳ thi')
            return
        self.exams = response.get('exams', [])
        for child in self.cards.winfo_children():
            child.destroy()
        for exam in self.exams:
            row = tk.Frame(self.cards, bg='#f5f5f5', highlightbackground='#e5e7eb', highlightthickness=1, padx=16, pady=14)
            row.pack(fill='x', pady=8)
            tk.Label(row, text=(exam.get('title') or 'Kỳ thi'), font=('Arial', 14, 'bold'), bg='#f5f5f5', fg='#1f2937').pack(anchor='w')
            tk.Label(row, text=f"{exam.get('duration') or 0} phút • {exam.get('total_questions') or 0} câu • {exam.get('status') or 'active'}", bg='#f5f5f5', fg='#6b7280').pack(anchor='w')
            btn = tk.Button(row, text='🔴 VÀO THI', command=lambda e=exam: self.start_exam(e), bg='#B91C1C', fg='#ffffff')
            btn.pack(anchor='e')

    def start_exam(self, exam):
        payload = {'action': 'start_exam', 'exam_id': exam.get('id'), 'user_id': self.current_user.get('id'), 'role': self.current_user.get('role')}
        thread = threading.Thread(target=self.request_exam_worker, args=(payload,), daemon=True)
        thread.start()

    def request_exam_worker(self, payload):
        try:
            response = self.client.send_request(payload)
            self.root.after(0, lambda: self.open_exam_window(response))
        except Exception as exc:
            self.root.after(0, lambda: messagebox.showerror('Lỗi mạng', str(exc)))

    def open_exam_window(self, response):
        if response.get('status') != 'success' or not response.get('exam'):
            messagebox.showerror('Lỗi thi', response.get('message') or 'Không thể bắt đầu kỳ thi')
            return
        self.destroy()
        ExamWindow(self, response.get('exam'), self.current_user, self.client)

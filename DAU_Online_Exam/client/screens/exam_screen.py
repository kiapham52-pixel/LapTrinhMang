import ctypes
import logging
import os
import sys
import threading
import tkinter as tk
import uuid
from tkinter import messagebox, ttk
from client.screens.admin_ui import module_header, toolbar, primary_button, secondary_button, panel, empty_state, loading_state, configure_tree

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


EXAM_STATES = ('NOT_STARTED', 'IN_PROGRESS', 'SUBMITTING', 'SUBMITTED', 'SHOWING_RESULT', 'EXITING')
logger = logging.getLogger(__name__)


class ExamListWindow(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg='#eef3f6')
        self.app = parent.winfo_toplevel()
        self.client = getattr(self.app, 'client', None)
        self.current_user = getattr(self.app, 'current_user') or {}
        self.exam_rows = []
        self.subjects = []
        self.pack(fill='both', expand=True)
        self.build_ui()
        self.load_exams()
        if self.current_user.get('role') == 'admin':
            threading.Thread(target=self._subjects_worker, daemon=True).start()

    def _subjects_worker(self):
        response = self.client.send_request({'action': 'get_subjects', 'role': 'admin'})
        self.app.after(0, lambda: self.set_subjects(response))

    def set_subjects(self, response):
        if response.get('status') == 'success':
            self.subjects = [subject.get('name') for subject in response.get('subjects', [])]

    def build_ui(self):
        if self.current_user.get('role') == 'admin':
            self.build_admin_ui()
            return
        frame = tk.Frame(self, bg='#eef3f6', padx=20, pady=20)
        frame.pack(fill='both', expand=True)
        header = tk.Frame(frame, bg='#ffffff', padx=20, pady=16)
        header.pack(fill='x')
        tk.Label(header, text='Danh sách môn/kỳ thi', font=('Arial', 20, 'bold'), fg='#102a43', bg='#ffffff').pack(anchor='w')
        panel = tk.Frame(frame, bg='#ffffff', padx=14, pady=14)
        panel.pack(fill='both', expand=True, pady=(12, 0))
        columns = ('id', 'title', 'description', 'subject', 'duration', 'total_questions', 'status')
        headings = {'id': 'ID', 'title': 'Tên kỳ thi', 'description': 'Mô tả', 'subject': 'Môn học', 'duration': 'Thời lượng', 'total_questions': 'Số câu', 'status': 'Trạng thái'}
        widths = {'id': 50, 'title': 180, 'description': 260, 'subject': 180, 'duration': 90, 'total_questions': 90, 'status': 100}
        self.tree = ttk.Treeview(panel, columns=columns, show='headings', height=16)
        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], anchor='center' if column in ('id', 'duration', 'total_questions', 'status') else 'w')
        yscroll = ttk.Scrollbar(panel, orient='vertical', command=self.tree.yview)
        xscroll = ttk.Scrollbar(panel, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.tree.pack(side='left', fill='both', expand=True)
        yscroll.pack(side='right', fill='y')
        xscroll.pack(side='bottom', fill='x')
        btn_frame = tk.Frame(frame, bg='#eef3f6', pady=12)
        btn_frame.pack(fill='x')
        tk.Button(btn_frame, text='Vào thi', command=self.open_selected_exam, width=14, bg='#0d6efd', fg='white').pack(side='left')
        tk.Button(btn_frame, text='Làm mới', command=self.load_exams, width=12).pack(side='left', padx=(8, 0))

    def load_exams(self):
        threading.Thread(target=self.request_exams_worker, daemon=True).start()

    def request_exams_worker(self):
        response = self.client.send_request({'action': 'get_exams'})
        self.app.after(0, lambda: self.render_exams(response))

    def render_exams(self, response):
        if response.get('status') != 'success':
            messagebox.showerror('Lỗi', response.get('message', 'Không lấy được kỳ thi'))
            return
        tree = self.exam_tree if self.current_user.get('role') == 'admin' else self.tree
        for item in tree.get_children():
            tree.delete(item)
        self.exam_rows = response.get('exams', [])
        if self.current_user.get('role') == 'admin':
            for exam in self.exam_rows:
                tree.insert('', 'end', values=(exam.get('id'), exam.get('title'), exam.get('subject') or 'Chưa có môn', exam.get('total_questions') or 0, exam.get('duration') or 0, exam.get('status') or 'active'))
            return
        for exam in self.exam_rows:
            tree.insert('', 'end', values=(exam.get('id'), exam.get('title'), exam.get('description') or '', exam.get('subject') or 'Chưa có môn', exam.get('duration') or 0, exam.get('total_questions') or 0, exam.get('status') or 'active'))

    def open_selected_exam(self):
        if self.current_user.get('role') == 'admin':
            selected = self.exam_tree.selection()
            if not selected:
                messagebox.showwarning('Chưa chọn đề', 'Vui lòng chọn một đề thi.')
                return
            self.current_exam_id = int(self.exam_tree.item(selected[0], 'values')[0])
            self.load_exam_questions()
            return
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning('Chưa chọn kỳ thi', 'Vui lòng chọn một kỳ thi để bắt đầu.')
            return
        exam_id = int(self.tree.item(selected[0], 'values')[0])
        payload = {'action': 'start_exam', 'exam_id': exam_id, 'user_id': self.current_user.get('id'), 'role': self.current_user.get('role')}
        threading.Thread(target=self.start_exam_worker, args=(payload,), daemon=True).start()

    def start_exam_worker(self, payload):
        response = self.client.send_request(payload)
        if response.get('status') == 'success' and response.get('exam'):
            self.app.after(0, lambda: ExamWindow(self.app, response['exam'], self.current_user, self.client))
        else:
            self.app.after(0, lambda: messagebox.showerror('Lỗi thi', response.get('message') or 'Không thể bắt đầu kỳ thi'))

    def build_admin_ui(self):
        frame = tk.Frame(self, bg='#f5f5f5', padx=20, pady=20)
        frame.pack(fill='both', expand=True)
        module_header(frame, '📝', 'QUẢN LÝ ĐỀ THI', 'Xây dựng đề thi từ ngân hàng câu hỏi.')
        bar = toolbar(frame)
        primary_button(bar, '+ Tạo đề thi', self.create_exam).pack(side='left')
        secondary_button(bar, 'Sửa đề', self.edit_exam).pack(side='left', padx=8)
        secondary_button(bar, 'Xóa đề', self.delete_exam).pack(side='left')
        secondary_button(bar, 'Làm mới', self.load_exams).pack(side='left', padx=8)
        primary_button(bar, 'Quản lý câu hỏi', self.open_selected_exam).pack(side='left')
        table_panel = panel(frame, 10)
        table_panel.pack(fill='both', expand=True)
        columns = ('id', 'title', 'subject', 'questions', 'duration', 'status')
        self.exam_tree = ttk.Treeview(table_panel, columns=columns, show='headings', selectmode='browse')
        configure_tree(self.exam_tree)
        for col, text, width in [('id', 'ID', 60), ('title', 'Tên đề', 260), ('subject', 'Môn', 180), ('questions', 'Số câu', 80), ('duration', 'Phút', 80), ('status', 'Trạng thái', 100)]:
            self.exam_tree.heading(col, text=text)
            self.exam_tree.column(col, width=width)
        self.exam_tree.pack(side='left', fill='both', expand=True)
        exam_scroll = ttk.Scrollbar(table_panel, orient='vertical', command=self.exam_tree.yview)
        exam_scroll.pack(side='right', fill='y')
        self.exam_tree.configure(yscrollcommand=exam_scroll.set)
        self.current_exam_id = None
        self.question_panel = tk.Frame(frame, bg='white', padx=12, pady=12)
        self.question_panel.pack(fill='both', expand=True, pady=(12, 0))
        tk.Label(self.question_panel, text='Chọn một đề để xem và thêm câu hỏi từ ngân hàng.', bg='white', fg='#6b7280').pack(anchor='w')

    def create_exam(self):
        for child in self.question_panel.winfo_children():
            child.destroy()
        form = tk.Frame(self.question_panel, bg='white')
        form.pack(fill='x')
        tk.Label(form, text='TẠO ĐỀ THI', font=('Arial', 15, 'bold'), bg='white', fg='#7F1D1D').grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 10))
        fields = {}
        tk.Label(form, text='Môn học', bg='white').grid(row=4, column=0, padx=10, pady=8, sticky='w')
        subject_var = tk.StringVar()
        subject_combo = ttk.Combobox(form, textvariable=subject_var, values=self.subjects, state='readonly', width=38)
        subject_combo.grid(row=4, column=1, padx=10, pady=8)
        if self.subjects:
            subject_combo.current(0)
        for index, (key, label) in enumerate((('title', 'Tên đề'), ('description', 'Mô tả'), ('duration', 'Thời lượng (phút)')), start=1):
            tk.Label(form, text=label, bg='white').grid(row=index, column=0, padx=10, pady=8, sticky='w')
            fields[key] = tk.Entry(form, width=40)
            fields[key].grid(row=index, column=1, padx=10, pady=8)
        fields['duration'].insert(0, '30')
        def save():
            response = self.client.send_request({'action': 'create_exam', 'role': 'admin', 'title': fields['title'].get(), 'description': fields['description'].get(), 'duration': fields['duration'].get(), 'subject': subject_var.get()})
            if response.get('status') == 'success':
                messagebox.showinfo('Thành công', f"Đã tạo đề ID {response.get('exam_id')}")
                for child in self.question_panel.winfo_children():
                    child.destroy()
                self.load_exams()
            else:
                messagebox.showerror('Không thể tạo đề', response.get('message') or 'Lỗi server')
        tk.Button(form, text='Lưu đề', command=save, bg='#7F1D1D', fg='white').grid(row=5, column=1, pady=10, sticky='e')

    def edit_exam(self):
        selected = self.exam_tree.selection()
        if not selected:
            messagebox.showwarning('Chưa chọn đề', 'Vui lòng chọn đề cần sửa.')
            return
        values = self.exam_tree.item(selected[0], 'values')
        for child in self.question_panel.winfo_children():
            child.destroy()
        form = tk.Frame(self.question_panel, bg='white')
        form.pack(fill='x')
        fields = {}
        for index, (key, label, value) in enumerate((('title', 'Tên đề', values[1]), ('description', 'Mô tả', ''), ('duration', 'Thời lượng (phút)', values[4])), start=1):
            tk.Label(form, text=label, bg='white').grid(row=index, column=0, padx=10, pady=8, sticky='w')
            fields[key] = tk.Entry(form, width=40)
            fields[key].insert(0, value)
            fields[key].grid(row=index, column=1, padx=10, pady=8)
        def save():
            response = self.client.send_request({'action': 'update_exam', 'role': 'admin', 'id': int(values[0]), 'title': fields['title'].get(), 'description': fields['description'].get(), 'duration': fields['duration'].get(), 'total_questions': int(values[3]), 'status': values[5]})
            if response.get('status') == 'success':
                self.load_exams()
                self.load_exam_questions()
            else:
                messagebox.showerror('Không thể sửa đề', response.get('message') or 'Lỗi server')
        tk.Button(form, text='Lưu thay đổi', command=save, bg='#7F1D1D', fg='white').grid(row=4, column=1, pady=10, sticky='e')

    def delete_exam(self):
        selected = self.exam_tree.selection()
        if not selected:
            messagebox.showwarning('Chưa chọn đề', 'Vui lòng chọn đề cần xóa.')
            return
        values = self.exam_tree.item(selected[0], 'values')
        if not messagebox.askyesno('Xác nhận', f"Xóa đề '{values[1]}' và các liên kết câu hỏi?"):
            return
        response = self.client.send_request({'action': 'delete_exam', 'role': 'admin', 'id': int(values[0])})
        if response.get('status') == 'success':
            self.current_exam_id = None
            self.load_exams()
            for child in self.question_panel.winfo_children():
                child.destroy()
            tk.Label(self.question_panel, text='Chọn một đề để xem và thêm câu hỏi từ ngân hàng.', bg='white', fg='#6b7280').pack(anchor='w')
        else:
            messagebox.showerror('Không thể xóa đề', response.get('message') or 'Lỗi server')

    def load_exam_questions(self):
        response = self.client.send_request({'action': 'get_exam_questions', 'role': 'admin', 'exam_id': self.current_exam_id})
        if response.get('status') != 'success':
            messagebox.showerror('Lỗi', response.get('message') or 'Không tải được câu hỏi của đề')
            return
        for child in self.question_panel.winfo_children():
            child.destroy()
        exam = next((item for item in self.exam_rows if item.get('id') == self.current_exam_id), {})
        tk.Label(self.question_panel, text=f"Đề: {exam.get('title', '')} | ID: {self.current_exam_id} | Số câu: {len(response.get('questions', []))}", font=('Arial', 14, 'bold'), bg='white', fg='#7F1D1D').pack(anchor='w')
        self.current_questions_tree = ttk.Treeview(self.question_panel, columns=('id', 'content', 'subject', 'difficulty', 'answer'), show='headings', height=6)
        for col, text, width in [('id', 'ID', 50), ('content', 'Nội dung', 360), ('subject', 'Môn', 140), ('difficulty', 'Độ khó', 100), ('answer', 'Đúng', 60)]:
            self.current_questions_tree.heading(col, text=text)
            self.current_questions_tree.column(col, width=width)
        self.current_questions_tree.pack(fill='both', expand=True)
        self.current_exam_questions = response.get('questions', [])
        for question in self.current_exam_questions:
            self.current_questions_tree.insert('', 'end', values=(question.get('id'), question.get('content'), question.get('subject'), question.get('difficulty'), question.get('correct_answer')))
        button_row = tk.Frame(self.question_panel, bg='white')
        button_row.pack(fill='x', pady=8)
        tk.Button(button_row, text='+ Thêm từ ngân hàng', command=self.open_question_picker, bg='#991B1B', fg='white').pack(side='left')
        tk.Button(button_row, text='Xóa khỏi đề', command=self.remove_selected_question, bg='#dc2626', fg='white').pack(side='left', padx=8)

    def open_question_picker(self):
        response = self.client.send_request({'action': 'get_questions', 'role': 'admin'})
        if response.get('status') != 'success':
            messagebox.showerror('Lỗi', response.get('message') or 'Không tải được ngân hàng câu hỏi')
            return
        existing = {question.get('id') for question in getattr(self, 'current_exam_questions', [])}
        exam = next((item for item in self.exam_rows if item.get('id') == self.current_exam_id), {})
        exam_subject = exam.get('subject') or ''
        for child in self.question_panel.winfo_children():
            child.destroy()
        picker = tk.Frame(self.question_panel, bg='white')
        picker.pack(fill='both', expand=True)
        tk.Label(picker, text='THÊM CÂU HỎI TỪ NGÂN HÀNG', font=('Arial', 15, 'bold'), bg='white', fg='#7F1D1D').pack(anchor='w')
        canvas = tk.Canvas(picker, bg='white', highlightthickness=0)
        scroll = ttk.Scrollbar(picker, orient='vertical', command=canvas.yview)
        cards = tk.Frame(canvas, bg='white')
        canvas_window = canvas.create_window((0, 0), window=cards, anchor='nw')
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side='left', fill='both', expand=True, padx=(0, 8), pady=10)
        scroll.pack(side='right', fill='y', pady=10)
        canvas.bind('<MouseWheel>', lambda event: canvas.yview_scroll(-int(event.delta / 120), 'units'))
        canvas.bind('<Prior>', lambda _event: canvas.yview_scroll(-1, 'pages'))
        canvas.bind('<Next>', lambda _event: canvas.yview_scroll(1, 'pages'))
        cards.bind('<Configure>', lambda _event: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>', lambda event: canvas.itemconfigure(canvas_window, width=event.width))
        selected_vars = {}
        for question in response.get('questions', []):
            if question.get('id') not in existing and (not exam_subject or question.get('subject') == exam_subject):
                question_id = question.get('id')
                selected_vars[question_id] = tk.BooleanVar(value=False)
                card = tk.Frame(cards, bg='#fff7f7', padx=14, pady=12, highlightbackground='#e5e7eb', highlightthickness=1)
                card.pack(fill='x', pady=6, padx=4)
                top = tk.Frame(card, bg='#fff7f7')
                top.pack(fill='x')
                tk.Checkbutton(top, text=f"Câu hỏi {question_id}", variable=selected_vars[question_id], bg='#fff7f7', fg='#7F1D1D', font=('Arial', 10, 'bold')).pack(side='left')
                tk.Label(top, text=question.get('difficulty') or 'Chưa phân loại', bg='#dcfce7', fg='#166534', padx=8, pady=2).pack(side='right')
                tk.Label(card, text=question.get('content') or '', bg='#fff7f7', fg='#1f2937', font=('Arial', 11, 'bold'), wraplength=720, justify='left').pack(anchor='w', pady=(8, 5))
                for letter, key in (('A', 'option_a'), ('B', 'option_b'), ('C', 'option_c'), ('D', 'option_d')):
                    tk.Label(card, text=f'{letter}. {question.get(key) or ""}', bg='#fff7f7', fg='#4b5563', wraplength=720, justify='left').pack(anchor='w', padx=24, pady=1)
                tk.Label(card, text=f"✓ Đáp án đúng: {question.get('correct_answer') or '-'}    📚 {question.get('subject') or '-'}", bg='#fff7f7', fg='#15803d', font=('Arial', 9, 'bold')).pack(anchor='w', pady=(7, 0))
        def add_selected():
            ids = [question_id for question_id, variable in selected_vars.items() if variable.get()]
            if not ids:
                messagebox.showwarning('Chưa chọn câu hỏi', 'Vui lòng chọn ít nhất một câu hỏi.')
                return
            result = self.client.send_request({'action': 'add_exam_questions', 'role': 'admin', 'exam_id': self.current_exam_id, 'question_ids': ids})
            if result.get('status') == 'success':
                messagebox.showinfo('Thành công', result.get('message'))
                self.load_exam_questions()
                self.load_exams()
            else:
                messagebox.showerror('Không thể thêm câu hỏi', result.get('message') or 'Lỗi server')
        button_row = tk.Frame(picker, bg='white')
        button_row.pack(fill='x', pady=8)
        tk.Button(button_row, text='Thêm câu hỏi vào đề', command=add_selected, bg='#7F1D1D', fg='white').pack(side='left')
        tk.Button(button_row, text='Hủy', command=self.load_exam_questions).pack(side='left', padx=8)

    def remove_selected_question(self):
        selected = self.current_questions_tree.selection()
        if not selected:
            messagebox.showwarning('Chưa chọn', 'Vui lòng chọn câu hỏi cần xóa khỏi đề.')
            return
        question_id = int(self.current_questions_tree.item(selected[0], 'values')[0])
        response = self.client.send_request({'action': 'remove_exam_question', 'role': 'admin', 'exam_id': self.current_exam_id, 'question_id': question_id})
        if response.get('status') == 'success':
            self.load_exam_questions()
            self.load_exams()
        else:
            messagebox.showerror('Không thể xóa', response.get('message') or 'Lỗi server')


class ExamWindow(tk.Frame):
    def __init__(self, parent, exam, current_user, client, student_dashboard=None):
        super().__init__(parent, bg='#eef3f6')
        self.root = parent.winfo_toplevel()
        self.client = client
        self.current_user = current_user
        self.student_dashboard = student_dashboard
        self.exam = exam
        self.questions = exam.get('questions', [])
        self.current_index = 0
        self.answer_var = tk.StringVar(value='')
        self.question_state = {
            q.get('id'): {'selected_answer': None, 'flagged': False, 'lifeline_used': False, 'visible_options': None}
            for q in self.questions
        }
        self.submission_token = str(uuid.uuid4())
        self.exam_state = 'IN_PROGRESS'
        self.lifeline_remaining = 2
        self.lifeline_request_pending = False
        self.time_left_seconds = int((exam.get('duration') or 0) * 60)
        self.timer_job = None
        self.focus_job = None
        if self.current_user.get('role') == 'student':
            enter_fullscreen = getattr(self.root, 'enter_exam_fullscreen', None)
            if enter_fullscreen:
                enter_fullscreen()
            else:
                self.root.attributes('-fullscreen', True)
                self.root.resizable(False, False)
                self.root.update_idletasks()
        self.build_ui()
        self.root.protocol('WM_DELETE_WINDOW', self.handle_root_close)
        self.root.bind('<Alt-F4>', self.handle_alt_f4)
        self.root.resizable(False, False)
        self.pack(fill='both', expand=True)
        self.bind('<Configure>', self.resize_question_text)
        self.start_timer()
        self.start_focus_monitor()
        self.render_question()

    def build_ui(self):
        frame = tk.Frame(self, bg='#eef3f6', padx=20, pady=20)
        frame.pack(fill='both', expand=True)
        header = tk.Frame(frame, bg='#ffffff', padx=18, pady=14)
        header.pack(fill='x')
        tk.Label(header, text='DAU ONLINE EXAM', font=('Arial', 20, 'bold'), fg='#102a43', bg='#ffffff').pack(anchor='w')
        tk.Label(header, text=self.exam.get('title', ''), font=('Arial', 14, 'bold'), fg='#102a43', bg='#ffffff').pack(anchor='w', pady=(5, 0))
        body = tk.Frame(frame, bg='#eef3f6')
        body.pack(fill='both', expand=True, pady=12)
        left = tk.Frame(body, bg='#ffffff', padx=18, pady=18)
        left.pack(side='left', fill='both', expand=True)
        self.question_no = tk.Label(left, text='', font=('Arial', 14, 'bold'), fg='#102a43', bg='#ffffff')
        self.question_no.pack(anchor='w')
        self.question_text = tk.Label(left, text='', justify='left', wraplength=720, font=('Arial', 14, 'bold'), fg='#102a43', bg='#ffffff')
        self.question_text.pack(anchor='w', pady=(16, 12))
        option_frame = tk.Frame(left, bg='#ffffff')
        option_frame.pack(fill='x')
        self.option_buttons = []
        self.option_labels = []
        for letter in ('A', 'B', 'C', 'D'):
            row = tk.Frame(option_frame, bg='#ffffff')
            row.pack(anchor='w', fill='x', pady=4)
            button = tk.Radiobutton(row, text='', variable=self.answer_var, value=letter, bg='#ffffff', fg='#102a43', font=('Arial', 11), command=self.save_current_answer)
            button.pack(side='left')
            label = tk.Label(row, text='', bg='#ffffff', fg='#58758a', font=('Arial', 11), wraplength=680, justify='left')
            label.pack(side='left', padx=(10, 0), anchor='w')
            self.option_buttons.append(button)
            self.option_labels.append(label)
        nav = tk.Frame(left, bg='#ffffff')
        nav.pack(fill='x', pady=14)
        tk.Button(nav, text='Câu trước', command=self.prev_question, width=14, bg='#7F1D1D', fg='white').pack(side='left', padx=(0, 8))
        self.flag_button = tk.Button(nav, text='[!] Phân vân', command=self.toggle_flag, width=14, bg='#ffffff', fg='#7F1D1D', relief='solid', borderwidth=1)
        self.flag_button.pack(side='left', padx=(0, 8))
        self.lifeline_button = tk.Button(nav, text='[+] Giảm áp lực', command=self.use_lifeline, width=16, bg='#fff7ed', fg='#9a3412', relief='solid', borderwidth=1)
        self.lifeline_button.pack(side='left', padx=(0, 8))
        tk.Button(nav, text='Câu tiếp', command=self.next_question, width=14, bg='#7F1D1D', fg='white').pack(side='left', padx=(0, 8))
        self.submit_button = tk.Button(nav, text='Nộp bài', command=self.submit_exam, width=12, bg='#dc3545', fg='white')
        self.submit_button.pack(side='left')
        right = tk.Frame(body, bg='#ffffff', padx=14, pady=14)
        right.pack(side='right', fill='y')
        self.timer_label = tk.Label(right, text='Thời gian: 00:00', font=('Arial', 12, 'bold'), bg='#ffffff', fg='#7F1D1D')
        self.timer_label.pack(anchor='w', pady=(0, 12))
        tk.Label(right, text='Danh sách câu', font=('Arial', 13, 'bold'), bg='#ffffff').pack(anchor='w')
        self.q_grid = tk.Frame(right, bg='#ffffff')
        self.q_grid.pack(fill='both', expand=True)
        self.nav_buttons = []
        for index in range(len(self.questions)):
            button = tk.Button(self.q_grid, text=str(index + 1), width=4, command=lambda idx=index: self.jump_to(idx))
            button.grid(row=index // 8, column=index % 8, padx=4, pady=4)
            self.nav_buttons.append(button)

    def render_question(self):
        question = self.questions[self.current_index]
        qid = question.get('id')
        state = self.question_state[qid]
        self.question_no.config(text=f'Câu {self.current_index + 1} / {len(self.questions)}')
        self.question_text.config(text=question.get('question_text') or question.get('content') or '')
        state_options = state.get('visible_options')
        for letter, button, label, key in zip(('A', 'B', 'C', 'D'), self.option_buttons, self.option_labels, ('option_a', 'option_b', 'option_c', 'option_d')):
            visible = state_options is None or letter in state_options
            button.config(state='normal' if visible else 'disabled')
            label.config(text=(f'{letter}. {question.get(key) or ""}' if visible else ''))
        self.answer_var.set(state.get('selected_answer') or '')
        self.update_flag_button(qid)
        self.update_lifeline_button(qid)
        self.refresh_grid_colors()

    def resize_question_text(self, _event=None):
        if not hasattr(self, 'question_text'):
            return
        available_width = max(480, self.winfo_width() - 430)
        self.question_text.config(wraplength=available_width)
        for label in getattr(self, 'option_labels', []):
            label.config(wraplength=max(420, available_width - 40))

    def save_current_answer(self):
        if self.exam_state != 'IN_PROGRESS':
            return
        qid = self.questions[self.current_index].get('id')
        self.question_state[qid]['selected_answer'] = self.answer_var.get() or None
        self.refresh_grid_colors()

    def update_flag_button(self, qid):
        flagged = self.question_state[qid].get('flagged')
        self.flag_button.config(text='[!] Đã đánh dấu' if flagged else '[!] Phân vân', bg='#7F1D1D' if flagged else '#ffffff', fg='white' if flagged else '#7F1D1D')

    def update_lifeline_button(self, qid):
        state = self.question_state[qid]
        if self.lifeline_request_pending:
            self.lifeline_button.config(text='[+] Đang xử lý...', state='disabled')
        elif self.lifeline_remaining <= 0:
            self.lifeline_button.config(text='[+] Đã hết lượt', state='disabled')
        elif state.get('lifeline_used'):
            self.lifeline_button.config(text=f'[+] Còn {self.lifeline_remaining} lượt', state='disabled')
        else:
            self.lifeline_button.config(text=f'[+] Giảm áp lực ({self.lifeline_remaining})', state='normal')

    def use_lifeline(self):
        if self.exam_state != 'IN_PROGRESS':
            return
        question = self.questions[self.current_index]
        qid = question.get('id')
        state = self.question_state[qid]
        if self.lifeline_remaining <= 0 or state.get('lifeline_used') or self.lifeline_request_pending:
            return
        self.lifeline_request_pending = True
        self.lifeline_button.config(state='disabled', text='Đang xử lý...')
        payload = {'action': 'use_lifeline', 'exam_id': self.exam.get('id'), 'question_id': qid, 'user_id': self.current_user.get('id'), 'role': self.current_user.get('role')}
        threading.Thread(target=self.lifeline_worker, args=(payload, qid), daemon=True).start()

    def lifeline_worker(self, payload, qid):
        response = self.client.send_request(payload)
        self.root.after(0, lambda: self.handle_lifeline_response(response, qid))

    def handle_lifeline_response(self, response, qid):
        if self.exam_state != 'IN_PROGRESS':
            return
        if response.get('status') != 'success':
            self.lifeline_request_pending = False
            messagebox.showerror('Không thể dùng hỗ trợ', response.get('message') or 'Server không trả về hỗ trợ.')
            self.update_lifeline_button(qid)
            return
        state = self.question_state[qid]
        self.lifeline_request_pending = False
        self.lifeline_remaining -= 1
        state['lifeline_used'] = True
        state['visible_options'] = response.get('visible_options') or []
        self.render_question()

    def toggle_flag(self):
        if self.exam_state != 'IN_PROGRESS':
            return
        qid = self.questions[self.current_index].get('id')
        self.question_state[qid]['flagged'] = not self.question_state[qid].get('flagged', False)
        self.update_flag_button(qid)
        self.refresh_grid_colors()

    def refresh_grid_colors(self):
        for index, button in enumerate(self.nav_buttons):
            state = self.question_state[self.questions[index].get('id')]
            if index == self.current_index:
                button.config(bg='#0d6efd', fg='white')
            elif state.get('flagged'):
                button.config(bg='#ffc107', fg='#1f2937')
            elif state.get('selected_answer'):
                button.config(bg='#198754', fg='white')
            else:
                button.config(bg='#ffffff', fg='#102a43')

    def prev_question(self):
        if self.exam_state == 'IN_PROGRESS' and self.current_index > 0:
            self.save_current_answer()
            self.current_index -= 1
            self.render_question()

    def next_question(self):
        if self.exam_state == 'IN_PROGRESS' and self.current_index < len(self.questions) - 1:
            self.save_current_answer()
            self.current_index += 1
            self.render_question()

    def jump_to(self, index):
        if self.exam_state == 'IN_PROGRESS':
            self.save_current_answer()
            self.current_index = index
            self.render_question()

    def start_timer(self):
        self.timer_job = self.root.after(1000, self.tick_timer)

    def tick_timer(self):
        if self.exam_state != 'IN_PROGRESS':
            return
        self.time_left_seconds = max(0, self.time_left_seconds - 1)
        minutes, seconds = divmod(self.time_left_seconds, 60)
        self.timer_label.config(text=f'Thời gian: {minutes:02d}:{seconds:02d}')
        if self.time_left_seconds == 0:
            self.submit_exam(reason='timeout', source='timer')
        else:
            self.timer_job = self.root.after(1000, self.tick_timer)

    def start_focus_monitor(self):
        self.focus_job = self.root.after(500, self.check_foreground)

    def check_foreground(self):
        if self.exam_state != 'IN_PROGRESS':
            return
        if self._is_foreground_lost():
            self.submit_exam(reason='focus_lost', source='focus_monitor')
            return
        self.focus_job = self.root.after(500, self.check_foreground)

    def _is_foreground_lost(self):
        try:
            if sys.platform == 'win32':
                user32 = ctypes.windll.user32
                foreground = user32.GetForegroundWindow()
                root_hwnd = user32.GetAncestor(self.root.winfo_id(), 2)
                return foreground != root_hwnd
            return self.root.focus_displayof() is None
        except (AttributeError, tk.TclError, OSError):
            return False

    def submit_exam(self, quiet=False, reason='manual', source='manual'):
        if self.exam_state != 'IN_PROGRESS':
            return False
        self.exam_state = 'SUBMITTING'
        self.submit_button.config(state='disabled')
        if self.timer_job:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None
        if self.focus_job:
            self.root.after_cancel(self.focus_job)
            self.focus_job = None
        payload = {
            'action': 'submit_exam',
            'exam_id': self.exam.get('id'),
            'user_id': self.current_user.get('id'),
            'role': self.current_user.get('role'),
            'answers': [{'question_id': q.get('id'), 'selected_answer': self.question_state[q.get('id')].get('selected_answer')} for q in self.questions],
            'duration': int(self.exam.get('duration') or 0) * 60 - self.time_left_seconds,
            'source': source,
            'reason': reason,
            'submission_token': self.submission_token,
        }
        threading.Thread(target=self.submit_worker, args=(payload,), daemon=True).start()
        return True

    def submit_worker(self, payload):
        try:
            response = self.client.send_request(payload)
        except Exception as exc:
            logger.exception('[EXAM] submit_request_failed')
            response = {'status': 'error', 'message': str(exc)}
        self.root.after(0, lambda: self.handle_submit_response(response, payload.get('reason')))

    def handle_submit_response(self, response, reason):
        if self.exam_state != 'SUBMITTING':
            return
        if response.get('status') == 'success':
            self.exam_state = 'SUBMITTED'
            self.render_result_panel(response.get('result') or response, reason)
        else:
            self.render_submit_error(response.get('message') or 'Không thể nộp bài')

    def render_result_panel(self, result, reason):
        self.exam_state = 'SHOWING_RESULT'
        for child in self.winfo_children():
            child.destroy()
        title = 'BÀI THI ĐÃ ĐƯỢC NỘP' if reason == 'focus_lost' else 'HOÀN THÀNH BÀI THI'
        reason_text = 'Lý do: Rời khỏi màn hình thi' if reason == 'focus_lost' else 'Trạng thái: Đã nộp bài'
        frame = tk.Frame(self, bg='#ffffff', padx=30, pady=30)
        frame.pack(fill='both', expand=True)
        tk.Label(frame, text=title, font=('Arial', 22, 'bold'), fg='#102a43', bg='#ffffff').pack(pady=(20, 16))
        tk.Label(frame, text=reason_text, font=('Arial', 13), fg='#7F1D1D', bg='#ffffff').pack(anchor='w', pady=5)
        tk.Label(frame, text=f"Điểm: {result.get('score', 0)} / 10", font=('Arial', 18, 'bold'), fg='#0d6efd', bg='#ffffff').pack(anchor='w', pady=12)
        tk.Label(frame, text=f"Đúng: {result.get('correct_answers', 0)}    Sai: {result.get('wrong_answers', 0)}    Bỏ trống: {result.get('unanswered_questions', 0)}", font=('Arial', 12), bg='#ffffff').pack(anchor='w')
        self.root.after(4000, self.safe_close_application)

    def render_submit_error(self, message):
        self.exam_state = 'EXITING'
        for child in self.winfo_children():
            child.destroy()
        frame = tk.Frame(self, bg='#ffffff', padx=30, pady=30)
        frame.pack(fill='both', expand=True)
        tk.Label(frame, text='KHÔNG THỂ NỘP BÀI', font=('Arial', 22, 'bold'), fg='#7F1D1D', bg='#ffffff').pack(pady=20)
        tk.Label(frame, text=message, font=('Arial', 12), bg='#ffffff', wraplength=600).pack()
        self.root.after(4000, self.safe_close_application)

    def handle_alt_f4(self, _event=None):
        self.handle_root_close()
        return 'break'

    def handle_root_close(self):
        if self.exam_state == 'IN_PROGRESS':
            self.submit_exam(reason='close_window', source='window_close')
        elif self.exam_state not in ('SUBMITTING', 'SHOWING_RESULT'):
            self.safe_close_application()

    def safe_close_application(self):
        self.exam_state = 'EXITING'
        try:
            self.client.close()
        except Exception as exc:
            logger.exception('[EXAM] client_close_failed: %s', exc)
        self.root.destroy()
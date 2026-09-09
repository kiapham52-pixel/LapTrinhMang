import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class ExamListWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.client = app.client
        self.current_user = app.current_user or {}
        self.title('Danh sách môn/kỳ thi')
        self.geometry('900x520')
        self.configure(bg='#eef3f6')
        self.exam_rows = []

        self.build_ui()
        self.load_exams()

    def build_ui(self):
        frame = tk.Frame(self, bg='#eef3f6', padx=20, pady=20)
        frame.pack(fill='both', expand=True)

        header = tk.Frame(frame, bg='#ffffff', padx=20, pady=16)
        header.pack(fill='x')
        tk.Label(header, text='Danh sách môn/kỳ thi', font=('Arial', 20, 'bold'), fg='#102a43', bg='#ffffff').pack(anchor='w')

        panel = tk.Frame(frame, bg='#ffffff', padx=14, pady=14)
        panel.pack(fill='both', expand=True, pady=(12, 0))

        columns = ('id', 'title', 'description', 'subject', 'duration', 'total_questions', 'status')
        self.tree = ttk.Treeview(panel, columns=columns, show='headings', height=16)
        self.tree.heading('id', text='ID')
        self.tree.heading('title', text='Tên kỳ thi')
        self.tree.heading('description', text='Mô tả')
        self.tree.heading('subject', text='Môn học')
        self.tree.heading('duration', text='Thời lượng')
        self.tree.heading('total_questions', text='Số câu')
        self.tree.heading('status', text='Trạng thái')

        self.tree.column('id', width=50, anchor='center')
        self.tree.column('title', width=180)
        self.tree.column('description', width=260)
        self.tree.column('subject', width=180)
        self.tree.column('duration', width=90, anchor='center')
        self.tree.column('total_questions', width=90, anchor='center')
        self.tree.column('status', width=100, anchor='center')

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
        payload = {'action': 'get_exams'}
        thread = threading.Thread(target=self.request_exams_worker, args=(payload,), daemon=True)
        thread.start()

    def request_exams_worker(self, payload):
        try:
            response = self.client.send_request(payload)
            self.app.after(0, lambda: self.render_exams(response))
        except Exception as exc:
            self.app.after(0, lambda: messagebox.showerror('Lỗi mạng', str(exc)))

    def render_exams(self, response):
        if response.get('status') != 'success':
            messagebox.showerror('Lỗi', response.get('message', 'Không lấy được kỳ thi'))
            return
        exams = response.get('exams', [])
        for item in self.tree.get_children():
            self.tree.delete(item)
        for exam in exams:
            self.tree.insert('', 'end', values=(
                exam.get('id'),
                exam.get('title'),
                exam.get('description') or '',
                exam.get('subject') or 'Chưa có môn',
                exam.get('duration') or 0,
                exam.get('total_questions') or 0,
                exam.get('status') or 'active',
            ))
        self.exam_rows = exams

    def open_selected_exam(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning('Chưa chọn kỳ thi', 'Vui lòng chọn một kỳ thi để bắt đầu.')
            return
        values = self.tree.item(selected[0], 'values')
        exam_id = int(values[0])
        payload = {'action': 'start_exam', 'exam_id': exam_id, 'user_id': self.current_user.get('id'), 'role': self.current_user.get('role')}
        thread = threading.Thread(target=self.start_exam_worker, args=(payload,), daemon=True)
        thread.start()

    def start_exam_worker(self, payload):
        try:
            response = self.client.send_request(payload)
            if response.get('status') == 'success' and response.get('exam'):
                self.app.after(0, lambda: ExamWindow(self.app, response.get('exam'), self.current_user, self.client))
            else:
                self.app.after(0, lambda: messagebox.showerror('Lỗi thi', response.get('message') or 'Không thể bắt đầu kỳ thi'))
        except Exception as exc:
            self.app.after(0, lambda: messagebox.showerror('Lỗi mạng', str(exc)))


class ExamWindow(tk.Toplevel):
    def __init__(self, app, exam, current_user, client):
        super().__init__(app)
        self.app = app
        self.client = client
        self.current_user = current_user
        self.exam = exam
        self.questions = exam.get('questions', [])
        self.answers = {}
        self.current_index = 0
        self.answer_var = tk.StringVar(value='')
        self.title('Thi trắc nghiệm - ' + exam.get('title', ''))
        self.geometry('1100x680')
        self.configure(bg='#eef3f6')

        self.build_ui()
        self.render_question()

    def build_ui(self):
        self.frame = tk.Frame(self, bg='#eef3f6', padx=20, pady=20)
        self.frame.pack(fill='both', expand=True)

        top = tk.Frame(self.frame, bg='#ffffff', padx=14, pady=14)
        top.pack(fill='x')
        tk.Label(top, text='THI TRẮC NGHIỆM - ' + self.exam.get('title', ''), font=('Arial', 20, 'bold'), fg='#102a43', bg='#ffffff').pack(anchor='w')
        tk.Label(top, text='Môn: ' + (self.exam.get('subject') or self.exam.get('title') or 'Kỳ thi'), font=('Arial', 12), fg='#58758a', bg='#ffffff').pack(anchor='w')
        tk.Label(top, text='Thời gian: ' + str(self.exam.get('duration') or 0) + ' phút', font=('Arial', 12), fg='#58758a', bg='#ffffff').pack(anchor='w')

        body = tk.Frame(self.frame, bg='#eef3f6')
        body.pack(fill='both', expand=True, pady=12)

        left = tk.Frame(body, bg='#ffffff', padx=18, pady=18)
        left.pack(side='left', fill='both', expand=True)

        self.question_no = tk.Label(left, text='Câu 1 / ' + str(len(self.questions)), font=('Arial', 14, 'bold'), fg='#102a43', bg='#ffffff')
        self.question_no.pack(anchor='w')

        self.question_text = tk.Label(left, text='', justify='left', wraplength=720, font=('Arial', 14, 'bold'), fg='#102a43', bg='#ffffff')
        self.question_text.pack(anchor='w', pady=(16, 12))

        option_frame = tk.Frame(left, bg='#ffffff')
        option_frame.pack(fill='x')

        self.option_rows = []
        self.option_labels = []
        self.option_buttons = []
        for letter in ('A', 'B', 'C', 'D'):
            row = tk.Frame(option_frame, bg='#ffffff')
            row.pack(anchor='w', fill='x', pady=4)
            btn = tk.Radiobutton(row, text='', variable=self.answer_var, value=letter, bg='#ffffff', fg='#102a43', font=('Arial', 11), command=self.save_current_answer)
            btn.pack(side='left')
            label = tk.Label(row, text='', bg='#ffffff', fg='#58758a', font=('Arial', 11), wraplength=680, justify='left')
            label.pack(side='left', padx=(10, 0), anchor='w')
            self.option_rows.append(row)
            self.option_buttons.append(btn)
            self.option_labels.append(label)

        nav = tk.Frame(left, bg='#ffffff')
        nav.pack(fill='x', pady=14)
        tk.Button(nav, text='Câu trước', command=self.prev_question, width=12).pack(side='left', padx=(0, 8))
        tk.Button(nav, text='Câu tiếp', command=self.next_question, width=12).pack(side='left', padx=(0, 8))
        tk.Button(nav, text='Nộp bài', command=self.submit_exam, width=12, bg='#dc3545', fg='white').pack(side='left')

        right = tk.Frame(body, bg='#ffffff', padx=14, pady=14)
        right.pack(side='right', fill='y')
        tk.Label(right, text='Danh sách câu', font=('Arial', 13, 'bold'), bg='#ffffff').pack(anchor='w')
        self.q_grid = tk.Frame(right, bg='#ffffff')
        self.q_grid.pack(fill='both', expand=True)

        # dynamic grid of numbered buttons
        self.nav_buttons = []
        for i in range(len(self.questions)):
            btn = tk.Button(self.q_grid, text=str(i+1), width=4, command=lambda idx=i: self.jump_to(idx))
            btn.grid(row=i//8, column=i%8, padx=4, pady=4)
            self.nav_buttons.append(btn)

    def render_question(self):
        q = self.questions[self.current_index]
        qid = q.get('id')
        self.question_no.config(text='Câu ' + str(self.current_index + 1) + ' / ' + str(len(self.questions)))
        self.question_text.config(text=q.get('question_text') or q.get('content') or '')

        option_texts = [
            q.get('option_a') or '',
            q.get('option_b') or '',
            q.get('option_c') or '',
            q.get('option_d') or '',
        ]
        for label, text in zip(self.option_labels, option_texts):
            label.config(text=text)

        current_selected = self.answers.get(qid, '')
        if current_selected:
            self.answer_var.set(current_selected)
        else:
            self.answer_var.set('')
        self.refresh_grid_colors()

    def save_current_answer(self):
        qid = self.questions[self.current_index].get('id')
        selected = self.answer_var.get()
        if selected:
            self.answers[qid] = selected
        else:
            self.answers.pop(qid, None)
        self.refresh_grid_colors()

    def refresh_grid_colors(self):
        for i, btn in enumerate(self.nav_buttons):
            qid = self.questions[i].get('id')
            if i == self.current_index:
                btn.config(bg='#0d6efd', fg='white')
            elif qid in self.answers:
                btn.config(bg='#198754', fg='white')
            else:
                btn.config(bg='#ffffff', fg='#102a43')

    def prev_question(self):
        self.save_current_answer()
        if self.current_index > 0:
            self.current_index -= 1
            self.render_question()

    def next_question(self):
        self.save_current_answer()
        if self.current_index < len(self.questions) - 1:
            self.current_index += 1
            self.render_question()

    def jump_to(self, idx):
        self.save_current_answer()
        self.current_index = idx
        self.render_question()

    def submit_exam(self):
        answered = len(self.answers)
        total = len(self.questions)
        unanswered = total - answered
        if not messagebox.askyesno('Xác nhận nộp bài', f'Bạn đã trả lời {answered}/{total} câu.\nCòn {unanswered} câu chưa trả lời.\n\nBạn có chắc chắn muốn nộp bài không?'):
            return

        payload = {
            'action': 'submit_exam',
            'exam_id': self.exam.get('id'),
            'user_id': self.current_user.get('id'),
            'role': self.current_user.get('role'),
            'answers': [{'question_id': qid, 'answer': ans} for qid, ans in self.answers.items()],
            'duration': self.exam.get('duration') or 0,
        }
        thread = threading.Thread(target=self.submit_worker, args=(payload,), daemon=True)
        thread.start()

    def submit_worker(self, payload):
        try:
            response = self.client.send_request(payload)
            if response.get('status') == 'success':
                result = response.get('result') or response
                self.app.after(0, lambda: ResultWindow(self.app, result))
                self.app.after(0, self.destroy)
            else:
                self.app.after(0, lambda: messagebox.showerror('Lỗi nộp bài', response.get('message') or 'Không thể nộp bài'))
        except Exception as exc:
            self.app.after(0, lambda: messagebox.showerror('Lỗi mạng', str(exc)))


class ResultWindow(tk.Toplevel):
    def __init__(self, app, result):
        super().__init__(app)
        self.app = app
        self.result = result
        self.title('Kết quả thi')
        self.geometry('560x380')
        self.configure(bg='#eef3f6')
        self.build_ui()

    def build_ui(self):
        frame = tk.Frame(self, bg='#ffffff', padx=25, pady=25)
        frame.pack(fill='both', expand=True)
        tk.Label(frame, text='KẾT QUẢ THI', font=('Arial', 20, 'bold'), fg='#102a43', bg='#ffffff').pack(pady=(0, 16))
        tk.Label(frame, text='Môn: ' + (self.result.get('subject') or 'Lập trình mạng'), font=('Arial', 12), bg='#ffffff').pack(anchor='w')
        tk.Label(frame, text='Tổng số câu: ' + str(self.result.get('total_questions') or 0), font=('Arial', 12), bg='#ffffff').pack(anchor='w')
        tk.Label(frame, text='Đã trả lời: ' + str(self.result.get('answered_questions') or 0), font=('Arial', 12), bg='#ffffff').pack(anchor='w')
        tk.Label(frame, text='Đúng: ' + str(self.result.get('correct_answers') or 0), font=('Arial', 12), bg='#ffffff').pack(anchor='w')
        tk.Label(frame, text='Sai: ' + str(self.result.get('wrong_answers') or 0), font=('Arial', 12), bg='#ffffff').pack(anchor='w')
        tk.Label(frame, text='Chưa trả lời: ' + str(self.result.get('unanswered_questions') or 0), font=('Arial', 12), bg='#ffffff').pack(anchor='w')
        tk.Label(frame, text='ĐIỂM: ' + str(self.result.get('score') or 0) + ' / 10', font=('Arial', 16, 'bold'), fg='#0d6efd', bg='#ffffff').pack(anchor='w', pady=(16, 0))
        tk.Button(frame, text='Quay về trang chủ', command=self.destroy, width=16, bg='#198754', fg='white').pack(pady=14)

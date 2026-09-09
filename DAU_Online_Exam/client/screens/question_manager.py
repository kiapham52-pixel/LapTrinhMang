import tkinter as tk
from tkinter import ttk, messagebox
import threading


class QuestionManagementWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.current_user = app.current_user or {}
        self.client = app.client
        self.title('Quản lý câu hỏi')
        self.geometry('1100x680')
        self.configure(bg='#eef3f6')

        self.build_ui()
        self.load_questions()

    def build_ui(self):
        self.frame = tk.Frame(self, bg='#eef3f6', padx=20, pady=20)
        self.frame.pack(fill='both', expand=True)

        header = tk.Frame(self.frame, bg='#ffffff', padx=20, pady=16)
        header.pack(fill='x')
        tk.Label(header, text='Quản lý câu hỏi', font=('Arial', 20, 'bold'), fg='#102a43', bg='#ffffff').pack(anchor='w')

        toolbar = tk.Frame(self.frame, bg='#eef3f6', pady=12)
        toolbar.pack(fill='x')

        self.search_entry = tk.Entry(toolbar, width=35, font=('Arial', 11))
        self.search_entry.pack(side='left', padx=(0, 8))
        tk.Button(toolbar, text='Tìm kiếm', command=self.search_questions, width=14, bg='#0d6efd', fg='white').pack(side='left', padx=(0, 8))
        tk.Button(toolbar, text='Thêm câu hỏi', command=self.open_create_form, width=16, bg='#198754', fg='white').pack(side='left', padx=(0, 8))
        tk.Button(toolbar, text='Sửa', command=self.open_edit_form, width=10, bg='#ffc107', fg='#102a43').pack(side='left', padx=(0, 8))
        tk.Button(toolbar, text='Xóa', command=self.delete_selected_question, width=10, bg='#dc3545', fg='white').pack(side='left', padx=(0, 8))
        tk.Button(toolbar, text='Làm mới', command=self.load_questions, width=12).pack(side='left', padx=(0, 8))

        table_panel = tk.Frame(self.frame, bg='#ffffff', padx=10, pady=10)
        table_panel.pack(fill='both', expand=True)

        cols = ('stt', 'id', 'question_text', 'subject', 'difficulty', 'correct_answer', 'created_at')
        self.tree = ttk.Treeview(table_panel, columns=cols, show='headings', height=22)
        self.tree.heading('stt', text='STT')
        self.tree.heading('id', text='ID')
        self.tree.heading('question_text', text='Nội dung câu hỏi')
        self.tree.heading('subject', text='Môn học')
        self.tree.heading('difficulty', text='Độ khó')
        self.tree.heading('correct_answer', text='Đáp án đúng')
        self.tree.heading('created_at', text='Ngày tạo')

        self.tree.column('stt', width=60, anchor='center')
        self.tree.column('id', width=60, anchor='center')
        self.tree.column('question_text', width=320)
        self.tree.column('subject', width=140)
        self.tree.column('difficulty', width=100)
        self.tree.column('correct_answer', width=110, anchor='center')
        self.tree.column('created_at', width=140)

        y_scroll = ttk.Scrollbar(table_panel, orient='vertical', command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_panel, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.pack(side='left', fill='both', expand=True)
        y_scroll.pack(side='right', fill='y')
        x_scroll.pack(side='bottom', fill='x')

    def load_questions(self):
        payload = {'action': 'get_questions', 'role': self.current_user.get('role'), 'user_id': self.current_user.get('id')}
        self.start_worker(payload, self.render_questions)

    def search_questions(self):
        keyword = self.search_entry.get().strip()
        payload = {'action': 'search_questions', 'role': self.current_user.get('role'), 'user_id': self.current_user.get('id'), 'keyword': keyword}
        self.start_worker(payload, self.render_questions)

    def start_worker(self, payload, callback):
        thread = threading.Thread(target=self.request_worker, args=(payload, callback), daemon=True)
        thread.start()

    def request_worker(self, payload, callback):
        try:
            response = self.client.send_request(payload)
            self.app.after(0, lambda: callback(response))
        except Exception as exc:
            self.app.after(0, lambda: messagebox.showerror('Lỗi mạng', str(exc)))

    def render_questions(self, response):
        if response.get('success') is not True and response.get('status') != 'success':
            messagebox.showerror('Lỗi', response.get('message', 'Không thể tải danh sách câu hỏi'))
            return

        questions = response.get('questions', [])
        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, q in enumerate(questions, start=1):
            values = (
                i,
                q.get('id'),
                q.get('content') or q.get('question_text') or '',
                q.get('subject') or '',
                q.get('difficulty') or '',
                q.get('correct_answer') or '',
                (q.get('created_at') or '').split(' ')[0] if q.get('created_at') else ''
            )
            self.tree.insert('', 'end', values=values)

    def open_create_form(self):
        form = QuestionFormDialog(self, 'create')
        self.wait_window(form)
        self.load_questions()

    def open_edit_form(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning('Chọn câu hỏi', 'Vui lòng chọn câu hỏi cần sửa.')
            return
        values = self.tree.item(selected[0], 'values')
        qid = values[1]
        form = QuestionFormDialog(self, 'edit', question_id=qid, fields={
            'question_text': values[2],
            'subject': values[3],
            'difficulty': values[4],
            'correct_answer': values[5],
        })
        self.wait_window(form)
        self.load_questions()

    def delete_selected_question(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning('Chọn câu hỏi', 'Vui lòng chọn câu hỏi cần xóa.')
            return
        values = self.tree.item(selected[0], 'values')
        qid = values[1]
        content = values[2]
        answer = messagebox.askyesno('Xác nhận', f'Bạn có chắc chắn muốn xóa câu hỏi này không?\n\n{content[:80]}')
        if not answer:
            return
        payload = {'action': 'delete_question', 'role': self.current_user.get('role'), 'user_id': self.current_user.get('id'), 'question_id': qid}
        response = self.client.send_request(payload)
        if response.get('success') is True or response.get('status') == 'success':
            messagebox.showinfo('Thành công', response.get('message', 'Đã xóa câu hỏi'))
            self.load_questions()
        else:
            messagebox.showerror('Lỗi', response.get('message', 'Không thể xóa câu hỏi'))


class QuestionFormDialog(tk.Toplevel):
    def __init__(self, parent, mode, question_id=None, fields=None):
        super().__init__(parent)
        self.parent = parent
        self.mode = mode
        self.question_id = question_id
        self.current_user = parent.current_user
        self.client = parent.client
        self.title('Thêm câu hỏi' if mode == 'create' else 'Sửa câu hỏi')
        self.geometry('620x560')
        self.configure(bg='#eef3f6')

        form = tk.Frame(self, bg='#ffffff', padx=20, pady=20)
        form.pack(fill='both', expand=True)

        tk.Label(form, text='Nội dung câu hỏi', font=('Arial', 11, 'bold'), bg='#ffffff').grid(row=0, column=0, sticky='w', padx=5, pady=8)
        self.question_text = tk.Text(form, width=50, height=4)
        self.question_text.grid(row=0, column=1, padx=5, pady=8)

        for idx, opt in enumerate(['option_a', 'option_b', 'option_c', 'option_d'], start=1):
            tk.Label(form, text=f'Đáp án {chr(64 + idx)}', font=('Arial', 11, 'bold'), bg='#ffffff').grid(row=idx, column=0, sticky='w', padx=5, pady=8)
            entry = tk.Entry(form, width=35)
            entry.grid(row=idx, column=1, padx=5, pady=8)
            setattr(self, opt, entry)

        tk.Label(form, text='Đáp án đúng', font=('Arial', 11, 'bold'), bg='#ffffff').grid(row=5, column=0, sticky='w', padx=5, pady=8)
        self.correct_answer = ttk.Combobox(form, values=['A', 'B', 'C', 'D'], state='readonly', width=10)
        self.correct_answer.grid(row=5, column=1, sticky='w', padx=5, pady=8)

        tk.Label(form, text='Môn học', font=('Arial', 11, 'bold'), bg='#ffffff').grid(row=6, column=0, sticky='w', padx=5, pady=8)
        self.subject = tk.Entry(form, width=35)
        self.subject.grid(row=6, column=1, padx=5, pady=8)

        tk.Label(form, text='Độ khó', font=('Arial', 11, 'bold'), bg='#ffffff').grid(row=7, column=0, sticky='w', padx=5, pady=8)
        self.difficulty = ttk.Combobox(form, values=['Dễ', 'Trung bình', 'Khó'], state='readonly', width=20)
        self.difficulty.grid(row=7, column=1, sticky='w', padx=5, pady=8)

        if fields:
            self.question_text.insert('1.0', fields.get('question_text') or '')
            self.subject.insert(0, fields.get('subject') or '')
            self.difficulty.set(fields.get('difficulty') or 'Dễ')
            self.correct_answer.set(fields.get('correct_answer') or 'A')

        buttons = tk.Frame(form, bg='#ffffff')
        buttons.grid(row=8, column=0, columnspan=2, pady=20)
        tk.Button(buttons, text='Lưu', command=self.save, width=12, bg='#0d6efd', fg='white').pack(side='left', padx=10)
        tk.Button(buttons, text='Hủy', command=self.destroy, width=12).pack(side='left', padx=10)

    def save(self):
        question_text = self.question_text.get('1.0', 'end').strip()
        option_a = self.option_a.get().strip()
        option_b = self.option_b.get().strip()
        option_c = self.option_c.get().strip()
        option_d = self.option_d.get().strip()
        correct_answer = self.correct_answer.get().strip().upper()
        subject = self.subject.get().strip()
        difficulty = self.difficulty.get().strip()

        if not question_text or not all([option_a, option_b, option_c, option_d]):
            messagebox.showerror('Lỗi dữ liệu', 'Nội dung câu hỏi và 4 đáp án không được rỗng.')
            return
        if not subject:
            messagebox.showerror('Lỗi dữ liệu', 'Môn học không được rỗng.')
            return
        if correct_answer not in ('A', 'B', 'C', 'D'):
            messagebox.showerror('Lỗi dữ liệu', 'Đáp án đúng phải thuộc A/B/C/D.')
            return
        if difficulty not in ('Dễ', 'Trung bình', 'Khó'):
            messagebox.showerror('Lỗi dữ liệu', 'Độ khó không hợp lệ.')
            return

        payload = {
            'action': 'create_question' if self.mode == 'create' else 'update_question',
            'role': self.current_user.get('role'),
            'user_id': self.current_user.get('id'),
            'question': {
                'question_text': question_text,
                'option_a': option_a,
                'option_b': option_b,
                'option_c': option_c,
                'option_d': option_d,
                'correct_answer': correct_answer,
                'subject': subject,
                'difficulty': difficulty,
            }
        }
        if self.mode == 'edit':
            payload['question_id'] = self.question_id

        response = self.client.send_request(payload)
        if response.get('success') is True or response.get('status') == 'success':
            messagebox.showinfo('Thành công', response.get('message', 'Thao tác thành công'))
            self.destroy()
        else:
            messagebox.showerror('Lỗi', response.get('message', 'Thao tác thất bại'))

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from client.screens.admin_ui import module_header, toolbar, primary_button, secondary_button, panel, empty_state, loading_state, configure_tree, BG, PANEL


class QuestionManagementWindow(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg='#eef3f6')
        self.root = parent.winfo_toplevel()
        self.app = self.root
        self.current_user = getattr(self.root, 'current_user') or {}
        self.client = getattr(self.root, 'client', None)
        self.configure(bg='#eef3f6')
        self.pack(fill='both', expand=True)
        self.subjects = []
        self.question_ids = {}

        self.build_ui()
        self.load_subjects()
        self.load_questions()

    def load_subjects(self):
        threading.Thread(target=self._subjects_worker, daemon=True).start()

    def _subjects_worker(self):
        response = self.client.send_request({'action': 'get_subjects', 'role': self.current_user.get('role')})
        self.root.after(0, lambda: self.set_subjects(response))

    def set_subjects(self, response):
        if response.get('status') == 'success':
            self.subjects = [subject.get('name') for subject in response.get('subjects', [])]

    def build_ui(self):
        self.frame = tk.Frame(self, bg='#f5f5f5', padx=20, pady=20)
        self.frame.pack(fill='both', expand=True)
        module_header(self.frame, '❓', 'NGÂN HÀNG CÂU HỎI', 'Quản lý và tổ chức toàn bộ câu hỏi của hệ thống.')
        bar = toolbar(self.frame)

        self.search_entry = tk.Entry(bar, width=35, font=('Arial', 11))
        self.search_entry.pack(side='left', padx=(0, 8))
        primary_button(bar, '🔍 Tìm câu hỏi', self.search_questions).pack(side='left')
        primary_button(bar, '+ Tạo câu hỏi', self.open_create_form).pack(side='left', padx=8)
        secondary_button(bar, 'Sửa', self.open_edit_form).pack(side='left')
        secondary_button(bar, 'Xóa', self.delete_selected_question).pack(side='left', padx=8)
        secondary_button(bar, 'Làm mới', self.load_questions).pack(side='left')

        self.form_host = tk.Frame(self.frame, bg='#f5f5f5')
        self.form_host.pack(fill='x', pady=(0, 10))

        table_panel = panel(self.frame, 10)
        table_panel.pack(fill='both', expand=True)

        cols = ('stt', 'question_text', 'subject', 'difficulty', 'correct_answer', 'exam_count', 'created_at')
        self.tree = ttk.Treeview(table_panel, columns=cols, show='headings', height=22)
        configure_tree(self.tree)
        self.tree.heading('stt', text='STT')
        self.tree.heading('question_text', text='Nội dung câu hỏi')
        self.tree.heading('subject', text='Môn học')
        self.tree.heading('difficulty', text='Độ khó')
        self.tree.heading('correct_answer', text='Đáp án đúng')
        self.tree.heading('exam_count', text='Số đề sử dụng')
        self.tree.heading('created_at', text='Ngày tạo')

        self.tree.column('stt', width=60, anchor='center')
        self.tree.column('question_text', width=320)
        self.tree.column('subject', width=140)
        self.tree.column('difficulty', width=100)
        self.tree.column('correct_answer', width=110, anchor='center')
        self.tree.column('exam_count', width=110, anchor='center')
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
            self.root.after(0, lambda: callback(response))
        except Exception as exc:
            self.root.after(0, lambda: messagebox.showerror('Lỗi mạng', str(exc)))

    def render_questions(self, response):
        if response.get('success') is not True and response.get('status') != 'success':
            messagebox.showerror('Lỗi', response.get('message', 'Không thể tải danh sách câu hỏi'))
            return

        questions = response.get('questions', [])
        self.question_ids = {}
        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, q in enumerate(questions, start=1):
            values = (
                i,
                q.get('content') or q.get('question_text') or '',
                q.get('subject') or '',
                q.get('difficulty') or '',
                q.get('correct_answer') or '',
                q.get('exam_count') or 0,
                (q.get('created_at') or '').split(' ')[0] if q.get('created_at') else ''
            )
            item_id = self.tree.insert('', 'end', values=values)
            self.question_ids[item_id] = q.get('id')

    def open_create_form(self):
        if not self.subjects:
            messagebox.showinfo('Chưa có môn học', 'Chưa có môn học. Vui lòng tạo môn học trước.')
            return
        self._clear_form_panel()
        QuestionFormFrame(self.form_host, self, 'create')

    def open_edit_form(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning('Chọn câu hỏi', 'Vui lòng chọn câu hỏi cần sửa.')
            return
        values = self.tree.item(selected[0], 'values')
        qid = self.question_ids.get(selected[0])
        self._clear_form_panel()
        QuestionFormFrame(self.form_host, self, 'edit', question_id=qid, fields={
            'question_text': values[1],
            'subject': values[2],
            'difficulty': values[3],
            'correct_answer': values[4],
        })

    def _clear_form_panel(self):
        for child in self.form_host.winfo_children():
            child.destroy()

    def delete_selected_question(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning('Chọn câu hỏi', 'Vui lòng chọn câu hỏi cần xóa.')
            return
        values = self.tree.item(selected[0], 'values')
        qid = self.question_ids.get(selected[0])
        content = values[1]
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


class QuestionFormFrame(tk.Frame):
    def __init__(self, parent, manager, mode, question_id=None, fields=None):
        super().__init__(parent, bg='#ffffff', padx=20, pady=20)
        self.name = 'question_form_frame'
        self.parent = parent
        self.manager = manager
        self.mode = mode
        self.question_id = question_id
        self.current_user = manager.current_user
        self.client = manager.client
        self.pack(fill='x', pady=(12, 0))

        tk.Label(self, text='Nội dung câu hỏi', font=('Arial', 11, 'bold'), bg='#ffffff').grid(row=0, column=0, sticky='w', padx=5, pady=8)
        self.question_text = tk.Text(self, width=50, height=4)
        self.question_text.grid(row=0, column=1, padx=5, pady=8)

        for idx, opt in enumerate(['option_a', 'option_b', 'option_c', 'option_d'], start=1):
            tk.Label(self, text=f'Đáp án {chr(64 + idx)}', font=('Arial', 11, 'bold'), bg='#ffffff').grid(row=idx, column=0, sticky='w', padx=5, pady=8)
            entry = tk.Entry(self, width=35)
            entry.grid(row=idx, column=1, padx=5, pady=8)
            setattr(self, opt, entry)

        tk.Label(self, text='Đáp án đúng', font=('Arial', 11, 'bold'), bg='#ffffff').grid(row=5, column=0, sticky='w', padx=5, pady=8)
        self.correct_answer = ttk.Combobox(self, values=['A', 'B', 'C', 'D'], state='readonly', width=10)
        self.correct_answer.grid(row=5, column=1, sticky='w', padx=5, pady=8)

        tk.Label(self, text='Môn học', font=('Arial', 11, 'bold'), bg='#ffffff').grid(row=6, column=0, sticky='w', padx=5, pady=8)
        self.subject = ttk.Combobox(self, values=manager.subjects, state='readonly', width=32)
        self.subject.grid(row=6, column=1, padx=5, pady=8)

        tk.Label(self, text='Độ khó', font=('Arial', 11, 'bold'), bg='#ffffff').grid(row=7, column=0, sticky='w', padx=5, pady=8)
        self.difficulty = ttk.Combobox(self, values=['Dễ', 'Trung bình', 'Khó'], state='readonly', width=20)
        self.difficulty.grid(row=7, column=1, sticky='w', padx=5, pady=8)

        if fields:
            self.question_text.insert('1.0', fields.get('question_text') or '')
            self.subject.insert(0, fields.get('subject') or '')
            self.difficulty.set(fields.get('difficulty') or 'Dễ')
            self.correct_answer.set(fields.get('correct_answer') or 'A')
        elif manager.subjects:
            self.subject.current(0)

        buttons = tk.Frame(self, bg='#ffffff')
        buttons.grid(row=8, column=0, columnspan=2, pady=20)
        tk.Button(buttons, text='Lưu câu hỏi', command=self.save, width=14, bg='#7F1D1D', fg='white').pack(side='left', padx=10)
        tk.Button(buttons, text='Hủy', command=self.destroy, width=12).pack(side='left', padx=10)
        preview = tk.Frame(self, bg='#fff7f7', padx=12, pady=12, highlightbackground='#fecaca', highlightthickness=1)
        preview.grid(row=9, column=0, columnspan=2, sticky='ew', padx=5, pady=(4, 12))
        tk.Label(preview, text='👁 XEM TRƯỚC', font=('Arial', 12, 'bold'), bg='#fff7f7', fg='#7F1D1D').pack(anchor='w')
        self.preview_label = tk.Label(preview, text='Nhập nội dung và đáp án để xem trước câu hỏi.', bg='#fff7f7', fg='#4b5563', justify='left', wraplength=650)
        self.preview_label.pack(anchor='w', pady=(6, 0))
        for widget in (self.question_text, self.option_a, self.option_b, self.option_c, self.option_d):
            widget.bind('<KeyRelease>', self.update_preview)

    def update_preview(self, _event=None):
        content = self.question_text.get('1.0', 'end').strip() or 'Nội dung câu hỏi...'
        options = '\n'.join(f'{letter}. {entry.get().strip() or "..."}' for letter, entry in zip(('A', 'B', 'C', 'D'), (self.option_a, self.option_b, self.option_c, self.option_d)))
        self.preview_label.config(text=f'{content}\n\n{options}\n\n✓ Đáp án đúng: {self.correct_answer.get() or "-"}')

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
            messagebox.showerror('Lỗi dữ liệu', 'Vui lòng chọn môn học. Hãy tạo môn học trước nếu danh sách đang trống.')
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
            self.manager.load_questions()
            self.destroy()
        else:
            messagebox.showerror('Lỗi', response.get('message', 'Thao tác thất bại'))

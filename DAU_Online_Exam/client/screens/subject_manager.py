import tkinter as tk
from tkinter import ttk, messagebox
import threading
from client.screens.admin_ui import module_header, toolbar, primary_button, secondary_button, panel, empty_state, loading_state, configure_tree, BG, PANEL, TEXT, MUTED


class SubjectManagementWindow(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg='#f5f5f5', padx=18, pady=18)
        self.root = parent.winfo_toplevel()
        self.client = getattr(self.root, 'client', None)
        self.user = getattr(self.root, 'current_user', {}) or {}
        self.pack(fill='both', expand=True)
        self.form = None
        self.subject_rows = []
        self.build_ui()
        self.load_subjects()

    def build_ui(self):
        module_header(self, '📚', 'QUẢN LÝ MÔN HỌC', 'Quản lý các môn học được sử dụng trong hệ thống thi.')
        bar = toolbar(self)
        self.search_var = tk.StringVar()
        tk.Entry(bar, textvariable=self.search_var, width=32, font=('Arial', 10)).pack(side='left', padx=(0, 8))
        primary_button(bar, '+ Thêm môn học', self.open_form).pack(side='left')
        secondary_button(bar, 'Làm mới', self.load_subjects).pack(side='left', padx=8)
        self.form_host = tk.Frame(self, bg='#f5f5f5')
        self.form_host.pack(fill='x')
        self.content_panel = panel(self, 12)
        self.content_panel.pack(fill='both', expand=True)

    def load_subjects(self):
        for child in self.content_panel.winfo_children():
            child.destroy()
        loading_state(self.content_panel).pack(fill='x')
        table_panel = panel(self.content_panel, 10)
        table_panel.pack(fill='both', expand=True, pady=(10, 0))
        self._build_tree(table_panel)
        threading.Thread(target=self._load_worker, daemon=True).start()

    def _build_tree(self, parent):
        columns = ('code', 'name', 'question_count', 'exam_count', 'status')
        self.tree = ttk.Treeview(parent, columns=columns, show='headings')
        configure_tree(self.tree)
        for column, heading, width in (('code', 'Mã môn', 120), ('name', 'Tên môn', 280), ('question_count', 'Số câu hỏi', 110), ('exam_count', 'Số đề', 90), ('status', 'Trạng thái', 120)):
            self.tree.heading(column, text=heading)
            self.tree.column(column, width=width)
        scroll = ttk.Scrollbar(parent, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')

    def _load_worker(self):
        response = self.client.send_request({'action': 'get_subjects', 'role': self.user.get('role')})
        self.root.after(0, lambda: self.render_subjects(response))

    def render_subjects(self, response):
        if response.get('status') != 'success':
            messagebox.showerror('Không thể tải môn học', response.get('message') or 'Lỗi máy chủ')
            return
        for item in self.tree.get_children():
            self.tree.delete(item)
        subjects = response.get('subjects', [])
        self.subject_rows = subjects
        for subject in subjects:
            self.tree.insert('', 'end', values=(subject.get('code'), subject.get('name'), subject.get('question_count', 0), subject.get('exam_count', 0), 'Hoạt động' if subject.get('status') == 'active' else 'Tạm dừng'))
        if not subjects:
            for child in self.content_panel.winfo_children():
                child.destroy()
            empty_state(self.content_panel, '📚', 'Chưa có môn học', 'Hãy tạo môn học đầu tiên để bắt đầu xây dựng ngân hàng câu hỏi.', '+ Tạo môn học', self.open_form).pack(fill='x')

    def open_form(self):
        if self.form is not None and self.form.winfo_exists():
            self.form.destroy()
        self.form = tk.Frame(self.form_host, bg='white', padx=16, pady=16)
        self.form.pack(fill='x', pady=(0, 12))
        tk.Label(self.form, text='THÊM MÔN HỌC', font=('Arial', 15, 'bold'), bg='white', fg='#7F1D1D').grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 10))
        fields = {}
        for row, (key, label) in enumerate((('code', 'Mã môn học'), ('name', 'Tên môn học'), ('description', 'Mô tả')), start=1):
            tk.Label(self.form, text=label, bg='white').grid(row=row, column=0, sticky='w', padx=6, pady=6)
            widget = tk.Text(self.form, width=42, height=3) if key == 'description' else tk.Entry(self.form, width=42)
            widget.grid(row=row, column=1, padx=6, pady=6)
            fields[key] = widget
        buttons = tk.Frame(self.form, bg='white')
        buttons.grid(row=4, column=1, sticky='e', pady=8)
        tk.Button(buttons, text='Hủy', command=self.form.destroy).pack(side='left', padx=5)
        tk.Button(buttons, text='Lưu môn học', command=lambda: self.save_subject(fields), bg='#7F1D1D', fg='white').pack(side='left')

    def save_subject(self, fields):
        description = fields['description'].get('1.0', 'end').strip()
        response = self.client.send_request({
            'action': 'create_subject', 'role': self.user.get('role'),
            'code': fields['code'].get().strip(), 'name': fields['name'].get().strip(),
            'description': description, 'status': 'active',
        })
        if response.get('status') == 'success':
            messagebox.showinfo('Thành công', 'Đã thêm môn học.')
            self.form.destroy()
            self.load_subjects()
        else:
            messagebox.showerror('Không thể lưu môn học', response.get('message') or 'Dữ liệu không hợp lệ')

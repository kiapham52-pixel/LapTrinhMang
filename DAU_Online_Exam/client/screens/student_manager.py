import tkinter as tk
from tkinter import ttk, messagebox
import threading


class StudentManagementWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.current_user = app.current_user or {}
        self.client = app.client
        self.title('Quản lý sinh viên')
        self.geometry('1100x680')
        self.configure(bg='#eef3f6')
        self.search_var = tk.StringVar()
        self.student_id_by_code = {}

        self.build_ui()
        self.load_students()

    def build_ui(self):
        self.frame = tk.Frame(self, bg='#eef3f6', padx=20, pady=20)
        self.frame.pack(fill='both', expand=True)

        header = tk.Frame(self.frame, bg='#ffffff', padx=20, pady=16)
        header.pack(fill='x')
        tk.Label(header, text='Quản lý sinh viên', font=('Arial', 20, 'bold'), fg='#102a43', bg='#ffffff').pack(anchor='w')

        toolbar = tk.Frame(self.frame, bg='#eef3f6', pady=12)
        toolbar.pack(fill='x')

        self.search_entry = tk.Entry(toolbar, width=35, font=('Arial', 11))
        self.search_entry.pack(side='left', padx=(0, 8))
        tk.Button(toolbar, text='Tìm kiếm', command=self.search_students, width=14, bg='#0d6efd', fg='white').pack(side='left', padx=(0, 8))
        tk.Button(toolbar, text='Thêm sinh viên', command=self.open_create_form, width=16, bg='#198754', fg='white').pack(side='left', padx=(0, 8))
        tk.Button(toolbar, text='Sửa', command=self.open_edit_form, width=10, bg='#ffc107', fg='#102a43').pack(side='left', padx=(0, 8))
        tk.Button(toolbar, text='Xóa', command=self.delete_selected_student, width=10, bg='#dc3545', fg='white').pack(side='left', padx=(0, 8))
        tk.Button(toolbar, text='Làm mới', command=self.load_students, width=12).pack(side='left', padx=(0, 8))

        table_panel = tk.Frame(self.frame, bg='#ffffff', padx=10, pady=10)
        table_panel.pack(fill='both', expand=True)

        cols = ('stt', 'student_code', 'full_name', 'email', 'class_name', 'username', 'role', 'status')
        self.tree = ttk.Treeview(table_panel, columns=cols, show='headings', height=22)
        self.tree.heading('stt', text='STT')
        self.tree.heading('student_code', text='Mã sinh viên')
        self.tree.heading('full_name', text='Họ và tên')
        self.tree.heading('email', text='Email')
        self.tree.heading('class_name', text='Lớp')
        self.tree.heading('username', text='Username')
        self.tree.heading('role', text='Vai trò')
        self.tree.heading('status', text='Trạng thái')

        self.tree.column('stt', width=50, anchor='center')
        self.tree.column('student_code', width=110, anchor='center')
        self.tree.column('full_name', width=160)
        self.tree.column('email', width=180)
        self.tree.column('class_name', width=110)
        self.tree.column('username', width=110)
        self.tree.column('role', width=100)
        self.tree.column('status', width=120)

        y_scroll = ttk.Scrollbar(table_panel, orient='vertical', command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_panel, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.pack(side='left', fill='both', expand=True)
        y_scroll.pack(side='right', fill='y')
        x_scroll.pack(side='bottom', fill='x')

    def load_students(self):
        self.start_worker({'action': 'get_students', 'role': self.current_user.get('role'), 'user_id': self.current_user.get('id')}, self.render_students)

    def search_students(self):
        keyword = self.search_entry.get().strip()
        payload = {'action': 'search_students', 'role': self.current_user.get('role'), 'user_id': self.current_user.get('id'), 'keyword': keyword}
        self.start_worker(payload, self.render_students)

    def start_worker(self, payload, callback):
        thread = threading.Thread(target=self.request_worker, args=(payload, callback), daemon=True)
        thread.start()

    def request_worker(self, payload, callback):
        try:
            response = self.client.send_request(payload)
            self.app.after(0, lambda: callback(response))
        except Exception as exc:
            self.app.after(0, lambda: messagebox.showerror('Lỗi mạng', str(exc)))

    def render_students(self, response):
        if response.get('success') is not True and response.get('status') != 'success':
            messagebox.showerror('Lỗi', response.get('message', 'Không thể tải danh sách sinh viên'))
            return

        students = response.get('students', [])
        self.student_id_by_code = {}
        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, student in enumerate(students, start=1):
            code = student.get('student_code', '')
            sid = student.get('id')
            if code:
                self.student_id_by_code[code] = sid
            values = (
                i,
                code,
                student.get('full_name', ''),
                student.get('email', ''),
                student.get('class_name', ''),
                student.get('username', ''),
                student.get('role', 'student'),
                student.get('status', 'active')
            )
            self.tree.insert('', 'end', values=values)

    def open_create_form(self):
        form = StudentFormDialog(self, 'create', None)
        self.wait_window(form)
        self.load_students()

    def open_edit_form(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning('Chọn sinh viên', 'Vui lòng chọn sinh viên cần sửa.')
            return
        values = self.tree.item(selected[0], 'values')
        student_code = values[1]
        student_id = self.student_id_by_code.get(student_code)
        form = StudentFormDialog(self, 'edit', None, student_code=values[1], full_name=values[2], email=values[3], class_name=values[4], username=values[5], role=values[6], status=values[7], student_id=student_id)
        self.wait_window(form)
        self.load_students()

    def delete_selected_student(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning('Chọn sinh viên', 'Vui lòng chọn sinh viên cần xóa.')
            return
        values = self.tree.item(selected[0], 'values')
        student_code = values[1]
        answer = messagebox.askyesno('Xác nhận', f'Bạn có chắc chắn muốn xóa sinh viên {student_code} không?')
        if not answer:
            return
        # Send request with selected username and role
        target = {'action': 'delete_student', 'role': self.current_user.get('role'), 'user_id': self.current_user.get('id'), 'student_code': student_code}
        response = self.client.send_request(target)
        if response.get('success') is True or response.get('status') == 'success':
            messagebox.showinfo('Thành công', response.get('message', 'Đã xóa sinh viên'))
            self.load_students()
        else:
            messagebox.showerror('Lỗi', response.get('message', 'Không thể xóa sinh viên'))


class StudentFormDialog(tk.Toplevel):
    def __init__(self, parent, mode, student=None, student_id=None, student_code=None, full_name=None, email=None, class_name=None, username=None, role=None, status=None):
        super().__init__(parent)
        self.parent = parent
        self.mode = mode
        self.student = student
        self.student_id = student_id
        self.current_user = parent.current_user
        self.client = parent.client
        self.title('Thêm sinh viên' if mode == 'create' else 'Sửa sinh viên')
        self.geometry('460x560')
        self.configure(bg='#eef3f6')

        form = tk.Frame(self, bg='#ffffff', padx=20, pady=20)
        form.pack(fill='both', expand=True)

        tk.Label(form, text='Mã sinh viên', font=('Arial', 11, 'bold'), bg='#ffffff').grid(row=0, column=0, sticky='w', padx=5, pady=8)
        self.student_code = tk.Entry(form, width=30)
        self.student_code.grid(row=0, column=1, padx=5, pady=8)

        tk.Label(form, text='Họ tên', font=('Arial', 11, 'bold'), bg='#ffffff').grid(row=1, column=0, sticky='w', padx=5, pady=8)
        self.full_name = tk.Entry(form, width=30)
        self.full_name.grid(row=1, column=1, padx=5, pady=8)

        tk.Label(form, text='Email', font=('Arial', 11, 'bold'), bg='#ffffff').grid(row=2, column=0, sticky='w', padx=5, pady=8)
        self.email = tk.Entry(form, width=30)
        self.email.grid(row=2, column=1, padx=5, pady=8)

        tk.Label(form, text='Lớp', font=('Arial', 11, 'bold'), bg='#ffffff').grid(row=3, column=0, sticky='w', padx=5, pady=8)
        self.class_name = tk.Entry(form, width=30)
        self.class_name.grid(row=3, column=1, padx=5, pady=8)

        tk.Label(form, text='Username', font=('Arial', 11, 'bold'), bg='#ffffff').grid(row=4, column=0, sticky='w', padx=5, pady=8)
        self.username = tk.Entry(form, width=30)
        self.username.grid(row=4, column=1, padx=5, pady=8)

        tk.Label(form, text='Password', font=('Arial', 11, 'bold'), bg='#ffffff').grid(row=5, column=0, sticky='w', padx=5, pady=8)
        self.password = tk.Entry(form, width=30, show='*')
        self.password.grid(row=5, column=1, padx=5, pady=8)

        tk.Label(form, text='Trạng thái', font=('Arial', 11, 'bold'), bg='#ffffff').grid(row=6, column=0, sticky='w', padx=5, pady=8)
        self.status = ttk.Combobox(form, values=['active', 'inactive'], state='readonly', width=28)
        self.status.grid(row=6, column=1, padx=5, pady=8)
        self.status.set(status or 'active')

        if mode == 'edit':
            self.student_code.insert(0, student_code or '')
            self.full_name.insert(0, full_name or '')
            self.email.insert(0, email or '')
            self.class_name.insert(0, class_name or '')
            self.username.insert(0, username or '')
            self.status.set(status or 'active')
            # password left blank

        buttons = tk.Frame(form, bg='#ffffff')
        buttons.grid(row=7, column=0, columnspan=2, pady=20)
        tk.Button(buttons, text='Lưu', command=self.save, width=12, bg='#0d6efd', fg='white').pack(side='left', padx=10)
        tk.Button(buttons, text='Hủy', command=self.destroy, width=12).pack(side='left', padx=10)

    def save(self):
        payload = {
            'role': self.current_user.get('role'),
            'user_id': self.current_user.get('id'),
        }
        student = {
            'student_code': self.student_code.get().strip(),
            'full_name': self.full_name.get().strip(),
            'email': self.email.get().strip(),
            'class_name': self.class_name.get().strip(),
            'username': self.username.get().strip(),
            'password': self.password.get().strip(),
            'status': self.status.get().strip(),
        }
        if self.mode == 'create':
            payload['action'] = 'create_student'
            payload['student'] = student
        else:
            payload['action'] = 'update_student'
            payload['student_id'] = self.student_id
            payload['student'] = student

        response = self.client.send_request(payload)
        if response.get('success') is True or response.get('status') == 'success':
            messagebox.showinfo('Thành công', response.get('message', 'Thao tác thành công'))
            self.destroy()
        else:
            messagebox.showerror('Lỗi', response.get('message', 'Thao tác thất bại'))

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import sys
from datetime import datetime, timedelta
from client.screens.admin_ui import module_header, toolbar, primary_button, secondary_button, panel, configure_tree

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class RoomManagementWindow(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg='#f5f5f5')
        self.root = parent.winfo_toplevel()
        self.app = self.root
        self.current_user = getattr(self.root, 'current_user') or {}
        self.client = getattr(self.root, 'client', None)
        self.configure(bg='#f5f5f5')
        self.pack(fill='both', expand=True)
        self.rooms = []
        self.exams = []

        self.build_ui()
        self.load_rooms()
        self.load_exams()

    def build_ui(self):
        self.frame = tk.Frame(self, bg='#f5f5f5', padx=18, pady=18)
        self.frame.pack(fill='both', expand=True)

        module_header(self.frame, '🏫', 'QUẢN LÝ PHÒNG THI', 'Quản lý các phòng thi và sinh viên tham gia.')

        bar = toolbar(self.frame)

        self.search_entry = tk.Entry(bar, width=35, font=('Arial', 11))
        self.search_entry.pack(side='left', padx=(0, 8))
        primary_button(bar, '🔍 Tìm phòng', self.search_rooms).pack(side='left')
        primary_button(bar, '+ Tạo phòng thi', self.open_create_room_form).pack(side='left', padx=8)
        secondary_button(bar, 'Làm mới', self.load_rooms).pack(side='left')

        filter_frame = tk.Frame(bar, bg='#f5f5f5')
        filter_frame.pack(side='left', padx=(20, 0))
        tk.Label(filter_frame, text='Trạng thái:', font=('Arial', 10), bg='#f5f5f5', fg='#1f2937').pack(side='left')
        self.status_var = tk.StringVar(value='ALL')
        self.status_combo = ttk.Combobox(filter_frame, textvariable=self.status_var, state='readonly', width=16)
        self.status_combo['values'] = ('ALL', 'DRAFT', 'WAITING', 'RUNNING', 'FINISHED', 'CANCELLED')
        self.status_combo.pack(side='left', padx=(8, 0))
        tk.Button(filter_frame, text='Lọc', command=self.filter_rooms, width=10, bg='#7F1D1D', fg='white').pack(side='left', padx=(8, 0))

        self.form_host = tk.Frame(self.frame, bg='#f5f5f5')
        self.form_host.pack(fill='x')

        table_panel = panel(self.frame, 10)
        table_panel.pack(fill='both', expand=True)

        cols = ('room_code', 'name', 'subject', 'exam_title', 'students_count', 'online_count', 'submitted_count', 'duration', 'status')
        self.tree = ttk.Treeview(table_panel, columns=cols, show='headings', height=18)
        configure_tree(self.tree)
        self.tree.heading('room_code', text='Mã phòng')
        self.tree.heading('name', text='Tên phòng')
        self.tree.heading('subject', text='Môn thi')
        self.tree.heading('exam_title', text='Đề thi')
        self.tree.heading('students_count', text='Số thí sinh')
        self.tree.heading('online_count', text='Online')
        self.tree.heading('submitted_count', text='Đã nộp')
        self.tree.heading('duration', text='Thời gian')
        self.tree.heading('status', text='Trạng thái')

        self.tree.column('room_code', width=90, anchor='center')
        self.tree.column('name', width=150)
        self.tree.column('subject', width=130)
        self.tree.column('exam_title', width=150)
        self.tree.column('students_count', width=90, anchor='center')
        self.tree.column('online_count', width=90, anchor='center')
        self.tree.column('submitted_count', width=90, anchor='center')
        self.tree.column('duration', width=100, anchor='center')
        self.tree.column('status', width=110, anchor='center')

        y_scroll = ttk.Scrollbar(table_panel, orient='vertical', command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_panel, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.tree.pack(side='left', fill='both', expand=True)
        y_scroll.pack(side='right', fill='y')
        x_scroll.pack(side='bottom', fill='x')

        action_frame = tk.Frame(self.frame, bg='#f5f5f5', pady=10)
        action_frame.pack(fill='x')
        tk.Button(action_frame, text='Xem', command=self.view_room, width=10, bg='#1f2937', fg='white').pack(side='left', padx=(0, 8))
        tk.Button(action_frame, text='Sửa', command=self.edit_room, width=10, bg='#B91C1C', fg='white').pack(side='left', padx=(0, 8))
        tk.Button(action_frame, text='Mở', command=self.open_room, width=10, bg='#e58a00', fg='white').pack(side='left', padx=(0, 8))
        tk.Button(action_frame, text='Bắt đầu', command=self.start_room, width=11, bg='#991B1B', fg='white').pack(side='left', padx=(0, 8))
        tk.Button(action_frame, text='Giám sát', command=self.monitor_room, width=11, bg='#1f2937', fg='white').pack(side='left', padx=(0, 8))
        tk.Button(action_frame, text='Kết thúc', command=self.finish_room, width=11, bg='#6b7280', fg='white').pack(side='left', padx=(0, 8))
        tk.Button(action_frame, text='Xóa', command=self.delete_room, width=10, bg='#dc2626', fg='white').pack(side='left', padx=(0, 8))

    def search_rooms(self):
        keyword = self.search_entry.get().strip()
        payload = {'action': 'get_rooms', 'role': self.current_user.get('role'), 'keyword': keyword}
        self.request_rooms(payload)

    def filter_rooms(self):
        status = self.status_var.get()
        payload = {'action': 'get_rooms', 'role': self.current_user.get('role'), 'status': status}
        self.request_rooms(payload)

    def load_rooms(self):
        payload = {'action': 'get_rooms', 'role': self.current_user.get('role')}
        self.request_rooms(payload)

    def load_exams(self):
        threading.Thread(target=self._exam_worker, daemon=True).start()

    def _exam_worker(self):
        response = self.client.send_request({'action': 'get_exams'})
        self.root.after(0, lambda: self.set_exams(response))

    def set_exams(self, response):
        if response.get('status') == 'success':
            self.exams = [exam for exam in response.get('exams', []) if exam.get('status') == 'active']

    def request_rooms(self, payload):
        thread = threading.Thread(target=self.worker, args=(payload,), daemon=True)
        thread.start()

    def worker(self, payload):
        try:
            response = self.client.send_request(payload)
            self.root.after(0, lambda: self.render_rooms(response))
        except Exception as exc:
            self.root.after(0, lambda: messagebox.showerror('Lỗi mạng', str(exc)))

    def render_rooms(self, response):
        if response.get('status') != 'success':
            messagebox.showerror('Lỗi', response.get('message') or 'Không lấy được phòng thi')
            return
        self.rooms = response.get('rooms', [])
        for row in self.tree.get_children():
            self.tree.delete(row)
        for room in self.rooms:
            self.tree.insert('', 'end', values=(
                room.get('room_code') or room.get('id') or '',
                room.get('name') or '',
                room.get('subject') or '',
                room.get('exam_title') or '',
                room.get('students_count') or 0,
                room.get('online_count') or 0,
                room.get('submitted_count') or 0,
                room.get('duration') or 0,
                room.get('status') or 'DRAFT',
            ))

    def open_create_room_form(self):
        if hasattr(self, 'room_form'):
            self.room_form.destroy()
        self.room_form = tk.Frame(self.form_host, bg='#ffffff', padx=20, pady=20)
        self.room_form.pack(fill='x', pady=(12, 0))
        tk.Label(self.room_form, text='Tạo phòng thi', font=('Arial', 16, 'bold'), bg='#ffffff').pack(anchor='w', pady=(0, 12))

        default_start = (datetime.now() + timedelta(days=1)).replace(second=0, microsecond=0)
        default_end = default_start + timedelta(minutes=45)
        fields = {
            'room_code': tk.StringVar(value='PH' + str(self.app.current_user.get('id', 0))),
            'name': tk.StringVar(),
            'subject': tk.StringVar(),
            'exam_id': tk.StringVar(),
            'duration': tk.StringVar(value='60'),
            'start_time': tk.StringVar(value=default_start.strftime('%Y-%m-%d %H:%M')),
            'end_time': tk.StringVar(value=default_end.strftime('%Y-%m-%d %H:%M')),
            'status': tk.StringVar(value='DRAFT'),
        }
        labels = ['Mã phòng', 'Tên phòng', 'Môn thi', 'Đề thi', 'Thời lượng', 'Thời gian bắt đầu', 'Thời gian kết thúc', 'Trạng thái']
        label_map = {
            'Mã phòng': 'room_code', 'Tên phòng': 'name', 'Môn thi': 'subject',
            'Thời lượng': 'duration', 'Thời gian bắt đầu': 'start_time',
            'Thời gian kết thúc': 'end_time', 'Trạng thái': 'status',
        }
        for idx, label in enumerate(labels):
            row = tk.Frame(self.room_form, bg='#ffffff', padx=12, pady=8)
            row.pack(fill='x', padx=4, pady=4)
            tk.Label(row, text=label, width=18, bg='#ffffff', fg='#1f2937', font=('Arial', 10, 'bold')).pack(side='left')
            if label == 'Đề thi':
                exam_names = [f"{exam.get('id')} - {exam.get('title')} ({exam.get('total_questions', 0)} câu)" for exam in self.exams]
                exam_var = tk.StringVar()
                entry = ttk.Combobox(row, textvariable=exam_var, values=exam_names, state='readonly', width=38)
                entry.pack(side='left')
                if exam_names:
                    entry.current(0)
                def select_exam(_event=None):
                    selected = next((exam for exam in self.exams if f"{exam.get('id')} - {exam.get('title')} ({exam.get('total_questions', 0)} câu)" == exam_var.get()), None)
                    fields['exam_id'].set(str(selected.get('id')) if selected else '')
                    if selected:
                        fields['subject'].set(selected.get('subject') or '')
                        fields['duration'].set(str(selected.get('duration') or 60))
                entry.bind('<<ComboboxSelected>>', select_exam)
                if exam_names:
                    select_exam()
            else:
                entry = tk.Entry(row, textvariable=fields[label_map[label]], width=30, font=('Arial', 10))
                entry.pack(side='left')

        def create_room_submit():
            room = {key: variable.get().strip() for key, variable in fields.items()}
            if not room['room_code']:
                messagebox.showerror('Dữ liệu không hợp lệ', 'Mã phòng không được để trống.')
                return
            if not room['name']:
                messagebox.showerror('Dữ liệu không hợp lệ', 'Tên phòng không được để trống.')
                return
            if not room['subject']:
                messagebox.showerror('Dữ liệu không hợp lệ', 'Môn thi không được để trống.')
                return
            try:
                int(room['exam_id'])
            except (TypeError, ValueError):
                messagebox.showerror('Dữ liệu không hợp lệ', 'ID đề thi phải là số nguyên.')
                return
            try:
                duration = int(room['duration'])
            except (TypeError, ValueError):
                messagebox.showerror('Dữ liệu không hợp lệ', 'Thời lượng phải là số nguyên.')
                return
            if duration <= 0:
                messagebox.showerror('Dữ liệu không hợp lệ', 'Thời lượng phải lớn hơn 0 phút.')
                return
            try:
                start_time = datetime.strptime(room['start_time'], '%Y-%m-%d %H:%M')
                end_time = datetime.strptime(room['end_time'], '%Y-%m-%d %H:%M')
            except ValueError:
                messagebox.showerror('Dữ liệu không hợp lệ', 'Thời gian phải có dạng YYYY-MM-DD HH:MM.')
                return
            if start_time <= datetime.now():
                messagebox.showerror('Dữ liệu không hợp lệ', 'Thời gian bắt đầu đã ở trong quá khứ.')
                return
            if end_time <= start_time:
                messagebox.showerror('Dữ liệu không hợp lệ', 'Thời gian kết thúc phải sau thời gian bắt đầu.')
                return

            payload = {'action': 'create_room', 'role': self.current_user.get('role'), 'room': room}
            try:
                response = self.client.send_request(payload)
            except Exception as exc:
                messagebox.showerror('Lỗi kết nối', f'Không thể tạo phòng thi: {exc}')
                return
            if response.get('status') == 'success':
                messagebox.showinfo('Thành công', 'Tạo phòng thi thành công.')
                self.room_form.destroy()
                self.load_rooms()
            else:
                messagebox.showerror('Không thể tạo phòng thi', response.get('message') or 'Server không trả về lý do lỗi.')

        btn_frame = tk.Frame(self.room_form, bg='#ffffff', pady=12)
        btn_frame.pack(fill='x')
        tk.Button(btn_frame, text='Hủy', command=self.room_form.destroy, width=12, bg='#6b7280', fg='white').pack(side='left', padx=16)
        tk.Button(btn_frame, text='Tạo phòng thi', command=create_room_submit, width=16, bg='#B91C1C', fg='white').pack(side='left', padx=(8, 0))

    def view_room(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning('Chưa chọn', 'Vui lòng chọn một phòng thi.')
            return
        values = self.tree.item(selected[0], 'values')
        messagebox.showinfo('Chi tiết phòng thi', f"Phòng: {values[1]}\nMã: {values[0]}\nMôn: {values[2]}\nĐề thi: {values[3]}\nTrạng thái: {values[8]}")

    def edit_room(self):
        self.view_room()

    def open_room(self):
        room_id = self.get_selected_room_id()
        if not room_id:
            return
        self.send_room_action('open_room', room_id)

    def start_room(self):
        room_id = self.get_selected_room_id()
        if not room_id:
            return
        self.send_room_action('start_room', room_id)

    def finish_room(self):
        room_id = self.get_selected_room_id()
        if not room_id:
            return
        self.send_room_action('finish_room', room_id)

    def monitor_room(self):
        room_id = self.get_selected_room_id()
        if not room_id:
            return
        messagebox.showinfo('Giám sát phòng thi', f'Giám sát phòng {room_id}')

    def delete_room(self):
        room_id = self.get_selected_room_id()
        if not room_id:
            return
        payload = {'action': 'delete_room', 'role': self.current_user.get('role'), 'room_id': room_id}
        response = self.client.send_request(payload)
        if response.get('status') == 'success':
            messagebox.showinfo('Thành công', 'Phòng thi đã xóa')
            self.load_rooms()
        else:
            messagebox.showerror('Lỗi', response.get('message'))

    def send_room_action(self, action, room_id):
        payload = {'action': action, 'role': self.current_user.get('role'), 'room_id': room_id}
        response = self.client.send_request(payload)
        if response.get('status') == 'success':
            messagebox.showinfo('Thành công', response.get('message'))
            self.load_rooms()
        else:
            messagebox.showerror('Lỗi', response.get('message'))

    def get_selected_room_id(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning('Chưa chọn phòng', 'Vui lòng chọn phòng thi.')
            return None
        values = self.tree.item(selected[0], 'values')
        # room_code is shown but real id unavailable; use room_code string as common id fallback
        room_code = values[0]
        match = next((r for r in self.rooms if r.get('room_code') == room_code), None)
        if match:
            return match.get('id')
        return None

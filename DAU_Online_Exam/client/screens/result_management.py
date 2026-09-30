import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
from client.screens.admin_ui import module_header, toolbar, primary_button, secondary_button, panel, stat_card, empty_state, configure_tree

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class ResultManagementScreen(tk.Frame):
    def __init__(self, parent, client, current_user=None):
        super().__init__(parent, bg='#f5f5f5', padx=22, pady=22)
        self.parent = parent
        self.client = client
        self.current_user = current_user or {}
        self.pack(fill='both', expand=True)
        self.results = []
        self.build_ui()
        self.load_results()

    def build_ui(self):
        self.configure(bg='#edf2f7')
        header = tk.Frame(self, bg='#edf2f7', pady=6)
        header.pack(fill='x')
        tk.Label(header, text='EXAM PERFORMANCE', font=('Arial', 28, 'bold'), bg='#edf2f7', fg='#0f172a').pack(anchor='w')
        tk.Label(header, text='Theo dõi kết quả thi và xu hướng làm bài của sinh viên.', font=('Arial', 11), bg='#edf2f7', fg='#64748b').pack(anchor='w', pady=(4, 14))

        bar = tk.Frame(self, bg='#edf2f7')
        bar.pack(fill='x', pady=(0, 14))
        self.search_var = tk.StringVar()
        search_box = tk.Entry(bar, textvariable=self.search_var, width=40, font=('Arial', 11), relief='solid', bg='#ffffff', fg='#0f172a')
        search_box.pack(side='left', padx=(0, 8))
        tk.Button(bar, text='Tìm kiếm', command=self.load_results, bg='#7f1d2d', fg='white', font=('Arial', 10, 'bold'), padx=16, pady=8, relief='flat').pack(side='left')

        self.filter_frame = tk.Frame(self, bg='#edf2f7')
        self.filter_frame.pack(fill='x', pady=(0, 12))

        self.exam_var = tk.StringVar(value='all')
        self.room_var = tk.StringVar(value='all')
        self.status_var = tk.StringVar(value='all')
        self.date_var = tk.StringVar(value='all')

        for idx, (label, var, values) in enumerate([
            ('Kỳ thi', self.exam_var, ['all']),
            ('Phòng thi', self.room_var, ['all']),
            ('Trạng thái', self.status_var, ['all']),
            ('Ngày', self.date_var, ['all']),
        ]):
            tk.Label(self.filter_frame, text=label, bg='#edf2f7', fg='#475569', font=('Arial', 10, 'bold')).grid(row=0, column=idx * 2, padx=(0, 8), pady=4)
            ttk.Combobox(self.filter_frame, textvariable=var, values=values, state='readonly', width=16).grid(row=0, column=idx * 2 + 1, padx=(0, 18), pady=4)

        table_frame = tk.Frame(self, bg='#ffffff', padx=14, pady=14, highlightbackground='#e2e8f0', highlightthickness=1)
        table_frame.pack(fill='both', expand=True)
        self.tree = ttk.Treeview(table_frame, columns=('stt','student_code','full_name','class_name','exam_title','room_code','correct_answers','wrong_answers','score','duration','status'), show='headings', height=16)
        configure_tree(self.tree)
        for col, text in [('stt','STT'), ('student_code','Mã SV'), ('full_name','Họ tên'), ('class_name','Lớp'), ('exam_title','Kỳ thi'), ('room_code','Phòng'), ('correct_answers','Đúng'), ('wrong_answers','Sai'), ('score','Điểm'), ('duration','Thời gian'), ('status','Trạng thái')]:
            self.tree.heading(col, text=text)
        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<Double-1>', self.open_detail)

    def load_results(self):
        try:
            payload = {'action': 'get_all_results', 'role': self.current_user.get('role') or 'admin'}
            response = self.client.send_request(payload)
            if response.get('status') == 'success':
                self.results = response.get('results', [])
                self.render_table(self.results)
                return
            messagebox.showerror('Lỗi kết quả thi', response.get('message') or 'Không thể tải kết quả thi.')
        except Exception as exc:
            messagebox.showerror('Lỗi kết quả thi', str(exc))

    def render_table(self, rows):
        for child in self.tree.get_children():
            self.tree.delete(child)
        for idx, row in enumerate(rows, start=1):
            attempt_status = 'Hoàn thành'
            if row.get('status'):
                attempt_status = row.get('status')
            self.tree.insert('', 'end', values=(
                idx,
                row.get('student_code') or row.get('username') or '-',
                row.get('full_name') or '-',
                row.get('class_name') or '-',
                row.get('exam_title') or '-',
                row.get('room_code') or '-',
                row.get('correct_answers') or 0,
                row.get('wrong_answers') or 0,
                row.get('score') or 0,
                row.get('duration') or 0,
                attempt_status,
            ))

    def open_detail(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected[0], 'values')
        # item tuple includes display columns; not enough to know attempt_id, so ask server for the whole result set and pick by student/exam/order.
        # fallback: use row event static order by index currently selected.
        idx = int(item[0]) - 1
        if idx >= len(self.results):
            return
        row = self.results[idx]
        attempt_id = row.get('id')
        try:
            resp = self.client.send_request({'action': 'get_result', 'role': 'admin', 'attempt_id': attempt_id})
            if resp.get('status') == 'success':
                detail = resp.get('result', {})
                answers = resp.get('answers', [])
                panel = tk.Frame(self, bg='#ffffff', padx=20, pady=20)
                panel.pack(fill='both', expand=True)
                # clear the current content panel to render detail in same frame
                for child in self.winfo_children():
                    if child is not panel:
                        child.destroy()
                # build detail on a dedicated area
                tk.Label(panel, text='THÔNG TIN BÀI THI', font=('Arial', 19, 'bold'), bg='#ffffff', fg='#7F1D1D').pack(anchor='w')
                info = tk.Frame(panel, bg='#ffffff')
                info.pack(fill='x', pady=(12, 8))
                tk.Label(info, text=f"Sinh viên: {detail.get('full_name') or row.get('full_name') or '-'}", bg='#ffffff').grid(row=0, column=0, padx=(0, 20), pady=4, sticky='w')
                tk.Label(info, text=f"Mã SV: {detail.get('student_code') or row.get('student_code') or '-'}", bg='#ffffff').grid(row=1, column=0, padx=(0, 20), pady=4, sticky='w')
                tk.Label(info, text=f"Lớp: {detail.get('class_name') or row.get('class_name') or '-'}", bg='#ffffff').grid(row=2, column=0, padx=(0, 20), pady=4, sticky='w')
                tk.Label(info, text=f"Kỳ thi: {detail.get('exam_title') or row.get('exam_title') or '-'}", bg='#ffffff').grid(row=0, column=1, padx=(0, 20), pady=4, sticky='w')
                tk.Label(info, text=f"Phòng thi: {detail.get('room_code') or row.get('room_code') or '-'}", bg='#ffffff').grid(row=1, column=1, padx=(0, 20), pady=4, sticky='w')
                tk.Label(info, text=f"Điểm: {detail.get('score') or 0}", bg='#ffffff').grid(row=2, column=1, padx=(0, 20), pady=4, sticky='w')
                tk.Label(info, text=f"Số câu đúng: {detail.get('correct_answers') or 0}", bg='#ffffff').grid(row=3, column=0, padx=(0, 20), pady=4, sticky='w')
                tk.Label(info, text=f"Số câu sai: {detail.get('wrong_answers') or 0}", bg='#ffffff').grid(row=4, column=0, padx=(0, 20), pady=4, sticky='w')
                tk.Label(info, text=f"Bỏ trống: {detail.get('unanswered_questions') or 0}", bg='#ffffff').grid(row=5, column=0, padx=(0, 20), pady=4, sticky='w')
                tk.Label(info, text=f"Thời gian: {detail.get('duration') or 0}", bg='#ffffff').grid(row=3, column=1, padx=(0, 20), pady=4, sticky='w')
                tk.Button(panel, text='← QUAY LẠI KẾT QUẢ', command=self.back_to_results, bg='#7F1D1D', fg='white').pack(anchor='w', pady=(14, 0))

                answer_frame = tk.Frame(panel, bg='#ffffff')
                answer_frame.pack(fill='both', expand=True, pady=(16, 0))
                tk.Label(answer_frame, text='CHI TIẾT CÂU TRẢ LỜI', font=('Arial', 16, 'bold'), bg='#ffffff', fg='#7F1D1D').pack(anchor='w')
                for i, ans in enumerate(answers, start=1):
                    row = tk.Frame(answer_frame, bg='#ffffff', padx=10, pady=8)
                    row.pack(fill='x', pady=4)
                    tk.Label(row, text=f"Câu {i}", bg='#ffffff', fg='#1f2937', font=('Arial', 10, 'bold')).pack(side='left')
                    tk.Label(row, text=f"Đáp án SV: {ans.get('selected_answer') or '-'}", bg='#ffffff').pack(side='left', padx=(16, 0))
                    tk.Label(row, text=f"Đáp án đúng: {ans.get('correct_answer') or '-'}", bg='#ffffff').pack(side='left', padx=(16, 0))
                    status = '✓ Đúng' if int(ans.get('is_correct') or 0) == 1 else '✗ Sai'
                    color = '#15803d' if int(ans.get('is_correct') or 0) == 1 else '#b91c1c'
                    tk.Label(row, text=status, bg='#ffffff', fg=color, font=('Arial', 10, 'bold')).pack(side='left', padx=(16, 0))
            else:
                messagebox.showerror('Lỗi', resp.get('message') or 'Không thể tải chi tiết kết quả.')
        except Exception as exc:
            messagebox.showerror('Lỗi', str(exc))

    def back_to_results(self):
        for child in self.winfo_children():
            child.destroy()
        self.build_ui()
        self.load_results()

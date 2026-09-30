import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
from client.screens.admin_ui import module_header, panel, stat_card, empty_state, loading_state, configure_tree

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class StatisticsScreen(tk.Frame):
    def __init__(self, parent, client, current_user=None):
        super().__init__(parent, bg='#f5f5f5', padx=22, pady=22)
        self.parent = parent
        self.client = client
        self.current_user = current_user or {}
        self.pack(fill='both', expand=True)
        self.build_ui()
        self.load_statistics()

    def build_ui(self):
        self.configure(bg='#edf2f7')
        header = tk.Frame(self, bg='#edf2f7', pady=6)
        header.pack(fill='x')
        tk.Label(header, text='SYSTEM ANALYTICS', font=('Arial', 28, 'bold'), bg='#edf2f7', fg='#0f172a').pack(anchor='w')
        tk.Label(header, text='Theo dõi hiệu quả thi, tiến độ học tập và điểm số theo kỳ thi.', font=('Arial', 11), bg='#edf2f7', fg='#64748b').pack(anchor='w', pady=(4, 14))

        self.summary_frame = tk.Frame(self, bg='#edf2f7')
        self.summary_frame.pack(fill='x', pady=(0, 16))

        self.charts_frame = tk.Frame(self, bg='#ffffff', padx=16, pady=16, highlightbackground='#e2e8f0', highlightthickness=1)
        self.charts_frame.pack(fill='both', expand=True, pady=(0, 0))

        self.per_exam_tree = ttk.Treeview(self.charts_frame, columns=('exam','students','completed','not_done','avg','high','low'), show='headings', height=10)
        configure_tree(self.per_exam_tree)
        self.per_exam_tree.heading('exam', text='Kỳ thi')
        self.per_exam_tree.heading('students', text='Số sinh viên')
        self.per_exam_tree.heading('completed', text='Đã thi')
        self.per_exam_tree.heading('not_done', text='Chưa thi')
        self.per_exam_tree.heading('avg', text='Điểm TB')
        self.per_exam_tree.heading('high', text='Điểm cao nhất')
        self.per_exam_tree.heading('low', text='Điểm thấp nhất')
        self.per_exam_tree.pack(fill='x')

    def load_statistics(self):
        try:
            response = self.client.send_request({'action': 'get_statistics', 'role': self.current_user.get('role') or 'admin'})
            if response.get('status') == 'success':
                self.render_summary(response.get('statistics', {}))
                self.render_exam_stats(response.get('per_exam', []))
                return
            messagebox.showerror('Lỗi thống kê', response.get('message') or 'Không thể tải thống kê.')
        except Exception as exc:
            messagebox.showerror('Lỗi thống kê', str(exc))

    def render_summary(self, stats):
        for child in self.summary_frame.winfo_children():
            child.destroy()
        labels = [
            ('Tổng sinh viên', stats.get('total_students', 0)),
            ('Tổng kỳ thi', stats.get('total_exams', 0)),
            ('Tổng bài thi', stats.get('total_attempts', 0)),
            ('Tổng bài đã hoàn thành', stats.get('completed_attempts', 0)),
            ('Tổng bài đang thi', stats.get('active_attempts', 0)),
            ('Điểm trung bình', stats.get('average_score', 0)),
            ('Điểm cao nhất', stats.get('highest_score', 0)),
            ('Điểm thấp nhất', stats.get('lowest_score', 0)),
        ]
        for i, (label, value) in enumerate(labels):
            row = stat_card(self.summary_frame, '📈', label, value)
            row.grid(row=0, column=i, padx=8, pady=8, sticky='nsew')

    def render_exam_stats(self, per_exam):
        for child in self.per_exam_tree.get_children():
            self.per_exam_tree.delete(child)
        for row in per_exam:
            self.per_exam_tree.insert('', 'end', values=(
                row.get('title') or '-',
                row.get('student_count') or 0,
                row.get('completed') or 0,
                row.get('not_completed') or 0,
                row.get('average_score') or 0,
                row.get('highest_score') or 0,
                row.get('lowest_score') or 0,
            ))

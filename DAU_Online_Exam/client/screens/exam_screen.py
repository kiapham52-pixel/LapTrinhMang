import ctypes
import logging
import os
import re
import sys
import threading
import tkinter as tk
import uuid
from tkinter import messagebox, ttk

from client.screens.admin_ui import (
    module_header,
    toolbar,
    primary_button,
    secondary_button,
    panel,
    empty_state,
    loading_state,
    configure_tree
)

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )
    )
)


EXAM_STATES = (
    'NOT_STARTED',
    'IN_PROGRESS',
    'SUBMITTING',
    'SUBMITTED',
    'SHOWING_RESULT',
    'EXITING'
)

logger = logging.getLogger(__name__)


class ExamListWindow(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg='#eef3f6')

        self.app = parent.winfo_toplevel()
        self.client = getattr(self.app, 'client', None)
        self.current_user = getattr(
            self.app,
            'current_user',
            None
        ) or {}

        self.exam_rows = []
        self.subjects = []

        self.pack(
            fill='both',
            expand=True
        )

        self.build_ui()
        self.load_exams()

        if self.current_user.get('role') == 'admin':
            threading.Thread(
                target=self._subjects_worker,
                daemon=True
            ).start()

    def _subjects_worker(self):
        try:
            response = self.client.send_request({
                'action': 'get_subjects',
                'role': 'admin'
            })

            self.app.after(
                0,
                lambda: self.set_subjects(response)
            )

        except Exception as exc:
            logger.exception(
                '[EXAM] get_subjects_failed: %s',
                exc
            )

    def set_subjects(self, response):
        if response.get('status') == 'success':
            self.subjects = [
                subject.get('name')
                for subject in response.get('subjects', [])
            ]

    def build_ui(self):
        if self.current_user.get('role') == 'admin':
            self.build_admin_ui()
            return

        frame = tk.Frame(
            self,
            bg='#eef3f6',
            padx=20,
            pady=20
        )

        frame.pack(
            fill='both',
            expand=True
        )

        header = tk.Frame(
            frame,
            bg='#ffffff',
            padx=20,
            pady=16
        )

        header.pack(fill='x')

        tk.Label(
            header,
            text='Danh sách môn/kỳ thi',
            font=('Arial', 20, 'bold'),
            fg='#102a43',
            bg='#ffffff'
        ).pack(anchor='w')

        panel_frame = tk.Frame(
            frame,
            bg='#ffffff',
            padx=14,
            pady=14
        )

        panel_frame.pack(
            fill='both',
            expand=True,
            pady=(12, 0)
        )

        columns = (
            'id',
            'title',
            'description',
            'subject',
            'duration',
            'total_questions',
            'status'
        )

        headings = {
            'id': 'ID',
            'title': 'Tên kỳ thi',
            'description': 'Mô tả',
            'subject': 'Môn học',
            'duration': 'Thời lượng',
            'total_questions': 'Số câu',
            'status': 'Trạng thái'
        }

        widths = {
            'id': 50,
            'title': 180,
            'description': 260,
            'subject': 180,
            'duration': 90,
            'total_questions': 90,
            'status': 100
        }

        self.tree = ttk.Treeview(
            panel_frame,
            columns=columns,
            show='headings',
            height=16
        )

        for column in columns:
            self.tree.heading(
                column,
                text=headings[column]
            )

            self.tree.column(
                column,
                width=widths[column],
                anchor=(
                    'center'
                    if column in (
                        'id',
                        'duration',
                        'total_questions',
                        'status'
                    )
                    else 'w'
                )
            )

        yscroll = ttk.Scrollbar(
            panel_frame,
            orient='vertical',
            command=self.tree.yview
        )

        xscroll = ttk.Scrollbar(
            panel_frame,
            orient='horizontal',
            command=self.tree.xview
        )

        self.tree.configure(
            yscrollcommand=yscroll.set,
            xscrollcommand=xscroll.set
        )

        self.tree.pack(
            side='left',
            fill='both',
            expand=True
        )

        yscroll.pack(
            side='right',
            fill='y'
        )

        xscroll.pack(
            side='bottom',
            fill='x'
        )

        btn_frame = tk.Frame(
            frame,
            bg='#eef3f6',
            pady=12
        )

        btn_frame.pack(fill='x')

        tk.Button(
            btn_frame,
            text='Vào thi',
            command=self.open_selected_exam,
            width=14,
            bg='#0d6efd',
            fg='white'
        ).pack(side='left')

        tk.Button(
            btn_frame,
            text='Làm mới',
            command=self.load_exams,
            width=12
        ).pack(
            side='left',
            padx=(8, 0)
        )

    def load_exams(self):
        threading.Thread(
            target=self.request_exams_worker,
            daemon=True
        ).start()

    def request_exams_worker(self):
        try:
            response = self.client.send_request({
                'action': 'get_exams'
            })

            self.app.after(
                0,
                lambda: self.render_exams(response)
            )

        except Exception as exc:
            logger.exception(
                '[EXAM] get_exams_failed: %s',
                exc
            )

            self.app.after(
                0,
                lambda: messagebox.showerror(
                    'Lỗi',
                    str(exc)
                )
            )

    def render_exams(self, response):
        if response.get('status') != 'success':
            messagebox.showerror(
                'Lỗi',
                response.get(
                    'message',
                    'Không lấy được kỳ thi'
                )
            )
            return

        tree = (
            self.exam_tree
            if self.current_user.get('role') == 'admin'
            else self.tree
        )

        for item in tree.get_children():
            tree.delete(item)

        self.exam_rows = response.get(
            'exams',
            []
        )

        if self.current_user.get('role') == 'admin':
            for exam in self.exam_rows:
                tree.insert(
                    '',
                    'end',
                    values=(
                        exam.get('id'),
                        exam.get('title'),
                        exam.get('subject') or 'Chưa có môn',
                        exam.get('total_questions') or 0,
                        exam.get('duration') or 0,
                        exam.get('status') or 'active'
                    )
                )

            return

        for exam in self.exam_rows:
            tree.insert(
                '',
                'end',
                values=(
                    exam.get('id'),
                    exam.get('title'),
                    exam.get('description') or '',
                    exam.get('subject') or 'Chưa có môn',
                    exam.get('duration') or 0,
                    exam.get('total_questions') or 0,
                    exam.get('status') or 'active'
                )
            )

    def open_selected_exam(self):
        if self.current_user.get('role') == 'admin':
            selected = self.exam_tree.selection()

            if not selected:
                messagebox.showwarning(
                    'Chưa chọn đề',
                    'Vui lòng chọn một đề thi.'
                )
                return

            self.current_exam_id = int(
                self.exam_tree.item(
                    selected[0],
                    'values'
                )[0]
            )

            self.load_exam_questions()
            return

        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                'Chưa chọn kỳ thi',
                'Vui lòng chọn một kỳ thi để bắt đầu.'
            )
            return

        exam_id = int(
            self.tree.item(
                selected[0],
                'values'
            )[0]
        )

        payload = {
            'action': 'start_exam',
            'exam_id': exam_id,
            'user_id': self.current_user.get('id'),
            'role': self.current_user.get('role')
        }

        threading.Thread(
            target=self.start_exam_worker,
            args=(payload,),
            daemon=True
        ).start()

    def start_exam_worker(self, payload):
        try:
            response = self.client.send_request(
                payload
            )

            if (
                response.get('status') == 'success'
                and response.get('exam')
            ):
                self.app.after(
                    0,
                    lambda: ExamWindow(
                        self.app,
                        response['exam'],
                        self.current_user,
                        self.client
                    )
                )
            else:
                self.app.after(
                    0,
                    lambda: messagebox.showerror(
                        'Lỗi thi',
                        response.get('message')
                        or 'Không thể bắt đầu kỳ thi'
                    )
                )

        except Exception as exc:
            logger.exception(
                '[EXAM] start_exam_failed: %s',
                exc
            )

            self.app.after(
                0,
                lambda: messagebox.showerror(
                    'Lỗi thi',
                    str(exc)
                )
            )

    def build_admin_ui(self):
        frame = tk.Frame(
            self,
            bg='#f5f5f5',
            padx=20,
            pady=20
        )

        frame.pack(
            fill='both',
            expand=True
        )

        module_header(
            frame,
            '📝',
            'QUẢN LÝ ĐỀ THI',
            'Xây dựng đề thi từ ngân hàng câu hỏi.'
        )

        bar = toolbar(frame)

        primary_button(
            bar,
            '+ Tạo đề thi',
            self.create_exam
        ).pack(side='left')

        secondary_button(
            bar,
            'Sửa đề',
            self.edit_exam
        ).pack(
            side='left',
            padx=8
        )

        secondary_button(
            bar,
            'Xóa đề',
            self.delete_exam
        ).pack(side='left')

        secondary_button(
            bar,
            'Làm mới',
            self.load_exams
        ).pack(
            side='left',
            padx=8
        )

        primary_button(
            bar,
            'Quản lý câu hỏi',
            self.open_selected_exam
        ).pack(side='left')

        table_panel = panel(
            frame,
            10
        )

        table_panel.pack(
            fill='both',
            expand=True
        )

        columns = (
            'id',
            'title',
            'subject',
            'questions',
            'duration',
            'status'
        )

        self.exam_tree = ttk.Treeview(
            table_panel,
            columns=columns,
            show='headings',
            selectmode='browse'
        )

        configure_tree(
            self.exam_tree
        )

        for col, text, width in [
            ('id', 'ID', 60),
            ('title', 'Tên đề', 260),
            ('subject', 'Môn', 180),
            ('questions', 'Số câu', 80),
            ('duration', 'Phút', 80),
            ('status', 'Trạng thái', 100)
        ]:
            self.exam_tree.heading(
                col,
                text=text
            )

            self.exam_tree.column(
                col,
                width=width
            )

        self.exam_tree.pack(
            side='left',
            fill='both',
            expand=True
        )

        exam_scroll = ttk.Scrollbar(
            table_panel,
            orient='vertical',
            command=self.exam_tree.yview
        )

        exam_scroll.pack(
            side='right',
            fill='y'
        )

        self.exam_tree.configure(
            yscrollcommand=exam_scroll.set
        )

        self.current_exam_id = None

        self.question_panel = tk.Frame(
            frame,
            bg='white',
            padx=12,
            pady=12
        )

        self.question_panel.pack(
            fill='both',
            expand=True,
            pady=(12, 0)
        )

        tk.Label(
            self.question_panel,
            text='Chọn một đề để xem và thêm câu hỏi từ ngân hàng.',
            bg='white',
            fg='#6b7280'
        ).pack(anchor='w')

    def create_exam(self):
        for child in self.question_panel.winfo_children():
            child.destroy()

        form = tk.Frame(
            self.question_panel,
            bg='white'
        )

        form.pack(fill='x')

        tk.Label(
            form,
            text='TẠO ĐỀ THI',
            font=('Arial', 15, 'bold'),
            bg='white',
            fg='#7F1D1D'
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky='w',
            pady=(0, 10)
        )

        fields = {}

        tk.Label(
            form,
            text='Môn học',
            bg='white'
        ).grid(
            row=4,
            column=0,
            padx=10,
            pady=8,
            sticky='w'
        )

        subject_var = tk.StringVar()

        subject_combo = ttk.Combobox(
            form,
            textvariable=subject_var,
            values=self.subjects,
            state='readonly',
            width=38
        )

        subject_combo.grid(
            row=4,
            column=1,
            padx=10,
            pady=8
        )

        if self.subjects:
            subject_combo.current(0)

        for index, (
            key,
            label
        ) in enumerate(
            (
                ('title', 'Tên đề'),
                ('description', 'Mô tả'),
                ('duration', 'Thời lượng (phút)')
            ),
            start=1
        ):
            tk.Label(
                form,
                text=label,
                bg='white'
            ).grid(
                row=index,
                column=0,
                padx=10,
                pady=8,
                sticky='w'
            )

            fields[key] = tk.Entry(
                form,
                width=40
            )

            fields[key].grid(
                row=index,
                column=1,
                padx=10,
                pady=8
            )

        fields['duration'].insert(
            0,
            '30'
        )

        def save():
            response = self.client.send_request({
                'action': 'create_exam',
                'role': 'admin',
                'title': fields['title'].get(),
                'description': fields['description'].get(),
                'duration': fields['duration'].get(),
                'subject': subject_var.get()
            })

            if response.get('status') == 'success':
                messagebox.showinfo(
                    'Thành công',
                    f"Đã tạo đề ID {response.get('exam_id')}"
                )

                for child in self.question_panel.winfo_children():
                    child.destroy()

                self.load_exams()

            else:
                messagebox.showerror(
                    'Không thể tạo đề',
                    response.get('message')
                    or 'Lỗi server'
                )

        tk.Button(
            form,
            text='Lưu đề',
            command=save,
            bg='#7F1D1D',
            fg='white'
        ).grid(
            row=5,
            column=1,
            pady=10,
            sticky='e'
        )

    def edit_exam(self):
        selected = self.exam_tree.selection()

        if not selected:
            messagebox.showwarning(
                'Chưa chọn đề',
                'Vui lòng chọn đề cần sửa.'
            )
            return

        values = self.exam_tree.item(
            selected[0],
            'values'
        )

        for child in self.question_panel.winfo_children():
            child.destroy()

        form = tk.Frame(
            self.question_panel,
            bg='white'
        )

        form.pack(fill='x')

        fields = {}

        for index, (
            key,
            label,
            value
        ) in enumerate(
            (
                ('title', 'Tên đề', values[1]),
                ('description', 'Mô tả', ''),
                ('duration', 'Thời lượng (phút)', values[4])
            ),
            start=1
        ):
            tk.Label(
                form,
                text=label,
                bg='white'
            ).grid(
                row=index,
                column=0,
                padx=10,
                pady=8,
                sticky='w'
            )

            fields[key] = tk.Entry(
                form,
                width=40
            )

            fields[key].insert(
                0,
                value
            )

            fields[key].grid(
                row=index,
                column=1,
                padx=10,
                pady=8
            )

        def save():
            response = self.client.send_request({
                'action': 'update_exam',
                'role': 'admin',
                'id': int(values[0]),
                'title': fields['title'].get(),
                'description': fields['description'].get(),
                'duration': fields['duration'].get(),
                'total_questions': int(values[3]),
                'status': values[5]
            })

            if response.get('status') == 'success':
                self.load_exams()
                self.load_exam_questions()

            else:
                messagebox.showerror(
                    'Không thể sửa đề',
                    response.get('message')
                    or 'Lỗi server'
                )

        tk.Button(
            form,
            text='Lưu thay đổi',
            command=save,
            bg='#7F1D1D',
            fg='white'
        ).grid(
            row=4,
            column=1,
            pady=10,
            sticky='e'
        )

    def delete_exam(self):
        selected = self.exam_tree.selection()

        if not selected:
            messagebox.showwarning(
                'Chưa chọn đề',
                'Vui lòng chọn đề cần xóa.'
            )
            return

        values = self.exam_tree.item(
            selected[0],
            'values'
        )

        if not messagebox.askyesno(
            'Xác nhận',
            f"Xóa đề '{values[1]}' và các liên kết câu hỏi?"
        ):
            return

        response = self.client.send_request({
            'action': 'delete_exam',
            'role': 'admin',
            'id': int(values[0])
        })

        if response.get('status') == 'success':
            self.current_exam_id = None
            self.load_exams()

            for child in self.question_panel.winfo_children():
                child.destroy()

            tk.Label(
                self.question_panel,
                text='Chọn một đề để xem và thêm câu hỏi từ ngân hàng.',
                bg='white',
                fg='#6b7280'
            ).pack(anchor='w')

        else:
            messagebox.showerror(
                'Không thể xóa đề',
                response.get('message')
                or 'Lỗi server'
            )

    def load_exam_questions(self):
        response = self.client.send_request({
            'action': 'get_exam_questions',
            'role': 'admin',
            'exam_id': self.current_exam_id
        })

        if response.get('status') != 'success':
            messagebox.showerror(
                'Lỗi',
                response.get('message')
                or 'Không tải được câu hỏi của đề'
            )
            return

        for child in self.question_panel.winfo_children():
            child.destroy()

        exam = next(
            (
                item
                for item in self.exam_rows
                if item.get('id') == self.current_exam_id
            ),
            {}
        )

        tk.Label(
            self.question_panel,
            text=(
                f"Đề: {exam.get('title', '')} | "
                f"ID: {self.current_exam_id} | "
                f"Số câu: {len(response.get('questions', []))}"
            ),
            font=('Arial', 14, 'bold'),
            bg='white',
            fg='#7F1D1D'
        ).pack(anchor='w')

        self.current_questions_tree = ttk.Treeview(
            self.question_panel,
            columns=(
                'id',
                'content',
                'subject',
                'difficulty',
                'answer'
            ),
            show='headings',
            height=6
        )

        for col, text, width in [
            ('id', 'ID', 50),
            ('content', 'Nội dung', 360),
            ('subject', 'Môn', 140),
            ('difficulty', 'Độ khó', 100),
            ('answer', 'Đúng', 60)
        ]:
            self.current_questions_tree.heading(
                col,
                text=text
            )

            self.current_questions_tree.column(
                col,
                width=width
            )

        self.current_questions_tree.pack(
            fill='both',
            expand=True
        )

        self.current_exam_questions = response.get(
            'questions',
            []
        )

        for question in self.current_exam_questions:
            self.current_questions_tree.insert(
                '',
                'end',
                values=(
                    question.get('id'),
                    question.get('content'),
                    question.get('subject'),
                    question.get('difficulty'),
                    question.get('correct_answer')
                )
            )

        button_row = tk.Frame(
            self.question_panel,
            bg='white'
        )

        button_row.pack(
            fill='x',
            pady=8
        )

        tk.Button(
            button_row,
            text='+ Thêm từ ngân hàng',
            command=self.open_question_picker,
            bg='#991B1B',
            fg='white'
        ).pack(side='left')

        tk.Button(
            button_row,
            text='Xóa khỏi đề',
            command=self.remove_selected_question,
            bg='#dc2626',
            fg='white'
        ).pack(
            side='left',
            padx=8
        )

    def open_question_picker(self):
        response = self.client.send_request({
            'action': 'get_questions',
            'role': 'admin'
        })

        if response.get('status') != 'success':
            messagebox.showerror(
                'Lỗi',
                response.get('message')
                or 'Không tải được ngân hàng câu hỏi'
            )
            return

        existing = {
            question.get('id')
            for question in getattr(
                self,
                'current_exam_questions',
                []
            )
        }

        exam = next(
            (
                item
                for item in self.exam_rows
                if item.get('id') == self.current_exam_id
            ),
            {}
        )

        exam_subject = exam.get('subject') or ''

        for child in self.question_panel.winfo_children():
            child.destroy()

        picker = tk.Frame(
            self.question_panel,
            bg='white'
        )

        picker.pack(
            fill='both',
            expand=True
        )

        tk.Label(
            picker,
            text='THÊM CÂU HỎI TỪ NGÂN HÀNG',
            font=('Arial', 15, 'bold'),
            bg='white',
            fg='#7F1D1D'
        ).pack(anchor='w')

        canvas = tk.Canvas(
            picker,
            bg='white',
            highlightthickness=0
        )

        scroll = ttk.Scrollbar(
            picker,
            orient='vertical',
            command=canvas.yview
        )

        cards = tk.Frame(
            canvas,
            bg='white'
        )

        canvas_window = canvas.create_window(
            (0, 0),
            window=cards,
            anchor='nw'
        )

        canvas.configure(
            yscrollcommand=scroll.set
        )

        canvas.pack(
            side='left',
            fill='both',
            expand=True,
            padx=(0, 8),
            pady=10
        )

        scroll.pack(
            side='right',
            fill='y',
            pady=10
        )

        canvas.bind(
            '<MouseWheel>',
            lambda event: canvas.yview_scroll(
                -int(event.delta / 120),
                'units'
            )
        )

        canvas.bind(
            '<Prior>',
            lambda _event: canvas.yview_scroll(
                -1,
                'pages'
            )
        )

        canvas.bind(
            '<Next>',
            lambda _event: canvas.yview_scroll(
                1,
                'pages'
            )
        )

        cards.bind(
            '<Configure>',
            lambda _event: canvas.configure(
                scrollregion=canvas.bbox('all')
            )
        )

        canvas.bind(
            '<Configure>',
            lambda event: canvas.itemconfigure(
                canvas_window,
                width=event.width
            )
        )

        selected_vars = {}

        for question in response.get(
            'questions',
            []
        ):
            if (
                question.get('id') not in existing
                and (
                    not exam_subject
                    or question.get('subject') == exam_subject
                )
            ):
                question_id = question.get('id')

                selected_vars[question_id] = tk.BooleanVar(
                    value=False
                )

                card = tk.Frame(
                    cards,
                    bg='#fff7f7',
                    padx=14,
                    pady=12,
                    highlightbackground='#e5e7eb',
                    highlightthickness=1
                )

                card.pack(
                    fill='x',
                    pady=6,
                    padx=4
                )

                top = tk.Frame(
                    card,
                    bg='#fff7f7'
                )

                top.pack(fill='x')

                tk.Checkbutton(
                    top,
                    text=f'Câu hỏi {question_id}',
                    variable=selected_vars[question_id],
                    bg='#fff7f7',
                    fg='#7F1D1D',
                    font=('Arial', 10, 'bold')
                ).pack(side='left')

                tk.Label(
                    top,
                    text=question.get('difficulty')
                    or 'Chưa phân loại',
                    bg='#dcfce7',
                    fg='#166534',
                    padx=8,
                    pady=2
                ).pack(side='right')

                tk.Label(
                    card,
                    text=question.get('content') or '',
                    bg='#fff7f7',
                    fg='#1f2937',
                    font=('Arial', 11, 'bold'),
                    wraplength=720,
                    justify='left'
                ).pack(
                    anchor='w',
                    pady=(8, 5)
                )

                for letter, key in (
                    ('A', 'option_a'),
                    ('B', 'option_b'),
                    ('C', 'option_c'),
                    ('D', 'option_d')
                ):
                    option_text = self.clean_option_text(
                        question.get(key)
                    )

                    tk.Label(
                        card,
                        text=f'{letter}. {option_text}',
                        bg='#fff7f7',
                        fg='#4b5563',
                        wraplength=720,
                        justify='left'
                    ).pack(
                        anchor='w',
                        padx=24,
                        pady=1
                    )

                tk.Label(
                    card,
                    text=(
                        f"✓ Đáp án đúng: "
                        f"{question.get('correct_answer') or '-'}    "
                        f"📚 {question.get('subject') or '-'}"
                    ),
                    bg='#fff7f7',
                    fg='#15803d',
                    font=('Arial', 9, 'bold')
                ).pack(
                    anchor='w',
                    pady=(7, 0)
                )

        def add_selected():
            ids = [
                question_id
                for question_id, variable
                in selected_vars.items()
                if variable.get()
            ]

            if not ids:
                messagebox.showwarning(
                    'Chưa chọn câu hỏi',
                    'Vui lòng chọn ít nhất một câu hỏi.'
                )
                return

            result = self.client.send_request({
                'action': 'add_exam_questions',
                'role': 'admin',
                'exam_id': self.current_exam_id,
                'question_ids': ids
            })

            if result.get('status') == 'success':
                messagebox.showinfo(
                    'Thành công',
                    result.get('message')
                )

                self.load_exam_questions()
                self.load_exams()

            else:
                messagebox.showerror(
                    'Không thể thêm câu hỏi',
                    result.get('message')
                    or 'Lỗi server'
                )

        button_row = tk.Frame(
            picker,
            bg='white'
        )

        button_row.pack(
            fill='x',
            pady=8
        )

        tk.Button(
            button_row,
            text='Thêm câu hỏi vào đề',
            command=add_selected,
            bg='#7F1D1D',
            fg='white'
        ).pack(side='left')

        tk.Button(
            button_row,
            text='Hủy',
            command=self.load_exam_questions
        ).pack(
            side='left',
            padx=8
        )

    def remove_selected_question(self):
        selected = self.current_questions_tree.selection()

        if not selected:
            messagebox.showwarning(
                'Chưa chọn',
                'Vui lòng chọn câu hỏi cần xóa khỏi đề.'
            )
            return

        question_id = int(
            self.current_questions_tree.item(
                selected[0],
                'values'
            )[0]
        )

        response = self.client.send_request({
            'action': 'remove_exam_question',
            'role': 'admin',
            'exam_id': self.current_exam_id,
            'question_id': question_id
        })

        if response.get('status') == 'success':
            self.load_exam_questions()
            self.load_exams()

        else:
            messagebox.showerror(
                'Không thể xóa',
                response.get('message')
                or 'Lỗi server'
            )

    @staticmethod
    def clean_option_text(value):
        text = str(value or '').strip()

        pattern = r'^\s*[A-Da-d]\s*[\.\):\-–—]\s*'

        while re.match(pattern, text):
            text = re.sub(
                pattern,
                '',
                text,
                count=1
            )

        return text.strip()


class ExamWindow(tk.Frame):
    def __init__(
        self,
        parent,
        exam,
        current_user,
        client,
        student_dashboard=None
    ):
        super().__init__(
            parent,
            bg='#eef3f6'
        )

        self.root = parent.winfo_toplevel()
        self.client = client
        self.current_user = current_user
        self.student_dashboard = student_dashboard
        self.exam = exam

        # =========================================================
        # DỮ LIỆU
        # =========================================================

        self.questions = (
            exam.get('questions', [])
            or []
        )

        self.current_index = 0

        self.answer_var = tk.StringVar(
            value=''
        )

        self.question_state = {
            q.get('id'): {
                'selected_answer': None,
                'flagged': False,
                'lifeline_used': False,
                'visible_options': None
            }
            for q in self.questions
        }

        self.submission_token = str(
            uuid.uuid4()
        )

        self.exam_state = 'IN_PROGRESS'

        # 50/50
        self.lifeline_remaining = 2
        self.lifeline_request_pending = False

        # TIMER
        self.time_left_seconds = int(
            (exam.get('duration') or 0) * 60
        )

        self.timer_job = None
        self.focus_job = None

        # =========================================================
        # FULLSCREEN
        # =========================================================

        if self.current_user.get('role') == 'student':
            enter_fullscreen = getattr(
                self.root,
                'enter_exam_fullscreen',
                None
            )

            if enter_fullscreen:
                enter_fullscreen()
            else:
                self.root.attributes(
                    '-fullscreen',
                    True
                )

                self.root.resizable(
                    False,
                    False
                )

                self.root.update_idletasks()

        # =========================================================
        # UI
        # =========================================================

        self.build_ui()

        self.root.protocol(
            'WM_DELETE_WINDOW',
            self.handle_root_close
        )

        self.root.bind(
            '<Alt-F4>',
            self.handle_alt_f4
        )

        self.root.resizable(
            False,
            False
        )

        self.pack(
            fill='both',
            expand=True
        )

        self.bind(
            '<Configure>',
            self.resize_question_text
        )

        self.start_timer()
        self.start_focus_monitor()
        self.render_question()

    # =============================================================
    # OPTION TEXT
    # =============================================================

    @staticmethod
    def clean_option_text(value):
        """
        Làm sạch A./B./C./D. đã có sẵn trong DB.

        Ví dụ:
        A. Paris
        -> Paris

        A. A. Paris
        -> Paris

        B) Hà Nội
        -> Hà Nội
        """

        text = str(value or '').strip()

        pattern = r'^\s*[A-Da-d]\s*[\.\):\-–—]\s*'

        while re.match(pattern, text):
            text = re.sub(
                pattern,
                '',
                text,
                count=1
            )

        return text.strip()

    # =============================================================
    # BUILD UI
    # =============================================================

    def build_ui(self):
        self.configure(
            bg='#edf2f7'
        )

        shell = tk.Frame(
            self,
            bg='#edf2f7',
            padx=18,
            pady=18
        )

        shell.pack(
            fill='both',
            expand=True
        )

        # =========================================================
        # TOP BAR
        # =========================================================

        topbar = tk.Frame(
            shell,
            bg='#ffffff',
            padx=22,
            pady=16,
            highlightbackground='#e2e8f0',
            highlightthickness=1
        )

        topbar.pack(
            fill='x'
        )

        tk.Label(
            topbar,
            text='DAU EXAM',
            font=('Arial', 22, 'bold'),
            bg='#ffffff',
            fg='#0f172a'
        ).pack(
            side='left'
        )

        tk.Label(
            topbar,
            text=self.exam.get('title', ''),
            font=('Arial', 11, 'bold'),
            bg='#ffffff',
            fg='#7f1d2d'
        ).pack(
            side='left',
            padx=(18, 0)
        )

        timer_card = tk.Frame(
            topbar,
            bg='#fff7f7',
            padx=16,
            pady=8,
            highlightbackground='#fecaca',
            highlightthickness=1
        )

        timer_card.pack(
            side='right'
        )

        tk.Label(
            timer_card,
            text='TIME LEFT',
            font=('Arial', 9, 'bold'),
            bg='#fff7f7',
            fg='#7f1d2d'
        ).pack()

        self.timer_label = tk.Label(
            timer_card,
            text='00:00',
            font=('Arial', 18, 'bold'),
            bg='#fff7f7',
            fg='#7f1d2d'
        )

        self.timer_label.pack()

        # =========================================================
        # BODY
        # =========================================================

        body = tk.Frame(
            shell,
            bg='#edf2f7'
        )

        body.pack(
            fill='both',
            expand=True,
            pady=(16, 0)
        )

        # =========================================================
        # MAIN QUESTION
        # =========================================================

        left = tk.Frame(
            body,
            bg='#ffffff',
            padx=24,
            pady=22,
            highlightbackground='#e2e8f0',
            highlightthickness=1
        )

        left.pack(
            side='left',
            fill='both',
            expand=True
        )

        self.question_no = tk.Label(
            left,
            text='',
            font=('Arial', 12, 'bold'),
            fg='#7f1d2d',
            bg='#ffffff'
        )

        self.question_no.pack(
            anchor='w',
            pady=(0, 14)
        )

        self.question_text = tk.Label(
            left,
            text='',
            justify='left',
            wraplength=740,
            font=('Arial', 18, 'bold'),
            fg='#111827',
            bg='#ffffff'
        )

        self.question_text.pack(
            anchor='w',
            pady=(0, 18)
        )

        # =========================================================
        # ANSWERS
        # =========================================================

        option_frame = tk.Frame(
            left,
            bg='#ffffff'
        )

        option_frame.pack(
            fill='x'
        )

        self.option_rows = []
        self.option_buttons = []
        self.option_labels = []

        for letter in (
            'A',
            'B',
            'C',
            'D'
        ):
            row = tk.Frame(
                option_frame,
                bg='#ffffff',
                padx=8,
                pady=8,
                highlightbackground='#e5e7eb',
                highlightthickness=1
            )

            row.pack(
                fill='x',
                pady=5
            )

            # -----------------------------------------------------
            # NÚT A/B/C/D
            # -----------------------------------------------------

            button = tk.Radiobutton(
                row,
                text=f'{letter}.',
                variable=self.answer_var,
                value=letter,
                bg='#ffffff',
                activebackground='#fff1f2',
                fg='#7f1d2d',
                activeforeground='#7f1d2d',
                font=('Arial', 11, 'bold'),
                command=self.save_current_answer,
                indicatoron=False,
                selectcolor='#fff1f2',
                bd=0,
                highlightthickness=0,
                width=4,
                padx=6,
                pady=8,
                cursor='hand2'
            )

            button.pack(
                side='left',
                padx=(0, 10)
            )

            # -----------------------------------------------------
            # NỘI DUNG ĐÁP ÁN
            # -----------------------------------------------------

            label = tk.Label(
                row,
                text='',
                bg='#ffffff',
                fg='#475569',
                font=('Arial', 12),
                wraplength=660,
                justify='left',
                anchor='w',
                cursor='hand2'
            )

            label.pack(
                side='left',
                fill='x',
                expand=True,
                anchor='w'
            )

            # Bấm trực tiếp vào chữ đáp án cũng chọn được
            label.bind(
                '<Button-1>',
                lambda event, value=letter:
                    self.select_answer(value)
            )

            row.bind(
                '<Button-1>',
                lambda event, value=letter:
                    self.select_answer(value)
            )

            self.option_rows.append(
                row
            )

            self.option_buttons.append(
                button
            )

            self.option_labels.append(
                label
            )

        # =========================================================
        # ACTION BAR
        # =========================================================

        action_bar = tk.Frame(
            left,
            bg='#ffffff',
            pady=18
        )

        action_bar.pack(
            fill='x'
        )

        self.flag_button = tk.Button(
            action_bar,
            text='⭐ Review later',
            command=self.toggle_flag,
            bg='#fff7ec',
            fg='#b45309',
            font=('Arial', 10, 'bold'),
            relief='flat',
            padx=14,
            pady=10,
            cursor='hand2'
        )

        self.flag_button.pack(
            side='left',
            padx=(0, 8)
        )

        self.lifeline_button = tk.Button(
            action_bar,
            text='🧠 50/50',
            command=self.use_lifeline,
            bg='#fdf2f8',
            fg='#9f1239',
            font=('Arial', 10, 'bold'),
            relief='flat',
            padx=14,
            pady=10,
            cursor='hand2'
        )

        self.lifeline_button.pack(
            side='left',
            padx=(0, 8)
        )

        tk.Button(
            action_bar,
            text='← Previous',
            command=self.prev_question,
            bg='#e2e8f0',
            fg='#0f172a',
            font=('Arial', 10, 'bold'),
            relief='flat',
            padx=12,
            pady=10,
            cursor='hand2'
        ).pack(
            side='left',
            padx=(0, 8)
        )

        tk.Button(
            action_bar,
            text='Next →',
            command=self.next_question,
            bg='#7f1d2d',
            fg='white',
            font=('Arial', 10, 'bold'),
            relief='flat',
            padx=14,
            pady=10,
            cursor='hand2'
        ).pack(
            side='left',
            padx=(0, 8)
        )

        self.submit_button = tk.Button(
            action_bar,
            text='Submit Exam',
            command=self.submit_exam,
            bg='#dc2626',
            fg='white',
            font=('Arial', 10, 'bold'),
            relief='flat',
            padx=18,
            pady=10,
            cursor='hand2'
        )

        self.submit_button.pack(
            side='right'
        )

        # =========================================================
        # RIGHT NAVIGATOR
        # =========================================================

        right = tk.Frame(
            body,
            bg='#ffffff',
            padx=18,
            pady=18,
            highlightbackground='#e2e8f0',
            highlightthickness=1
        )

        right.pack(
            side='right',
            fill='y'
        )

        tk.Label(
            right,
            text='QUESTION NAVIGATOR',
            font=('Arial', 11, 'bold'),
            bg='#ffffff',
            fg='#475569'
        ).pack(
            anchor='w',
            pady=(0, 12)
        )

        progress = tk.Frame(
            right,
            bg='#ffffff'
        )

        progress.pack(
            fill='x',
            pady=(0, 12)
        )

        self.progress_var = tk.StringVar(
            value='0%'
        )

        tk.Label(
            progress,
            text='Progress',
            font=('Arial', 10),
            bg='#ffffff',
            fg='#64748b'
        ).pack(
            anchor='w'
        )

        tk.Label(
            progress,
            textvariable=self.progress_var,
            font=('Arial', 11, 'bold'),
            bg='#ffffff',
            fg='#7f1d2d'
        ).pack(
            anchor='w',
            pady=(2, 6)
        )

        self.progress_bar = tk.Canvas(
            progress,
            width=180,
            height=10,
            bg='#ffffff',
            highlightthickness=0
        )

        self.progress_bar.pack(
            fill='x'
        )

        self.progress_fill = (
            self.progress_bar.create_rectangle(
                0,
                0,
                0,
                10,
                fill='#7f1d2d',
                outline=''
            )
        )

        # =========================================================
        # LEGEND
        # =========================================================

        legend = tk.Frame(
            right,
            bg='#ffffff'
        )

        legend.pack(
            fill='x',
            pady=(8, 12)
        )

        for label, color in [
            ('Answered', '#7f1d2d'),
            ('Review', '#f59e0b'),
            ('Current', '#2563eb'),
            ('Unanswered', '#e2e8f0')
        ]:
            row = tk.Frame(
                legend,
                bg='#ffffff'
            )

            row.pack(
                fill='x',
                pady=2
            )

            tk.Label(
                row,
                text='●',
                font=('Arial', 12),
                bg='#ffffff',
                fg=color
            ).pack(
                side='left'
            )

            tk.Label(
                row,
                text=label,
                bg='#ffffff',
                fg='#475569',
                font=('Arial', 10)
            ).pack(
                side='left',
                padx=(8, 0)
            )

        # =========================================================
        # QUESTION GRID
        # =========================================================

        self.q_grid = tk.Frame(
            right,
            bg='#ffffff'
        )

        self.q_grid.pack(
            fill='both',
            expand=True
        )

        self.nav_buttons = []

        for index in range(
            len(self.questions)
        ):
            button = tk.Button(
                self.q_grid,
                text=str(index + 1),
                width=4,
                height=1,
                command=lambda idx=index:
                    self.jump_to(idx),
                bg='#f8fafc',
                fg='#0f172a',
                font=('Arial', 10, 'bold'),
                relief='flat',
                cursor='hand2'
            )

            button.grid(
                row=index // 6,
                column=index % 6,
                padx=4,
                pady=4
            )

            self.nav_buttons.append(
                button
            )

        self.update_progress_bar()

    # =============================================================
    # SELECT ANSWER
    # =============================================================

    def select_answer(self, letter):
        if self.exam_state != 'IN_PROGRESS':
            return

        if not self.questions:
            return

        question = self.questions[
            self.current_index
        ]

        qid = question.get('id')

        if qid not in self.question_state:
            self.question_state[qid] = {
                'selected_answer': None,
                'flagged': False,
                'lifeline_used': False,
                'visible_options': None
            }

        state = self.question_state[qid]

        visible_options = state.get(
            'visible_options'
        )

        if (
            visible_options is not None
            and letter not in visible_options
        ):
            return

        self.answer_var.set(
            letter
        )

        self.question_state[qid][
            'selected_answer'
        ] = letter

        self.update_option_visuals()
        self.refresh_grid_colors()
        self.update_progress_bar()

    # =============================================================
    # RENDER QUESTION
    # =============================================================

    def render_question(self):
        if not self.questions:
            return

        question = self.questions[
            self.current_index
        ]

        qid = question.get('id')

        if qid not in self.question_state:
            self.question_state[qid] = {
                'selected_answer': None,
                'flagged': False,
                'lifeline_used': False,
                'visible_options': None
            }

        state = self.question_state[qid]

        self.question_no.config(
            text=(
                f'QUESTION '
                f'{self.current_index + 1} / '
                f'{len(self.questions)}'
            )
        )

        self.question_text.config(
            text=(
                question.get('question_text')
                or question.get('content')
                or ''
            )
        )

        state_options = state.get(
            'visible_options'
        )

        option_keys = (
            'option_a',
            'option_b',
            'option_c',
            'option_d'
        )

        letters = (
            'A',
            'B',
            'C',
            'D'
        )

        for letter, button, label, row, key in zip(
            letters,
            self.option_buttons,
            self.option_labels,
            self.option_rows,
            option_keys
        ):
            visible = (
                state_options is None
                or letter in state_options
            )

            raw_text = (
                question.get(key)
                or ''
            )

            option_text = self.clean_option_text(
                raw_text
            )

            if visible:
                button.config(
                    state='normal'
                )

                label.config(
                    text=option_text
                )

                # Cho phép click cả label
                label.bind(
                    '<Button-1>',
                    lambda event, value=letter:
                        self.select_answer(value)
                )

                row.bind(
                    '<Button-1>',
                    lambda event, value=letter:
                        self.select_answer(value)
                )

            else:
                button.config(
                    state='disabled'
                )

                label.config(
                    text=''
                )

                row.unbind(
                    '<Button-1>'
                )

                label.unbind(
                    '<Button-1>'
                )

                row.config(
                    bg='#f8fafc'
                )

                label.config(
                    bg='#f8fafc'
                )

        self.answer_var.set(
            state.get(
                'selected_answer'
            ) or ''
        )

        self.update_option_visuals()

        self.update_flag_button(
            qid
        )

        self.update_lifeline_button(
            qid
        )

        self.refresh_grid_colors()
        self.update_progress_bar()

    # =============================================================
    # OPTION VISUALS
    # =============================================================

    def update_option_visuals(self):
        if not self.questions:
            return

        question = self.questions[
            self.current_index
        ]

        qid = question.get('id')

        state = self.question_state.get(
            qid,
            {}
        )

        selected = state.get(
            'selected_answer'
        )

        visible_options = state.get(
            'visible_options'
        )

        for letter, button, label, row in zip(
            ('A', 'B', 'C', 'D'),
            self.option_buttons,
            self.option_labels,
            self.option_rows
        ):
            visible = (
                visible_options is None
                or letter in visible_options
            )

            if not visible:
                continue

            if letter == selected:
                row.config(
                    bg='#fff1f2',
                    highlightbackground='#fda4af'
                )

                label.config(
                    bg='#fff1f2',
                    fg='#7f1d2d',
                    font=(
                        'Arial',
                        12,
                        'bold'
                    )
                )

                button.config(
                    bg='#fff1f2',
                    activebackground='#fff1f2',
                    selectcolor='#fff1f2'
                )

            else:
                row.config(
                    bg='#ffffff',
                    highlightbackground='#e5e7eb'
                )

                label.config(
                    bg='#ffffff',
                    fg='#475569',
                    font=(
                        'Arial',
                        12
                    )
                )

                button.config(
                    bg='#ffffff',
                    activebackground='#fff1f2',
                    selectcolor='#fff7f7'
                )

    # =============================================================
    # RESIZE
    # =============================================================

    def resize_question_text(
        self,
        _event=None
    ):
        if not hasattr(
            self,
            'question_text'
        ):
            return

        available_width = max(
            480,
            self.winfo_width() - 430
        )

        self.question_text.config(
            wraplength=available_width
        )

        for label in getattr(
            self,
            'option_labels',
            []
        ):
            label.config(
                wraplength=max(
                    420,
                    available_width - 40
                )
            )

    # =============================================================
    # SAVE ANSWER
    # =============================================================

    def save_current_answer(self):
        if self.exam_state != 'IN_PROGRESS':
            return

        if not self.questions:
            return

        qid = self.questions[
            self.current_index
        ].get('id')

        answer = (
            self.answer_var.get()
            or None
        )

        if answer not in (
            'A',
            'B',
            'C',
            'D'
        ):
            answer = None

        self.question_state[qid][
            'selected_answer'
        ] = answer

        self.update_option_visuals()
        self.refresh_grid_colors()
        self.update_progress_bar()

    # =============================================================
    # FLAG
    # =============================================================

    def update_flag_button(
        self,
        qid
    ):
        if not hasattr(
            self,
            'flag_button'
        ):
            return

        flagged = self.question_state[
            qid
        ].get(
            'flagged'
        )

        self.flag_button.config(
            text=(
                '⭐ Đã đánh dấu'
                if flagged
                else '⭐ Review later'
            ),
            bg=(
                '#fef3c7'
                if flagged
                else '#fff7ec'
            ),
            fg=(
                '#92400e'
                if flagged
                else '#b45309'
            )
        )

    def toggle_flag(self):
        if self.exam_state != 'IN_PROGRESS':
            return

        if not self.questions:
            return

        qid = self.questions[
            self.current_index
        ].get('id')

        self.question_state[qid][
            'flagged'
        ] = not self.question_state[
            qid
        ].get(
            'flagged',
            False
        )

        self.update_flag_button(
            qid
        )

        self.refresh_grid_colors()

    # =============================================================
    # 50/50
    # =============================================================

    def update_lifeline_button(
        self,
        qid
    ):
        if not hasattr(
            self,
            'lifeline_button'
        ):
            return

        state = self.question_state[
            qid
        ]

        if self.lifeline_request_pending:
            self.lifeline_button.config(
                text='🧠 Đang xử lý...',
                state='disabled',
                bg='#f5f3ff',
                fg='#6d28d9'
            )

        elif self.lifeline_remaining <= 0:
            self.lifeline_button.config(
                text='🧠 Đã hết lượt',
                state='disabled',
                bg='#f3f4f6',
                fg='#64748b'
            )

        elif state.get(
            'lifeline_used'
        ):
            self.lifeline_button.config(
                text=(
                    f'🧠 '
                    f'{self.lifeline_remaining} left'
                ),
                state='disabled',
                bg='#fdf2f8',
                fg='#9f1239'
            )

        else:
            self.lifeline_button.config(
                text=(
                    f'🧠 50/50 '
                    f'({self.lifeline_remaining})'
                ),
                state='normal',
                bg='#fdf2f8',
                fg='#9f1239'
            )

    def use_lifeline(self):
        if self.exam_state != 'IN_PROGRESS':
            return

        if not self.questions:
            return

        question = self.questions[
            self.current_index
        ]

        qid = question.get('id')

        state = self.question_state[
            qid
        ]

        if (
            self.lifeline_remaining <= 0
            or state.get('lifeline_used')
            or self.lifeline_request_pending
        ):
            return

        self.lifeline_request_pending = True

        self.update_lifeline_button(
            qid
        )

        payload = {
            'action': 'use_lifeline',
            'exam_id': self.exam.get('id'),
            'question_id': qid,
            'user_id': self.current_user.get('id'),
            'role': self.current_user.get('role')
        }

        threading.Thread(
            target=self.lifeline_worker,
            args=(
                payload,
                qid
            ),
            daemon=True
        ).start()

    def lifeline_worker(
        self,
        payload,
        qid
    ):
        try:
            response = self.client.send_request(
                payload
            )

        except Exception as exc:
            logger.exception(
                '[EXAM] lifeline_failed: %s',
                exc
            )

            response = {
                'status': 'error',
                'message': str(exc)
            }

        self.root.after(
            0,
            lambda: self.handle_lifeline_response(
                response,
                qid
            )
        )

    def handle_lifeline_response(
        self,
        response,
        qid
    ):
        if self.exam_state != 'IN_PROGRESS':
            return

        if response.get(
            'status'
        ) != 'success':

            self.lifeline_request_pending = False

            messagebox.showerror(
                'Không thể dùng hỗ trợ',
                response.get('message')
                or 'Server không trả về hỗ trợ.'
            )

            self.update_lifeline_button(
                qid
            )

            return

        state = self.question_state[
            qid
        ]

        self.lifeline_request_pending = False

        self.lifeline_remaining = max(
            0,
            self.lifeline_remaining - 1
        )

        state[
            'lifeline_used'
        ] = True

        visible_options = (
            response.get(
                'visible_options'
            )
            or []
        )

        state[
            'visible_options'
        ] = [
            str(option).upper()
            for option in visible_options
        ]

        # Nếu đáp án hiện tại bị loại,
        # bỏ lựa chọn đó.
        selected = state.get(
            'selected_answer'
        )

        if (
            selected
            and selected not in state[
                'visible_options'
            ]
        ):
            state[
                'selected_answer'
            ] = None

        self.render_question()

    # =============================================================
    # QUESTION NAVIGATOR
    # =============================================================

    def refresh_grid_colors(self):
        if not hasattr(
            self,
            'nav_buttons'
        ):
            return

        for index, button in enumerate(
            self.nav_buttons
        ):
            if index >= len(
                self.questions
            ):
                continue

            qid = self.questions[
                index
            ].get('id')

            state = self.question_state.get(
                qid,
                {}
            )

            if index == self.current_index:
                button.config(
                    bg='#2563eb',
                    fg='white'
                )

            elif state.get(
                'flagged'
            ):
                button.config(
                    bg='#f59e0b',
                    fg='white'
                )

            elif state.get(
                'selected_answer'
            ):
                button.config(
                    bg='#7f1d2d',
                    fg='white'
                )

            else:
                button.config(
                    bg='#f8fafc',
                    fg='#0f172a'
                )

    def update_progress_bar(self):
        answered = sum(
            1
            for q in self.questions
            if self.question_state.get(
                q.get('id'),
                {}
            ).get(
                'selected_answer'
            )
        )

        percentage = int(
            (
                answered
                / max(
                    len(self.questions),
                    1
                )
            ) * 100
        )

        self.progress_var.set(
            f'{percentage}%'
        )

        self.progress_bar.coords(
            self.progress_fill,
            0,
            0,
            max(
                0,
                (percentage / 100) * 180
            ),
            10
        )

    # =============================================================
    # NAVIGATION
    # =============================================================

    def prev_question(self):
        if (
            self.exam_state == 'IN_PROGRESS'
            and self.current_index > 0
        ):
            self.save_current_answer()

            self.current_index -= 1

            self.render_question()

    def next_question(self):
        if (
            self.exam_state == 'IN_PROGRESS'
            and self.current_index
            < len(self.questions) - 1
        ):
            self.save_current_answer()

            self.current_index += 1

            self.render_question()

    def jump_to(
        self,
        index
    ):
        if (
            self.exam_state != 'IN_PROGRESS'
        ):
            return

        if not (
            0 <= index < len(
                self.questions
            )
        ):
            return

        self.save_current_answer()

        self.current_index = index

        self.render_question()

    # =============================================================
    # TIMER
    # =============================================================

    def start_timer(self):
        minutes, seconds = divmod(
            self.time_left_seconds,
            60
        )

        self.timer_label.config(
            text=(
                f'Thời gian: '
                f'{minutes:02d}:{seconds:02d}'
            )
        )

        self.timer_job = self.root.after(
            1000,
            self.tick_timer
        )

    def tick_timer(self):
        if self.exam_state != 'IN_PROGRESS':
            return

        self.time_left_seconds = max(
            0,
            self.time_left_seconds - 1
        )

        minutes, seconds = divmod(
            self.time_left_seconds,
            60
        )

        self.timer_label.config(
            text=(
                f'Thời gian: '
                f'{minutes:02d}:{seconds:02d}'
            )
        )

        if self.time_left_seconds == 0:
            self.submit_exam(
                reason='timeout',
                source='timer'
            )

        else:
            self.timer_job = self.root.after(
                1000,
                self.tick_timer
            )

    # =============================================================
    # FOCUS MONITOR
    # =============================================================

    def start_focus_monitor(self):
        self.focus_job = self.root.after(
            500,
            self.check_foreground
        )

    def check_foreground(self):
        if self.exam_state != 'IN_PROGRESS':
            return

        if self._is_foreground_lost():
            self.submit_exam(
                reason='focus_lost',
                source='focus_monitor'
            )

            return

        self.focus_job = self.root.after(
            500,
            self.check_foreground
        )

    def _is_foreground_lost(self):
        try:
            if sys.platform == 'win32':
                user32 = ctypes.windll.user32

                foreground = (
                    user32.GetForegroundWindow()
                )

                root_hwnd = user32.GetAncestor(
                    self.root.winfo_id(),
                    2
                )

                return foreground != root_hwnd

            return (
                self.root.focus_displayof()
                is None
            )

        except (
            AttributeError,
            tk.TclError,
            OSError
        ):
            return False

    # =============================================================
    # SUBMIT
    # =============================================================

    def submit_exam(
        self,
        quiet=False,
        reason='manual',
        source='manual'
    ):
        if self.exam_state != 'IN_PROGRESS':
            return False

        self.save_current_answer()

        self.exam_state = 'SUBMITTING'

        self.submit_button.config(
            state='disabled'
        )

        if self.timer_job:
            try:
                self.root.after_cancel(
                    self.timer_job
                )
            except Exception:
                pass

            self.timer_job = None

        if self.focus_job:
            try:
                self.root.after_cancel(
                    self.focus_job
                )
            except Exception:
                pass

            self.focus_job = None

        payload = {
            'action': 'submit_exam',
            'exam_id': self.exam.get('id'),
            'user_id': self.current_user.get('id'),
            'role': self.current_user.get('role'),

            'answers': [
                {
                    'question_id': q.get('id'),
                    'selected_answer':
                        self.question_state.get(
                            q.get('id'),
                            {}
                        ).get(
                            'selected_answer'
                        )
                }
                for q in self.questions
            ],

            'duration':
                int(
                    self.exam.get('duration')
                    or 0
                ) * 60
                - self.time_left_seconds,

            'source': source,
            'reason': reason,

            'submission_token':
                self.submission_token
        }

        threading.Thread(
            target=self.submit_worker,
            args=(payload,),
            daemon=True
        ).start()

        return True

    # =============================================================
    # SUBMIT WORKER
    # =============================================================

    def submit_worker(
        self,
        payload
    ):
        try:
            response = self.client.send_request(
                payload
            )

        except Exception as exc:
            logger.exception(
                '[EXAM] submit_request_failed'
            )

            response = {
                'status': 'error',
                'message': str(exc)
            }

        self.root.after(
            0,
            lambda: self.handle_submit_response(
                response,
                payload.get('reason')
            )
        )

    def handle_submit_response(
        self,
        response,
        reason
    ):
        if self.exam_state != 'SUBMITTING':
            return

        if response.get(
            'status'
        ) == 'success':

            self.exam_state = 'SUBMITTED'

            self.render_result_panel(
                response.get('result')
                or response,
                reason
            )

        else:
            self.render_submit_error(
                response.get('message')
                or 'Không thể nộp bài'
            )

    # =============================================================
    # RESULT
    # =============================================================

    def render_result_panel(
        self,
        result,
        reason
    ):
        self.exam_state = 'SHOWING_RESULT'

        for child in self.winfo_children():
            child.destroy()

        title = (
            'BÀI THI ĐÃ ĐƯỢC NỘP'
            if reason == 'focus_lost'
            else 'HOÀN THÀNH BÀI THI'
        )

        reason_text = (
            'Lý do: Rời khỏi màn hình thi'
            if reason == 'focus_lost'
            else 'Trạng thái: Đã nộp bài'
        )

        frame = tk.Frame(
            self,
            bg='#ffffff',
            padx=30,
            pady=30
        )

        frame.pack(
            fill='both',
            expand=True
        )

        tk.Label(
            frame,
            text=title,
            font=('Arial', 22, 'bold'),
            fg='#102a43',
            bg='#ffffff'
        ).pack(
            pady=(20, 16)
        )

        tk.Label(
            frame,
            text=reason_text,
            font=('Arial', 13),
            fg='#7F1D1D',
            bg='#ffffff'
        ).pack(
            anchor='w',
            pady=5
        )

        tk.Label(
            frame,
            text=(
                f"Điểm: "
                f"{result.get('score', 0)} / 10"
            ),
            font=('Arial', 18, 'bold'),
            fg='#0d6efd',
            bg='#ffffff'
        ).pack(
            anchor='w',
            pady=12
        )

        tk.Label(
            frame,
            text=(
                f"Đúng: "
                f"{result.get('correct_answers', 0)}    "
                f"Sai: "
                f"{result.get('wrong_answers', 0)}    "
                f"Bỏ trống: "
                f"{result.get('unanswered_questions', 0)}"
            ),
            font=('Arial', 12),
            bg='#ffffff'
        ).pack(
            anchor='w'
        )

        self.root.after(
            4000,
            self.safe_close_application
        )

    # =============================================================
    # SUBMIT ERROR
    # =============================================================

    def render_submit_error(
        self,
        message
    ):
        self.exam_state = 'EXITING'

        for child in self.winfo_children():
            child.destroy()

        frame = tk.Frame(
            self,
            bg='#ffffff',
            padx=30,
            pady=30
        )

        frame.pack(
            fill='both',
            expand=True
        )

        tk.Label(
            frame,
            text='KHÔNG THỂ NỘP BÀI',
            font=('Arial', 22, 'bold'),
            fg='#7F1D1D',
            bg='#ffffff'
        ).pack(
            pady=20
        )

        tk.Label(
            frame,
            text=message,
            font=('Arial', 12),
            bg='#ffffff',
            wraplength=600
        ).pack()

        self.root.after(
            4000,
            self.safe_close_application
        )

    # =============================================================
    # CLOSE
    # =============================================================

    def handle_alt_f4(
        self,
        _event=None
    ):
        self.handle_root_close()

        return 'break'

    def handle_root_close(self):
        if self.exam_state == 'IN_PROGRESS':
            self.submit_exam(
                reason='close_window',
                source='window_close'
            )

        elif self.exam_state not in (
            'SUBMITTING',
            'SHOWING_RESULT'
        ):
            self.safe_close_application()

    def safe_close_application(self):
        self.exam_state = 'EXITING'

        try:
            self.client.close()

        except Exception as exc:
            logger.exception(
                '[EXAM] client_close_failed: %s',
                exc
            )

        try:
            self.root.destroy()

        except tk.TclError:
            pass
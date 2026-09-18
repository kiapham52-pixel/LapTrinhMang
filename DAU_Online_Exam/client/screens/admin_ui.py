import tkinter as tk
from tkinter import ttk


BG = '#f5f5f5'
PANEL = '#ffffff'
BURGUNDY = '#7F1D1D'
RED = '#B91C1C'
TEXT = '#1f2937'
MUTED = '#6b7280'
BORDER = '#e5e7eb'
GREEN = '#15803d'


def module_header(parent, icon, title, subtitle):
    header = tk.Frame(parent, bg=BG)
    header.pack(fill='x', pady=(0, 14))
    tk.Label(header, text=f'{icon}  {title}', font=('Arial', 23, 'bold'), bg=BG, fg=BURGUNDY).pack(anchor='w')
    tk.Label(header, text=subtitle, font=('Arial', 10), bg=BG, fg=MUTED).pack(anchor='w', pady=(5, 0))
    return header


def toolbar(parent):
    bar = tk.Frame(parent, bg=BG)
    bar.pack(fill='x', pady=(0, 12))
    return bar


def primary_button(parent, text, command):
    return tk.Button(parent, text=text, command=command, bg=BURGUNDY, fg='white', activebackground=RED,
                      activeforeground='white', relief='flat', padx=14, pady=7, font=('Arial', 10, 'bold'))


def secondary_button(parent, text, command):
    return tk.Button(parent, text=text, command=command, bg=PANEL, fg=TEXT, activebackground='#fef2f2',
                      relief='solid', borderwidth=1, padx=12, pady=6, font=('Arial', 10))


def panel(parent, padding=14):
    return tk.Frame(parent, bg=PANEL, padx=padding, pady=padding, highlightbackground=BORDER, highlightthickness=1)


def stat_card(parent, icon, label, value, color=BURGUNDY):
    card = tk.Frame(parent, bg=PANEL, padx=14, pady=13, highlightbackground=BORDER, highlightthickness=1)
    tk.Label(card, text=icon, font=('Arial', 20), bg=PANEL, fg=color).pack(anchor='w')
    tk.Label(card, text=str(value), font=('Arial', 21, 'bold'), bg=PANEL, fg=TEXT).pack(anchor='w', pady=(4, 0))
    tk.Label(card, text=label, font=('Arial', 9), bg=PANEL, fg=MUTED).pack(anchor='w')
    return card


def empty_state(parent, icon, title, message, action_text=None, command=None):
    box = tk.Frame(parent, bg=PANEL, padx=22, pady=28)
    tk.Label(box, text=icon, font=('Arial', 30), bg=PANEL, fg=BURGUNDY).pack()
    tk.Label(box, text=title, font=('Arial', 14, 'bold'), bg=PANEL, fg=TEXT).pack(pady=(8, 3))
    tk.Label(box, text=message, font=('Arial', 10), bg=PANEL, fg=MUTED, justify='center').pack()
    if action_text and command:
        primary_button(box, action_text, command).pack(pady=(14, 0))
    return box


def loading_state(parent, text='Đang tải dữ liệu...'):
    box = tk.Frame(parent, bg=PANEL, padx=20, pady=22)
    tk.Label(box, text='⏳', font=('Arial', 22), bg=PANEL, fg=BURGUNDY).pack(side='left', padx=(0, 10))
    tk.Label(box, text=text, font=('Arial', 10), bg=PANEL, fg=MUTED).pack(side='left')
    return box


def configure_tree(tree):
    tree.configure(show='headings')
    style = ttk.Style(tree)
    style.configure('Treeview', rowheight=30, font=('Arial', 10), background=PANEL, fieldbackground=PANEL, foreground=TEXT)
    style.configure('Treeview.Heading', font=('Arial', 10, 'bold'), background='#fee2e2', foreground=BURGUNDY)
    style.map('Treeview', background=[('selected', '#fecaca')], foreground=[('selected', TEXT)])

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import sys, os, io, contextlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from patterns.structural.decorator import (
    UrgentDecorator, LoggingDecorator,
    ReminderDecorator, DifficultyDecorator,
)
from patterns.structural.adapter import (
    GoogleCalendarAdapter, TrelloAdapter,
    PlainTextAdapter, ImportService,
)


class TasksTab:

    def __init__(self, notebook, manager, creators, set_status_cb, refresh_stats_cb):
        self.manager        = manager
        self._creators      = creators
        self._set_status    = set_status_cb
        self._refresh_stats = refresh_stats_cb
        self._import_svc    = ImportService(manager)   

        self.frame = tk.Frame(notebook)
        notebook.add(self.frame, text="  ✏️  Задачи  ")
        self._build()

    def _build(self):
        tab = self.frame

        left = tk.Frame(tab, width=340)
        left.pack(side="left", fill="y", padx=(14, 7), pady=14)
        left.pack_propagate(False)

        tk.Label(left, text="Создать задачу",
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 10))

        tk.Label(left, text="Название задачи:",
                 font=("Segoe UI", 10)).pack(anchor="w")
        self.task_title_var = tk.StringVar()
        self.task_title_entry = tk.Entry(
            left, textvariable=self.task_title_var, font=("Segoe UI", 10))
        self.task_title_entry.pack(fill="x", pady=(2, 8))

        tk.Label(left, text="Предмет:", font=("Segoe UI", 10)).pack(anchor="w")
        self.task_subject_var = tk.StringVar()
        subjects = ["Математика", "Физика", "Химия", "Биология",
                    "История", "Информатика", "Литература", "Другое"]
        self.task_subject_cb = ttk.Combobox(
            left, textvariable=self.task_subject_var,
            values=subjects, font=("Segoe UI", 10))
        self.task_subject_cb.current(0)
        self.task_subject_cb.pack(fill="x", pady=(2, 8))

        tk.Label(left, text="Тип задачи (Factory Method):",
                 font=("Segoe UI", 10)).pack(anchor="w")
        self.task_type_var = tk.StringVar(value="Лекция")
        for ttype in ["Лекция", "Практика", "Повторение"]:
            tk.Radiobutton(
                left, text=ttype, variable=self.task_type_var,
                value=ttype, font=("Segoe UI", 10),
            ).pack(anchor="w")

        tk.Label(left, text="Продолжительность (мин):",
                 font=("Segoe UI", 10)).pack(anchor="w", pady=(8, 0))
        self.task_dur_var = tk.IntVar(value=60)
        tk.Spinbox(left, from_=15, to=240, increment=15,
                   textvariable=self.task_dur_var,
                   font=("Segoe UI", 10)).pack(fill="x", pady=(2, 8))

        tk.Label(left, text="Дедлайн (дней от сегодня):",
                 font=("Segoe UI", 10)).pack(anchor="w")
        self.task_days_var = tk.IntVar(value=7)
        tk.Spinbox(left, from_=1, to=90,
                   textvariable=self.task_days_var,
                   font=("Segoe UI", 10)).pack(fill="x", pady=(2, 10))

        dec_frame = tk.LabelFrame(
            left, text=" 🎀 Decorator (необязательно) ",
            font=("Segoe UI", 9, "bold"), padx=6, pady=4)
        dec_frame.pack(fill="x", pady=(0, 10))

        self._use_urgent   = tk.BooleanVar(value=False)
        self._use_reminder = tk.BooleanVar(value=False)
        self._use_logging  = tk.BooleanVar(value=False)
        self._use_diff     = tk.BooleanVar(value=False)
        self._diff_level   = tk.StringVar(value="средний")

        tk.Checkbutton(dec_frame, text="🚨 Срочная задача",
                       variable=self._use_urgent,
                       font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w")
        tk.Checkbutton(dec_frame, text="🔔 Напоминание",
                       variable=self._use_reminder,
                       font=("Segoe UI", 9)).grid(row=0, column=1, sticky="w")
        tk.Checkbutton(dec_frame, text="📝 Логировать",
                       variable=self._use_logging,
                       font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w")

        diff_cb_frame = tk.Frame(dec_frame)
        diff_cb_frame.grid(row=1, column=1, sticky="w")
        tk.Checkbutton(diff_cb_frame, text="🎯",
                       variable=self._use_diff,
                       font=("Segoe UI", 9)).pack(side="left")
        ttk.Combobox(diff_cb_frame, textvariable=self._diff_level,
                     values=["лёгкий", "средний", "сложный", "очень сложный"],
                     width=11, font=("Segoe UI", 9)).pack(side="left")

        self.btn_create = tk.Button(
            left, text="➕  Создать задачу",
            font=("Segoe UI", 11, "bold"),
            relief="flat", padx=10, pady=10,
            cursor="hand2", command=self.create_task)
        self.btn_create.pack(fill="x", pady=(0, 6))

        self.btn_delete = tk.Button(
            left, text="🗑  Удалить выбранную",
            font=("Segoe UI", 10),
            relief="flat", padx=10, pady=7,
            cursor="hand2", command=self.delete_task)
        self.btn_delete.pack(fill="x", pady=(0, 6))

        self.btn_done = tk.Button(
            left, text="✅  Отметить выполненной",
            font=("Segoe UI", 10),
            relief="flat", padx=10, pady=7,
            cursor="hand2", command=self.mark_done)
        self.btn_done.pack(fill="x", pady=(0, 10))

        imp_frame = tk.LabelFrame(
            left, text=" 🔌 Adapter — импорт задач ",
            font=("Segoe UI", 9, "bold"), padx=6, pady=6)
        imp_frame.pack(fill="x")

        self._import_source = tk.StringVar(value="google")
        sources = [
            ("📅 Google Cal",  "google"),
            ("📋 Trello",      "trello"),
            ("📄 PlainText",   "plain"),
        ]
        src_row = tk.Frame(imp_frame)
        src_row.pack(fill="x", pady=(0, 6))
        for label, key in sources:
            tk.Radiobutton(src_row, text=label,
                           variable=self._import_source, value=key,
                           font=("Segoe UI", 9)).pack(side="left")

        tk.Button(imp_frame, text="📥  Импортировать в список",
                  font=("Segoe UI", 10, "bold"),
                  relief="flat", padx=8, pady=7,
                  cursor="hand2", command=self.import_tasks
                  ).pack(fill="x")

        tk.Frame(tab, width=2).pack(side="left", fill="y", pady=14)

        right = tk.Frame(tab)
        right.pack(side="left", fill="both", expand=True,
                   padx=(7, 14), pady=14)

        tk.Label(right, text="Список задач",
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 8))

        cols = ("Тип", "Название", "Предмет", "Время",
                "Дедлайн", "Приоритет", "Декораторы", "Статус")
        self.tree = ttk.Treeview(right, columns=cols,
                                  show="headings", selectmode="browse")
        widths = (80, 200, 100, 60, 100, 80, 100, 55)
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")

        scroll_y = ttk.Scrollbar(right, orient="vertical",
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")


    def create_task(self):
        """Factory Method + опциональный Decorator."""
        title     = self.task_title_var.get().strip()
        subject   = self.task_subject_var.get()
        task_type = self.task_type_var.get()
        duration  = self.task_dur_var.get()
        days      = self.task_days_var.get()

        if not title:
            messagebox.showwarning("Ошибка", "Введите название задачи!")
            return

        deadline = datetime.now() + timedelta(days=days)
        creator  = self._creators[task_type]

        task = creator.factory_method(title, subject, duration, deadline)

        decorators_applied = []
        if self._use_diff.get():
            task = DifficultyDecorator(task, level=self._diff_level.get())
            decorators_applied.append(f"🎯{self._diff_level.get()}")
        if self._use_reminder.get():
            task = ReminderDecorator(task, remind_days_before=days)
            decorators_applied.append("🔔")
        if self._use_logging.get():
            task = LoggingDecorator(task)
            decorators_applied.append("📝")
        if self._use_urgent.get():
            task = UrgentDecorator(task, reason="Отмечено пользователем")
            decorators_applied.append("🚨")

        self.manager.add_task(task)

        self.task_title_var.set("")
        self.refresh()
        self._refresh_stats()

        dec_str = " ".join(decorators_applied)
        suffix  = f" [{dec_str}]" if dec_str else ""
        self._set_status(f"✅ [{task_type}] {title}{suffix}")

    def delete_task(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Ошибка", "Выберите задачу для удаления!")
            return
        title_val = self.tree.item(sel[0])["values"][1]
        clean = title_val.lstrip("🚨🔔 ")
        for t in self.manager.get_all_tasks():
            if t.title == clean or t.title == title_val:
                self.manager.remove_task(t.task_id)
                break
        self.refresh()
        self._refresh_stats()
        self._set_status("🗑 Задача удалена")

    def mark_done(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Ошибка", "Выберите задачу!")
            return
        title_val = self.tree.item(sel[0])["values"][1]
        clean = title_val.lstrip("🚨🔔 ")
        for t in self.manager.get_all_tasks():
            if (t.title == clean or t.title == title_val) and not t.completed:
                self.manager.mark_task_completed(t.task_id)
                break
        self.refresh()
        self._refresh_stats()
        self._set_status(f"✅ Выполнена: {title_val}")

    def import_tasks(self):
        """Adapter — импортируем задачи из внешнего источника прямо в список."""
        adapters = {
            "google": GoogleCalendarAdapter(),
            "trello": TrelloAdapter(),
            "plain":  PlainTextAdapter(),
        }
        source  = self._import_source.get()
        adapter = adapters[source]

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            count = self._import_svc.run_import(adapter)

        self.refresh()
        self._refresh_stats()
        self._set_status(
            f"🔌 Adapter [{adapter.get_source_name()}]: импортировано {count} задач")

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for task in self.manager.get_all_tasks():
            info = task.get_info()

            dec_icons = _detect_decorators(task)

            self.tree.insert("", "end", values=(
                info["type"],
                info["title"],
                info["subject"],
                info["duration"],
                info["deadline"],
                info["priority"],
                dec_icons,
                info["done"],
            ))


def _detect_decorators(task) -> str:
    """Проходим цепочку декораторов и собираем иконки."""
    icons = []
    current = task
    while hasattr(current, "_component"):
        name = type(current).__name__
        if name == "UrgentDecorator"     and "🚨" not in icons: icons.append("🚨")
        if name == "ReminderDecorator"   and "🔔" not in icons: icons.append("🔔")
        if name == "LoggingDecorator"    and "📝" not in icons: icons.append("📝")
        if name == "DifficultyDecorator" and "🎯" not in icons: icons.append("🎯")
        current = current._component
    return " ".join(icons) if icons else "—"
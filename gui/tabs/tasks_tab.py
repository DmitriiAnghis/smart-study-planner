import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta


class TasksTab:
    
    def __init__(self, notebook, manager, creators, set_status_cb, refresh_stats_cb):
      
        self.manager          = manager
        self._creators        = creators
        self._set_status      = set_status_cb
        self._refresh_stats   = refresh_stats_cb

        # Создаём фрейм вкладки
        self.frame = tk.Frame(notebook)
        notebook.add(self.frame, text="  ✏️  Задачи  ")

        self._build()

    def _build(self):
        tab = self.frame

        # Левая колонка — форма создания
        left = tk.Frame(tab, width=320)
        left.pack(side="left", fill="y", padx=(14, 7), pady=14)
        left.pack_propagate(False)

        tk.Label(left, text="Создать задачу",
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 12))

        # Название
        tk.Label(left, text="Название задачи:",
                 font=("Segoe UI", 10)).pack(anchor="w")
        self.task_title_var = tk.StringVar()
        self.task_title_entry = tk.Entry(
            left, textvariable=self.task_title_var, font=("Segoe UI", 10))
        self.task_title_entry.pack(fill="x", pady=(2, 10))

        # Предмет
        tk.Label(left, text="Предмет:", font=("Segoe UI", 10)).pack(anchor="w")
        self.task_subject_var = tk.StringVar()
        subjects = ["Математика", "Физика", "Химия", "Биология",
                    "История", "Информатика", "Литература", "Другое"]
        self.task_subject_cb = ttk.Combobox(
            left, textvariable=self.task_subject_var,
            values=subjects, font=("Segoe UI", 10))
        self.task_subject_cb.current(0)
        self.task_subject_cb.pack(fill="x", pady=(2, 10))

        # Тип задачи
        tk.Label(left, text="Тип задачи (Factory Method):",
                 font=("Segoe UI", 10)).pack(anchor="w")
        self.task_type_var = tk.StringVar(value="Лекция")
        for ttype in ["Лекция", "Практика", "Повторение"]:
            tk.Radiobutton(
                left, text=ttype, variable=self.task_type_var,
                value=ttype, font=("Segoe UI", 10),
            ).pack(anchor="w")

        # Продолжительность
        tk.Label(left, text="Продолжительность (мин):",
                 font=("Segoe UI", 10)).pack(anchor="w", pady=(10, 0))
        self.task_dur_var = tk.IntVar(value=60)
        tk.Spinbox(left, from_=15, to=240, increment=15,
                   textvariable=self.task_dur_var,
                   font=("Segoe UI", 10)).pack(fill="x", pady=(2, 10))

        # Дедлайн
        tk.Label(left, text="Дедлайн (дней от сегодня):",
                 font=("Segoe UI", 10)).pack(anchor="w")
        self.task_days_var = tk.IntVar(value=7)
        tk.Spinbox(left, from_=1, to=90,
                   textvariable=self.task_days_var,
                   font=("Segoe UI", 10)).pack(fill="x", pady=(2, 14))

        # Кнопки
        self.btn_create = tk.Button(
            left, text="➕  Создать задачу",
            font=("Segoe UI", 11, "bold"),
            relief="flat", padx=10, pady=10,
            cursor="hand2", command=self.create_task)
        self.btn_create.pack(fill="x", pady=(0, 8))

        self.btn_delete = tk.Button(
            left, text="🗑  Удалить выбранную",
            font=("Segoe UI", 10),
            relief="flat", padx=10, pady=8,
            cursor="hand2", command=self.delete_task)
        self.btn_delete.pack(fill="x", pady=(0, 8))

        self.btn_done = tk.Button(
            left, text="✅  Отметить выполненной",
            font=("Segoe UI", 10),
            relief="flat", padx=10, pady=8,
            cursor="hand2", command=self.mark_done)
        self.btn_done.pack(fill="x")

        # Разделитель
        tk.Frame(tab, width=2).pack(side="left", fill="y", pady=14)

        # Правая колонка — таблица
        right = tk.Frame(tab)
        right.pack(side="left", fill="both", expand=True,
                   padx=(7, 14), pady=14)

        tk.Label(right, text="Список задач",
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 8))

        cols = ("Тип", "Название", "Предмет", "Время", "Дедлайн", "Приоритет", "Статус")
        self.tree = ttk.Treeview(right, columns=cols,
                                  show="headings", selectmode="browse")
        widths = (90, 220, 110, 70, 110, 90, 70)
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")

        scroll_y = ttk.Scrollbar(right, orient="vertical",
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

    # ДЕЙСТВИЯ

    def create_task(self):
        """Factory Method: создаём задачу через ConcreteCreator."""
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
        creator.create_and_register(title, subject, duration, deadline)

        self.task_title_var.set("")
        self.refresh()
        self._refresh_stats()
        self._set_status(f"✅ Создана задача [{task_type}]: {title}")

    def delete_task(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Ошибка", "Выберите задачу для удаления!")
            return
        title_val = self.tree.item(sel[0])["values"][1]
        for t in self.manager.get_all_tasks():
            if t.title == title_val:
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
        for t in self.manager.get_all_tasks():
            if t.title == title_val and not t.completed:
                self.manager.mark_task_completed(t.task_id)
                break
        self.refresh()
        self._refresh_stats()
        self._set_status(f"✅ Задача выполнена: {title_val}")

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for task in self.manager.get_all_tasks():
            info = task.get_info()
            self.tree.insert("", "end", values=(
                info["type"], info["title"], info["subject"],
                info["duration"], info["deadline"],
                info["priority"], info["done"],
            ))
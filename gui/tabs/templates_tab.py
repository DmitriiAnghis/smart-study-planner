import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta


class TemplatesTab:
   

    def __init__(self, notebook, manager, creators,
                 template_registry, set_status_cb, refresh_stats_cb, refresh_tasks_cb):
       
        self.manager           = manager
        self._creators         = creators
        self.registry          = template_registry
        self._set_status       = set_status_cb
        self._refresh_stats    = refresh_stats_cb
        self._refresh_tasks = refresh_tasks_cb

        self.frame = tk.Frame(notebook)
        notebook.add(self.frame, text="  📋  Шаблоны  ")

        self._build()

    def _build(self):
        tab = self.frame

        # Левая колонка
        left = tk.Frame(tab, width=320)
        left.pack(side="left", fill="y", padx=(14, 7), pady=14)
        left.pack_propagate(False)

        tk.Label(left, text="Использовать шаблон",
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 12))

        # Выбор прототипа
        tk.Label(left, text="Прототип (clone):",
                 font=("Segoe UI", 10)).pack(anchor="w")
        self.proto_key_var = tk.StringVar()
        self.proto_cb = ttk.Combobox(
            left, textvariable=self.proto_key_var,
            values=self.registry.get_all_keys(), font=("Segoe UI", 10))
        self.proto_cb.current(0)
        self.proto_cb.pack(fill="x", pady=(2, 10))

        # Предмет клона
        tk.Label(left, text="Предмет клона:",
                 font=("Segoe UI", 10)).pack(anchor="w")
        self.proto_subject_var = tk.StringVar(value="Математика")
        subjects = ["Математика", "Физика", "Химия", "Биология",
                    "История", "Информатика", "Литература"]
        ttk.Combobox(left, textvariable=self.proto_subject_var,
                     values=subjects, font=("Segoe UI", 10)).pack(
                         fill="x", pady=(2, 10))

        # Дней до дедлайна
        tk.Label(left, text="Дней до дедлайна:",
                 font=("Segoe UI", 10)).pack(anchor="w")
        self.proto_days_var = tk.IntVar(value=5)
        tk.Spinbox(left, from_=1, to=90,
                   textvariable=self.proto_days_var,
                   font=("Segoe UI", 10)).pack(fill="x", pady=(2, 14))

        # Кнопка клонировать
        self.btn_clone = tk.Button(
            left, text="🔁  Клонировать шаблон",
            font=("Segoe UI", 11, "bold"),
            relief="flat", padx=10, pady=10,
            cursor="hand2", command=self.clone_template)
        self.btn_clone.pack(fill="x", pady=(0, 8))

        # Разделитель
        tk.Label(left, text="─" * 36,
                 font=("Segoe UI", 8)).pack(pady=6)
        tk.Label(left, text="Зарегистрировать прототип:",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")

        # Форма регистрации
        tk.Label(left, text="Ключ:", font=("Segoe UI", 10)).pack(anchor="w")
        self.new_proto_key_var = tk.StringVar()
        tk.Entry(left, textvariable=self.new_proto_key_var,
                 font=("Segoe UI", 10)).pack(fill="x", pady=(2, 6))

        tk.Label(left, text="Название:", font=("Segoe UI", 10)).pack(anchor="w")
        self.new_proto_name_var = tk.StringVar()
        tk.Entry(left, textvariable=self.new_proto_name_var,
                 font=("Segoe UI", 10)).pack(fill="x", pady=(2, 6))

        tk.Label(left, text="Тип:", font=("Segoe UI", 10)).pack(anchor="w")
        self.new_proto_type_var = tk.StringVar(value="Лекция")
        ttk.Combobox(left, textvariable=self.new_proto_type_var,
                     values=["Лекция", "Практика", "Повторение"],
                     font=("Segoe UI", 10)).pack(fill="x", pady=(2, 6))

        tk.Label(left, text="Длительность (мин):",
                 font=("Segoe UI", 10)).pack(anchor="w")
        self.new_proto_dur_var = tk.IntVar(value=60)
        tk.Spinbox(left, from_=15, to=240, increment=15,
                   textvariable=self.new_proto_dur_var,
                   font=("Segoe UI", 10)).pack(fill="x", pady=(2, 10))

        self.btn_register = tk.Button(
            left, text="📌  Зарегистрировать",
            font=("Segoe UI", 10),
            relief="flat", padx=10, pady=8,
            cursor="hand2", command=self.register_prototype)
        self.btn_register.pack(fill="x")

        # Правая часть — таблица
        right = tk.Frame(tab)
        right.pack(side="left", fill="both", expand=True,
                   padx=(7, 14), pady=14)

        tk.Label(right, text="Зарегистрированные прототипы",
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 7))

        cols = ("Ключ", "Название", "Тип", "Предмет", "Время")
        self.tree = ttk.Treeview(right, columns=cols,
                                  show="headings", selectmode="browse")
        ws = (130, 170, 90, 100, 70)
        for col, w in zip(cols, ws):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")
        sc = ttk.Scrollbar(right, orient="vertical",
                           command=self.tree.yview)
        self.tree.configure(yscrollcommand=sc.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sc.pack(side="right", fill="y")

    # ДЕЙСТВИЯ

    def clone_template(self):
        key     = self.proto_key_var.get()
        subject = self.proto_subject_var.get()
        days    = self.proto_days_var.get()

        try:
            cloned    = self.registry.clone(key).customize(subject=subject)
            deadline  = datetime.now() + timedelta(days=days)
            task_dict = cloned.to_task_dict(deadline)

            creator = self._creators.get(
                cloned.task_type, self._creators["Лекция"])
            creator.create_and_register(
                task_dict["title"], task_dict["subject"],
                task_dict["duration"], task_dict["deadline"])
            
            self._refresh_tasks()
            self._refresh_stats()
            self._set_status(f"🔁 Клонирован '{key}' → задача для {subject}")
        except KeyError as e:
            messagebox.showerror("Ошибка", str(e))

    def register_prototype(self):
        key   = self.new_proto_key_var.get().strip()
        name  = self.new_proto_name_var.get().strip()
        ptype = self.new_proto_type_var.get()
        dur   = self.new_proto_dur_var.get()

        if not key or not name:
            messagebox.showwarning("Ошибка", "Заполните ключ и название!")
            return

        from patterns.prototype import LectureTemplate, PracticeTemplate, RevisionTemplate
        templates = {
            "Лекция":     lambda: LectureTemplate(name, "Общий", dur),
            "Практика":   lambda: PracticeTemplate(name, "Общий", dur),
            "Повторение": lambda: RevisionTemplate(name, "Общий", dur),
        }
        proto = templates[ptype]()
        self.registry.register(key, proto)

        self.proto_cb["values"] = self.registry.get_all_keys()
        self.refresh()
        self.new_proto_key_var.set("")
        self.new_proto_name_var.set("")
        self._set_status(f"📌 Прототип '{key}' зарегистрирован")

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for key in self.registry.get_all_keys():
            proto = self.registry._prototypes[key]
            self.tree.insert("", "end", values=(
                key, proto.template_name, proto.task_type,
                proto.subject, f"{proto.duration_minutes} мин",
            ))
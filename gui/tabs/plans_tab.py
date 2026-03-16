import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta


class PlansTab:


    def __init__(self, notebook, manager, director,
                 intensive_builder_cls, relaxed_builder_cls,
                 set_status_cb, refresh_stats_cb):
      
        self.manager               = manager
        self.director              = director
        self._IntensivePlanBuilder = intensive_builder_cls
        self._RelaxedPlanBuilder   = relaxed_builder_cls
        self._set_status           = set_status_cb
        self._refresh_stats        = refresh_stats_cb

        self.frame = tk.Frame(notebook)
        notebook.add(self.frame, text="  📅  Планы  ")

        self._build()

    def _build(self):
        tab = self.frame

        # Левая колонка — форма
        left = tk.Frame(tab, width=320)
        left.pack(side="left", fill="y", padx=(14, 7), pady=14)
        left.pack_propagate(False)

        tk.Label(left, text="Создать учебный план",
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 12))

        # Предмет
        tk.Label(left, text="Предмет:", font=("Segoe UI", 10)).pack(anchor="w")
        self.plan_subject_var = tk.StringVar()
        subjects = ["Математика", "Физика", "Химия", "Биология",
                    "История", "Информатика", "Литература"]
        cb = ttk.Combobox(left, textvariable=self.plan_subject_var,
                          values=subjects, font=("Segoe UI", 10))
        cb.current(0)
        cb.pack(fill="x", pady=(2, 10))

        # Дней до экзамена
        tk.Label(left, text="Дней до экзамена:",
                 font=("Segoe UI", 10)).pack(anchor="w")
        self.plan_days_var = tk.IntVar(value=14)
        tk.Spinbox(left, from_=1, to=120,
                   textvariable=self.plan_days_var,
                   font=("Segoe UI", 10)).pack(fill="x", pady=(2, 10))

        # Часов в день
        tk.Label(left, text="Часов в день:",
                 font=("Segoe UI", 10)).pack(anchor="w")
        self.plan_hours_var = tk.DoubleVar(value=3.0)
        tk.Spinbox(left, from_=0.5, to=12.0, increment=0.5,
                   textvariable=self.plan_hours_var,
                   font=("Segoe UI", 10)).pack(fill="x", pady=(2, 10))

        # Тип плана
        tk.Label(left, text="Тип плана (Builder):",
                 font=("Segoe UI", 10)).pack(anchor="w", pady=(6, 2))
        self.plan_type_var = tk.StringVar(value="intensive")
        tk.Radiobutton(left, text="⚡  Интенсивный (IntensivePlanBuilder)",
                       variable=self.plan_type_var, value="intensive",
                       font=("Segoe UI", 10)).pack(anchor="w")
        tk.Radiobutton(left, text="🌿  Расслабленный (RelaxedPlanBuilder)",
                       variable=self.plan_type_var, value="relaxed",
                       font=("Segoe UI", 10)).pack(anchor="w")

        # Кнопки
        self.btn_create = tk.Button(
            left, text="📅  Создать план",
            font=("Segoe UI", 11, "bold"),
            relief="flat", padx=10, pady=10,
            cursor="hand2", command=self.create_plan)
        self.btn_create.pack(fill="x", pady=(16, 8))

        self.btn_delete = tk.Button(
            left, text="🗑  Удалить план",
            font=("Segoe UI", 10),
            relief="flat", padx=10, pady=8,
            cursor="hand2", command=self.delete_plan)
        self.btn_delete.pack(fill="x")

        # Правая часть — детали
        right = tk.Frame(tab)
        right.pack(side="left", fill="both", expand=True,
                   padx=(7, 14), pady=14)

        tk.Label(right, text="Детали плана",
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 8))

        # Таблица планов
        plan_list_frame = tk.Frame(right, height=160)
        plan_list_frame.pack(fill="x")
        plan_list_frame.pack_propagate(False)

        cols = ("Предмет", "Тип", "Приоритет", "Дней", "В день", "Задач")
        self.tree = ttk.Treeview(plan_list_frame, columns=cols,
                                  show="headings", selectmode="browse")
        ws = (140, 130, 90, 70, 70, 70)
        for col, w in zip(cols, ws):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_plan_select)

        # Детальный текст
        tk.Label(right, text="Подробности:",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 2))
        self.plan_detail = tk.Text(right, font=("Consolas", 9),
                                    relief="flat", wrap="word", state="disabled")
        sc = ttk.Scrollbar(right, orient="vertical",
                           command=self.plan_detail.yview)
        self.plan_detail.configure(yscrollcommand=sc.set)
        self.plan_detail.pack(side="left", fill="both", expand=True)
        sc.pack(side="right", fill="y")

    # ДЕЙСТВИЯ

    def create_plan(self):
        subject   = self.plan_subject_var.get()
        days      = self.plan_days_var.get()
        hours     = self.plan_hours_var.get()
        ptype     = self.plan_type_var.get()
        exam_date = datetime.now() + timedelta(days=days)

        if ptype == "intensive":
            builder = self._IntensivePlanBuilder()
        else:
            builder = self._RelaxedPlanBuilder()

        self.director.set_builder(builder)
        plan = self.director.build_full_plan(subject, exam_date, hours)

        self.refresh()
        self._refresh_stats()
        self._set_status(
            f"📅 Создан план [{plan.plan_type}]: {subject}, {days} дней")

    def delete_plan(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Ошибка", "Выберите план для удаления!")
            return
        values = self.tree.item(sel[0])["values"]
        subj, ptype = values[0], values[1]
        plans = self.manager.get_all_plans()
        for i, p in enumerate(plans):
            if p.subject == subj and p.plan_type == ptype:
                self.manager._study_plans.pop(i)
                break
        self.refresh()
        self._refresh_stats()
        self._set_status("🗑 План удалён")

    def _on_plan_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0])["values"]
        subj, ptype = values[0], values[1]
        for p in self.manager.get_all_plans():
            if p.subject == subj and p.plan_type == ptype:
                self.plan_detail.configure(state="normal")
                self.plan_detail.delete("1.0", "end")
                self.plan_detail.insert("1.0", p.get_summary())
                self.plan_detail.configure(state="disabled")
                break

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for plan in self.manager.get_all_plans():
            days = (plan.exam_date - datetime.now()).days if plan.exam_date else 0
            self.tree.insert("", "end", values=(
                plan.subject, plan.plan_type, plan.priority,
                f"{days} дн.", f"{plan.daily_hours} ч", len(plan.tasks),
            ))
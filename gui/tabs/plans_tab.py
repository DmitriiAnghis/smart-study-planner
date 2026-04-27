import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from patterns.structural.composite import (
    PlanTreeBuilder, StudyPlanSection, TaskLeaf
)


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

        self._current_tree: StudyPlanSection = None
        self._leaf_map: dict = {}

        self.frame = tk.Frame(notebook)
        notebook.add(self.frame, text="  📅  Планы  ")
        self._build()

    def _build(self):
        tab = self.frame

        left = tk.Frame(tab, width=320)
        left.pack(side="left", fill="y", padx=(14, 7), pady=14)
        left.pack_propagate(False)

        tk.Label(left, text="Создать учебный план",
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 12))

        tk.Label(left, text="Предмет:", font=("Segoe UI", 10)).pack(anchor="w")
        self.plan_subject_var = tk.StringVar()
        subjects = ["Математика", "Физика", "Химия", "Биология",
                    "История", "Информатика", "Литература"]
        cb = ttk.Combobox(left, textvariable=self.plan_subject_var,
                          values=subjects, font=("Segoe UI", 10))
        cb.current(0)
        cb.pack(fill="x", pady=(2, 10))

        tk.Label(left, text="Дней до экзамена:",
                 font=("Segoe UI", 10)).pack(anchor="w")
        self.plan_days_var = tk.IntVar(value=14)
        tk.Spinbox(left, from_=1, to=120,
                   textvariable=self.plan_days_var,
                   font=("Segoe UI", 10)).pack(fill="x", pady=(2, 10))

        tk.Label(left, text="Часов в день:",
                 font=("Segoe UI", 10)).pack(anchor="w")
        self.plan_hours_var = tk.DoubleVar(value=3.0)
        tk.Spinbox(left, from_=0.5, to=12.0, increment=0.5,
                   textvariable=self.plan_hours_var,
                   font=("Segoe UI", 10)).pack(fill="x", pady=(2, 10))

        tk.Label(left, text="Тип плана (Builder):",
                 font=("Segoe UI", 10)).pack(anchor="w", pady=(6, 2))
        self.plan_type_var = tk.StringVar(value="intensive")
        tk.Radiobutton(left, text="⚡  Интенсивный (IntensivePlanBuilder)",
                       variable=self.plan_type_var, value="intensive",
                       font=("Segoe UI", 10)).pack(anchor="w")
        tk.Radiobutton(left, text="🌿  Расслабленный (RelaxedPlanBuilder)",
                       variable=self.plan_type_var, value="relaxed",
                       font=("Segoe UI", 10)).pack(anchor="w")

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
        self.btn_delete.pack(fill="x", pady=(0, 8))

        self.btn_complete = tk.Button(
            left, text="✅  Отметить задачу выполненной",
            font=("Segoe UI", 10),
            relief="flat", padx=10, pady=8,
            cursor="hand2", command=self._complete_selected_leaf)
        self.btn_complete.pack(fill="x")

        right = tk.Frame(tab)
        right.pack(side="left", fill="both", expand=True,
                   padx=(7, 14), pady=14)

        top_row = tk.Frame(right)
        top_row.pack(fill="x", pady=(0, 6))
        tk.Label(top_row, text="Планы",
                 font=("Segoe UI", 13, "bold")).pack(side="left")
        self._plan_info_var = tk.StringVar(value="")
        tk.Label(top_row, textvariable=self._plan_info_var,
                 font=("Segoe UI", 9), fg="#888").pack(side="left", padx=10)

        plan_list_frame = tk.Frame(right, height=130)
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

        tk.Label(right, text="🌲 Структура плана (Composite)",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 2))

        composite_frame = tk.Frame(right)
        composite_frame.pack(fill="both", expand=True)

        comp_cols = ("Узел", "Тип", "Мин", "Прогресс")
        self.comp_tree = ttk.Treeview(composite_frame, columns=comp_cols,
                                       show="headings", selectmode="browse")
        comp_ws = (280, 90, 60, 100)
        for col, w in zip(comp_cols, comp_ws):
            self.comp_tree.heading(col, text=col)
            self.comp_tree.column(col, width=w,
                                  anchor="w" if col == "Узел" else "center")

        comp_sc = ttk.Scrollbar(composite_frame, orient="vertical",
                                command=self.comp_tree.yview)
        self.comp_tree.configure(yscrollcommand=comp_sc.set)
        self.comp_tree.pack(side="left", fill="both", expand=True)
        comp_sc.pack(side="right", fill="y")

        self.plan_detail = tk.Text(right, height=1, font=("Segoe UI", 8),
                                    relief="flat", state="disabled",
                                    fg="#888")
        self.plan_detail.pack(fill="x", pady=(4, 0))
        self._set_detail("← Выберите план, чтобы увидеть Composite-дерево")


    def create_plan(self):
        subject   = self.plan_subject_var.get()
        days      = self.plan_days_var.get()
        hours     = self.plan_hours_var.get()
        ptype     = self.plan_type_var.get()
        exam_date = datetime.now() + timedelta(days=days)

        builder = (self._IntensivePlanBuilder() if ptype == "intensive"
                   else self._RelaxedPlanBuilder())
        self.director.set_builder(builder)
        plan = self.director.build_full_plan(subject, exam_date, hours)

        self.refresh()
        self._refresh_stats()
        self._set_status(f"📅 Создан план [{plan.plan_type}]: {subject}, {days} дней")

    def delete_plan(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Ошибка", "Выберите план для удаления!")
            return
        values = self.tree.item(sel[0])["values"]
        subj, ptype = values[0], values[1]
        for i, p in enumerate(self.manager.get_all_plans()):
            if p.subject == subj and p.plan_type == ptype:
                self.manager._study_plans.pop(i)
                break
        self._current_tree = None
        self._leaf_map.clear()
        self._clear_comp_tree()
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
                deadline = p.exam_date or (datetime.now() + timedelta(days=14))
                if "Интенсивный" in ptype:
                    self._current_tree = PlanTreeBuilder.build_intensive(subj, deadline)
                else:
                    self._current_tree = PlanTreeBuilder.build_relaxed(subj, deadline)

                self._render_comp_tree(self._current_tree)

                total = self._current_tree.get_task_count()
                done  = self._current_tree.get_completed_count()
                mins  = self._current_tree.get_total_minutes()
                self._plan_info_var.set(
                    f"задач: {total}  |  выполнено: {done}  |  итого: {mins} мин")
                self._set_detail(
                    f"Выбран план [{ptype}]: {subj}  —  "
                    f"кликни задачу ниже и нажми «✅ Отметить выполненной»")
                break

    def _complete_selected_leaf(self):
        """Отметить выбранный TaskLeaf выполненным прямо в Composite-дереве."""
        sel = self.comp_tree.selection()
        if not sel:
            messagebox.showinfo("Composite", "Выберите задачу в дереве!")
            return
        iid = sel[0]
        leaf = self._leaf_map.get(iid)
        if leaf is None:
            messagebox.showinfo("Composite", "Выберите конкретную задачу (не раздел)!")
            return
        if leaf.task.completed:
            self._set_status("⬜ Задача уже выполнена")
            return

        leaf.task.completed = True
        self._render_comp_tree(self._current_tree)

        total = self._current_tree.get_task_count()
        done  = self._current_tree.get_completed_count()
        mins  = self._current_tree.get_total_minutes()
        self._plan_info_var.set(
            f"задач: {total}  |  выполнено: {done}  |  итого: {mins} мин")
        self._set_status(
            f"✅ Composite: задача '{leaf.task.title}' отмечена выполненной")


    def _clear_comp_tree(self):
        for item in self.comp_tree.get_children():
            self.comp_tree.delete(item)
        self._leaf_map.clear()

    def _render_comp_tree(self, root: StudyPlanSection):
        """Рекурсивно строим Treeview из Composite-дерева."""
        self._clear_comp_tree()
        self._insert_node(root, parent="")

    def _insert_node(self, node, parent: str):
        done  = node.get_completed_count()
        total = node.get_task_count()
        mins  = node.get_total_minutes()

        if node.is_composite():
            progress = f"{done}/{total}"
            iid = self.comp_tree.insert(
                parent, "end",
                values=(node.name, "📁 Раздел", mins, progress),
                open=True)
            for i in range(len(node._children)):
                self._insert_node(node.get_child(i), parent=iid)
        else:
            
            status = "✅ выполнено" if node.task.completed else "⬜ не выполнено"
            iid = self.comp_tree.insert(
                parent, "end",
                values=(f"  {node.name}", node.task.get_type(), mins, status))
            self._leaf_map[iid] = node  

    def _set_detail(self, text: str):
        self.plan_detail.configure(state="normal")
        self.plan_detail.delete("1.0", "end")
        self.plan_detail.insert("1.0", text)
        self.plan_detail.configure(state="disabled")

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for plan in self.manager.get_all_plans():
            days = (plan.exam_date - datetime.now()).days if plan.exam_date else 0
            self.tree.insert("", "end", values=(
                plan.subject, plan.plan_type, plan.priority,
                f"{days} дн.", f"{plan.daily_hours} ч", len(plan.tasks),
            ))
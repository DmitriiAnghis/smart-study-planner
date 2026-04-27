

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from patterns.singleton      import StudySessionManager
from patterns.factory_method import (LectureTaskCreator, PracticeTaskCreator,
                                     RevisionTaskCreator, LectureTask,
                                     PracticeTask, RevisionTask)

from patterns.structural.adapter import (GoogleCalendarAdapter, TrelloAdapter,
                                         PlainTextAdapter, ImportService)
from patterns.structural.composite import (TaskLeaf, StudyPlanSection,
                                           PlanTreeBuilder)
from patterns.structural.decorator import (UrgentDecorator, LoggingDecorator,
                                           ReminderDecorator, DifficultyDecorator)
from patterns.structural.proxy import (RealSessionManager, ProtectionProxy,
                                       CachingProxy, LoggingProxy)
from patterns.structural.facade import SmartStudyFacade



class LogBox(tk.Frame):
    """Текстовое поле с кнопкой очистки для вывода демонстраций."""

    def __init__(self, parent, height=14, **kw):
        super().__init__(parent, **kw)
        bar = ttk.Scrollbar(self, orient="vertical")
        self._text = tk.Text(self, font=("Consolas", 9), wrap="word",
                             state="disabled", height=height,
                             relief="flat", yscrollcommand=bar.set)
        bar.configure(command=self._text.yview)
        self._text.pack(side="left", fill="both", expand=True)
        bar.pack(side="right", fill="y")

    def write(self, msg: str):
        self._text.configure(state="normal")
        self._text.insert("end", msg + "\n")
        self._text.see("end")
        self._text.configure(state="disabled")

    def clear(self):
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.configure(state="disabled")

    def apply_theme(self, bg, fg):
        self._text.configure(bg=bg, fg=fg, insertbackground=fg)



class StructuralTab:
    """
    Вкладка «🔧 Структурные» — пять sub-вкладок,
    по одному паттерну в каждой.
    """

    def __init__(self, notebook, manager: StudySessionManager,
                 set_status_cb, refresh_stats_cb):
        self.manager          = manager
        self._set_status      = set_status_cb
        self._refresh_stats   = refresh_stats_cb

        self.frame = tk.Frame(notebook)
        notebook.add(self.frame, text="  🔧  Структурные  ")

        self._sub = ttk.Notebook(self.frame)
        self._sub.pack(fill="both", expand=True, padx=8, pady=8)

        self._adapter_tab   = AdapterSubTab(self._sub, manager, set_status_cb, refresh_stats_cb)
        self._composite_tab = CompositeSubTab(self._sub, manager, set_status_cb)
        self._decorator_tab = DecoratorSubTab(self._sub, manager, set_status_cb, refresh_stats_cb)
        self._proxy_tab     = ProxySubTab(self._sub, manager)
        self._facade_tab    = FacadeSubTab(self._sub, manager, set_status_cb, refresh_stats_cb)

    def get_log_boxes(self):
        return [
            self._adapter_tab.log,
            self._composite_tab.log,
            self._decorator_tab.log,
            self._proxy_tab.log,
            self._facade_tab.log,
        ]


class AdapterSubTab:

    def __init__(self, nb, manager, set_status_cb, refresh_stats_cb):
        self.manager        = manager
        self._set_status    = set_status_cb
        self._refresh_stats = refresh_stats_cb
        self._service       = ImportService(manager)

        self.frame = tk.Frame(nb)
        nb.add(self.frame, text=" 🔌 Adapter ")
        self._build()

    def _build(self):
        f = self.frame

        tk.Label(f, text="ADAPTER — импорт задач из внешних источников",
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14, pady=(10, 0))
        tk.Label(f,
                 text="ImportService работает только через ITaskImporter.import_tasks().\n"
                      "Adaptee (Google Calendar / Trello / PlainText) — разные форматы, "
                      "код не менялся.",
                 font=("Segoe UI", 9), justify="left", fg="#555"
                 ).pack(anchor="w", padx=14, pady=(2, 8))

        btn_row = tk.Frame(f)
        btn_row.pack(fill="x", padx=14, pady=(0, 6))

        SOURCES = [
            ("📅 Google Calendar", "google"),
            ("📋 Trello",          "trello"),
            ("📄 PlainText",       "plain"),
            ("🔀 Все источники",   "all"),
        ]
        for label, key in SOURCES:
            tk.Button(btn_row, text=label,
                      font=("Segoe UI", 10),
                      relief="flat", padx=10, pady=6, cursor="hand2",
                      command=lambda k=key: self._run_import(k)
                      ).pack(side="left", padx=4)

        tk.Button(btn_row, text="🗑 Очистить лог",
                  font=("Segoe UI", 9), relief="flat", padx=8, pady=6,
                  cursor="hand2", command=lambda: self.log.clear()
                  ).pack(side="right", padx=4)

        self.log = LogBox(f, height=16)
        self.log.pack(fill="both", expand=True, padx=14, pady=(0, 10))

    def _run_import(self, source: str):
        self.log.clear()
        _orig_print = __builtins__["print"] if isinstance(__builtins__, dict) else print

        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            adapters = {
                "google": [GoogleCalendarAdapter()],
                "trello": [TrelloAdapter()],
                "plain":  [PlainTextAdapter()],
                "all":    [GoogleCalendarAdapter(), TrelloAdapter(), PlainTextAdapter()],
            }
            total = 0
            for adapter in adapters[source]:
                n = self._service.run_import(adapter)
                total += n

        output = buf.getvalue()
        for line in output.splitlines():
            self.log.write(line)

        self.log.write(f"\n  ✅ Импортировано задач: {total}")
        self.log.write(f"  Всего в сессии: {self.manager.get_statistics()['total_tasks']}")
        self._set_status(f"🔌 Adapter: импортировано {total} задач из [{source}]")
        self._refresh_stats()



class CompositeSubTab:

    def __init__(self, nb, manager, set_status_cb):
        self.manager     = manager
        self._set_status = set_status_cb
        self._tree_root: StudyPlanSection = None

        self.frame = tk.Frame(nb)
        nb.add(self.frame, text=" 🌲 Composite ")
        self._build()

    def _build(self):
        f = self.frame

        tk.Label(f, text="COMPOSITE — дерево учебного плана",
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14, pady=(10, 0))
        tk.Label(f,
                 text="Client вызывает operation() одинаково для Leaf (задача) "
                      "и Composite (раздел).\nДерево строится рекурсивно.",
                 font=("Segoe UI", 9), fg="#555", justify="left"
                 ).pack(anchor="w", padx=14, pady=(2, 8))

        btn_row = tk.Frame(f)
        btn_row.pack(fill="x", padx=14, pady=(0, 6))

        subjects = ["Математика", "Физика", "Химия", "История"]
        self._subj_var = tk.StringVar(value=subjects[0])
        ttk.Combobox(btn_row, textvariable=self._subj_var,
                     values=subjects, width=12,
                     font=("Segoe UI", 10)).pack(side="left", padx=(0, 6))

        self._type_var = tk.StringVar(value="intensive")
        tk.Radiobutton(btn_row, text="⚡ Интенсивный",
                       variable=self._type_var, value="intensive",
                       font=("Segoe UI", 10)).pack(side="left")
        tk.Radiobutton(btn_row, text="🌿 Расслабленный",
                       variable=self._type_var, value="relaxed",
                       font=("Segoe UI", 10)).pack(side="left", padx=(0, 10))

        tk.Button(btn_row, text="🌲 Построить дерево",
                  font=("Segoe UI", 10), relief="flat", padx=10, pady=6,
                  cursor="hand2", command=self._build_tree
                  ).pack(side="left", padx=4)

        tk.Button(btn_row, text="✅ Отметить 1-ю задачу выполненной",
                  font=("Segoe UI", 10), relief="flat", padx=10, pady=6,
                  cursor="hand2", command=self._complete_first
                  ).pack(side="left", padx=4)

        tk.Button(btn_row, text="🗑 Очистить",
                  font=("Segoe UI", 9), relief="flat", padx=8, pady=6,
                  cursor="hand2", command=lambda: self.log.clear()
                  ).pack(side="right", padx=4)

        self.log = LogBox(f, height=16)
        self.log.pack(fill="both", expand=True, padx=14, pady=(0, 10))

    def _build_tree(self):
        self.log.clear()
        subj     = self._subj_var.get()
        deadline = datetime.now() + timedelta(days=14)

        if self._type_var.get() == "intensive":
            self._tree_root = PlanTreeBuilder.build_intensive(subj, deadline)
        else:
            self._tree_root = PlanTreeBuilder.build_relaxed(subj, deadline)

        self.log.write(self._tree_root.operation())
        self.log.write(f"\n  Задач: {self._tree_root.get_task_count()}  |  "
                       f"Минут: {self._tree_root.get_total_minutes()}  |  "
                       f"Выполнено: {self._tree_root.get_completed_count()}")
        self._set_status(f"🌲 Composite: построено дерево для [{subj}]")

    def _complete_first(self):
        if not self._tree_root:
            messagebox.showinfo("Composite", "Сначала постройте дерево!")
            return
        leaves = self._tree_root.get_all_task_leaves()
        if leaves:
            leaves[0].task.completed = True
            self.log.clear()
            self.log.write(self._tree_root.operation())
            self.log.write(f"\n  ✅ Выполнено: {self._tree_root.get_completed_count()}"
                           f"/{self._tree_root.get_task_count()}")
            self._set_status("🌲 Composite: задача отмечена выполненной")



class DecoratorSubTab:

    def __init__(self, nb, manager, set_status_cb, refresh_stats_cb):
        self.manager        = manager
        self._set_status    = set_status_cb
        self._refresh_stats = refresh_stats_cb

        self.frame = tk.Frame(nb)
        nb.add(self.frame, text=" 🎀 Decorator ")
        self._build()

    def _build(self):
        f = self.frame

        tk.Label(f, text="DECORATOR — динамическое добавление обязанностей",
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14, pady=(10, 0))
        tk.Label(f,
                 text="Выберите базовую задачу и «наденьте» декораторы в любой комбинации.\n"
                      "Код LectureTask / PracticeTask / RevisionTask не меняется.",
                 font=("Segoe UI", 9), fg="#555", justify="left"
                 ).pack(anchor="w", padx=14, pady=(2, 8))

        ctrl = tk.Frame(f)
        ctrl.pack(fill="x", padx=14, pady=(0, 6))

        tk.Label(ctrl, text="Задача:", font=("Segoe UI", 10)).grid(
            row=0, column=0, sticky="w", padx=(0, 6))
        self._base_var = tk.StringVar(value="Лекция")
        ttk.Combobox(ctrl, textvariable=self._base_var,
                     values=["Лекция", "Практика", "Повторение"],
                     width=12, font=("Segoe UI", 10)).grid(row=0, column=1, padx=(0, 16))

        tk.Label(ctrl, text="Дедлайн (дней):", font=("Segoe UI", 10)).grid(
            row=0, column=2, sticky="w", padx=(0, 6))
        self._days_var = tk.IntVar(value=3)
        tk.Spinbox(ctrl, from_=1, to=30, textvariable=self._days_var,
                   width=5, font=("Segoe UI", 10)).grid(row=0, column=3, padx=(0, 16))

        tk.Label(ctrl, text="Сложность:", font=("Segoe UI", 10)).grid(
            row=0, column=4, sticky="w", padx=(0, 6))
        self._diff_var = tk.StringVar(value="средний")
        ttk.Combobox(ctrl, textvariable=self._diff_var,
                     values=["лёгкий", "средний", "сложный", "очень сложный"],
                     width=13, font=("Segoe UI", 10)).grid(row=0, column=5)

        dec_row = tk.Frame(f)
        dec_row.pack(fill="x", padx=14, pady=(0, 8))
        self._use_urgent   = tk.BooleanVar(value=True)
        self._use_logging  = tk.BooleanVar(value=True)
        self._use_reminder = tk.BooleanVar(value=True)
        self._use_diff     = tk.BooleanVar(value=True)

        for text, var in [
            ("🚨 UrgentDecorator",    self._use_urgent),
            ("📝 LoggingDecorator",   self._use_logging),
            ("🔔 ReminderDecorator",  self._use_reminder),
            ("🎯 DifficultyDecorator", self._use_diff),
        ]:
            tk.Checkbutton(dec_row, text=text, variable=var,
                           font=("Segoe UI", 10)).pack(side="left", padx=8)

        btn_row = tk.Frame(f)
        btn_row.pack(fill="x", padx=14, pady=(0, 6))
        tk.Button(btn_row, text="▶ Выполнить задачу (execute)",
                  font=("Segoe UI", 10, "bold"), relief="flat", padx=12, pady=7,
                  cursor="hand2", command=self._run_decor
                  ).pack(side="left", padx=(0, 8))
        tk.Button(btn_row, text="➕ Добавить в сессию",
                  font=("Segoe UI", 10), relief="flat", padx=10, pady=7,
                  cursor="hand2", command=self._add_to_session
                  ).pack(side="left", padx=(0, 8))
        tk.Button(btn_row, text="🗑 Очистить лог",
                  font=("Segoe UI", 9), relief="flat", padx=8, pady=7,
                  cursor="hand2", command=lambda: self.log.clear()
                  ).pack(side="right")

        self.log = LogBox(f, height=13)
        self.log.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        self._last_task = None

    def _make_task(self):
        deadline = datetime.now() + timedelta(days=self._days_var.get())
        btype    = self._base_var.get()
        creators = {"Лекция": LectureTask, "Практика": PracticeTask, "Повторение": RevisionTask}
        titles   = {"Лекция": "Теория интегралов", "Практика": "Задачи Ньютона",
                    "Повторение": "Повторение формул"}
        subjs    = {"Лекция": "Математика", "Практика": "Физика", "Повторение": "Химия"}
        task = creators[btype](titles[btype], subjs[btype], 60, deadline)

        if self._use_diff.get():
            task = DifficultyDecorator(task, level=self._diff_var.get())
        if self._use_reminder.get():
            task = ReminderDecorator(task, remind_days_before=5)
        if self._use_logging.get():
            task = LoggingDecorator(task)
        if self._use_urgent.get():
            task = UrgentDecorator(task, reason="Дедлайн близко!")
        return task

    def _run_decor(self):
        self.log.clear()
        import io, contextlib
        buf = io.StringIO()
        self._last_task = self._make_task()
        with contextlib.redirect_stdout(buf):
            result = self._last_task.execute()
        for line in buf.getvalue().splitlines():
            self.log.write(line)
        for line in result.splitlines():
            self.log.write(line)
        self.log.write("\n── get_info() ──")
        for k, v in self._last_task.get_info().items():
            self.log.write(f"  {k:12}: {v}")
        self._set_status("🎀 Decorator: задача выполнена с декораторами")

    def _add_to_session(self):
        if not self._last_task:
            self._run_decor()
        self.manager.add_task(self._last_task)
        self.log.write(f"\n  ✅ Задача добавлена в сессию. "
                       f"Всего: {self.manager.get_statistics()['total_tasks']}")
        self._refresh_stats()
        self._set_status("🎀 Decorator: декорированная задача добавлена в сессию")
        self._last_task = None



class ProxySubTab:

    def __init__(self, nb, manager):
        self.manager  = manager
        self._real    = RealSessionManager()

        self.frame = tk.Frame(nb)
        nb.add(self.frame, text=" 🛡 Proxy ")
        self._build()

    def _build(self):
        f = self.frame

        tk.Label(f, text="PROXY — контроль доступа к StudySessionManager",
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14, pady=(10, 0))
        tk.Label(f,
                 text="Три вида заместителей: Protection (права), "
                      "Caching (кэш статистики), Logging (аудит).\n"
                      "RealSubject (Singleton) не меняется.",
                 font=("Segoe UI", 9), fg="#555", justify="left"
                 ).pack(anchor="w", padx=14, pady=(2, 8))

        prot_f = tk.LabelFrame(f, text=" 🔑  ProtectionProxy — выберите роль ",
                               font=("Segoe UI", 10, "bold"), padx=8, pady=6)
        prot_f.pack(fill="x", padx=14, pady=(0, 6))

        self._role_var = tk.StringVar(value="student")
        for role in ["student", "teacher", "admin"]:
            tk.Radiobutton(prot_f, text=role, variable=self._role_var,
                           value=role, font=("Segoe UI", 10)).pack(side="left", padx=6)

        btn_prot = tk.Frame(prot_f)
        btn_prot.pack(side="right")
        for label, action in [("get_tasks", "get"), ("add_task", "add"),
                               ("remove_task", "remove")]:
            tk.Button(btn_prot, text=label,
                      font=("Segoe UI", 9), relief="flat", padx=6, pady=4,
                      cursor="hand2",
                      command=lambda a=action: self._prot_action(a)
                      ).pack(side="left", padx=2)

        cache_f = tk.LabelFrame(f, text=" ⚡  CachingProxy — get_statistics() ",
                                font=("Segoe UI", 10, "bold"), padx=8, pady=6)
        cache_f.pack(fill="x", padx=14, pady=(0, 6))

        self._caching = CachingProxy(self._real, ttl_seconds=5)
        btn_cache = tk.Frame(cache_f)
        btn_cache.pack(fill="x")
        tk.Button(btn_cache, text="📊 get_statistics() (×3 подряд)",
                  font=("Segoe UI", 10), relief="flat", padx=10, pady=4,
                  cursor="hand2", command=self._cache_demo
                  ).pack(side="left", padx=4)
        tk.Button(btn_cache, text="🔄 Сбросить кэш",
                  font=("Segoe UI", 10), relief="flat", padx=10, pady=4,
                  cursor="hand2", command=self._cache_invalidate
                  ).pack(side="left")

        log_f = tk.LabelFrame(f, text=" 📋  LoggingProxy — аудит обращений ",
                              font=("Segoe UI", 10, "bold"), padx=8, pady=6)
        log_f.pack(fill="x", padx=14, pady=(0, 6))

        self._lproxy = LoggingProxy(self._real)
        btn_log = tk.Frame(log_f)
        btn_log.pack(fill="x")
        for label, action in [("get_stats", "stats"), ("get_tasks", "tasks"),
                               ("get_theme", "theme")]:
            tk.Button(btn_log, text=label,
                      font=("Segoe UI", 10), relief="flat", padx=8, pady=4,
                      cursor="hand2",
                      command=lambda a=action: self._log_action(a)
                      ).pack(side="left", padx=4)
        tk.Button(btn_log, text="📋 Показать аудит",
                  font=("Segoe UI", 10), relief="flat", padx=8, pady=4,
                  cursor="hand2", command=self._show_audit
                  ).pack(side="left", padx=8)

        btn_row = tk.Frame(f)
        btn_row.pack(fill="x", padx=14, pady=(2, 4))
        tk.Button(btn_row, text="🗑 Очистить лог",
                  font=("Segoe UI", 9), relief="flat", padx=8, pady=4,
                  cursor="hand2", command=lambda: self.log.clear()
                  ).pack(side="right")

        self.log = LogBox(f, height=8)
        self.log.pack(fill="both", expand=True, padx=14, pady=(0, 10))

    def _prot_action(self, action: str):
        role  = self._role_var.get()
        proxy = ProtectionProxy(self._real, role=role)
        self.log.write(f"\n[ProtectionProxy] role={role!r}, action={action!r}")

        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            if action == "get":
                tasks = proxy.get_all_tasks()
                self.log.write(f"  → get_all_tasks(): {len(tasks)} задач")
            elif action == "add":
                dl   = datetime.now() + timedelta(days=3)
                task = LectureTask(f"Тест-задача ({role})", "Тест", 30, dl)
                proxy.add_task(task)
                self.log.write(f"  → add_task(): выполнено без ошибок")
            elif action == "remove":
                proxy.remove_task("fake-id")
                self.log.write("  → remove_task(): вызов выполнен")

        for line in buf.getvalue().splitlines():
            self.log.write("  " + line)

    def _cache_demo(self):
        self.log.write("\n[CachingProxy] 3 вызова get_statistics():")
        import io, contextlib
        for i in range(1, 4):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                stats = self._caching.get_statistics()
            line = buf.getvalue().strip()
            self.log.write(f"  #{i}: {line}  (tasks={stats['total_tasks']})")
        self.log.write(f"  Итого: {self._caching.cache_stats()}")

    def _cache_invalidate(self):
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self._caching.invalidate()
        self.log.write(f"\n[CachingProxy] {buf.getvalue().strip()}")

    def _log_action(self, action: str):
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            if action == "stats":
                self._lproxy.get_statistics()
            elif action == "tasks":
                self._lproxy.get_all_tasks()
            elif action == "theme":
                self._lproxy.get_theme()
        for line in buf.getvalue().splitlines():
            self.log.write(line)

    def _show_audit(self):
        audit = self._lproxy.get_audit()
        self.log.write(f"\n[LoggingProxy] Аудит ({len(audit)} записей):")
        for e in audit[-10:]:
            self.log.write(f"  [{e['time']}] {e['action']}"
                           + (f" | {e['detail']}" if e.get("detail") else ""))



class FacadeSubTab:

    def __init__(self, nb, manager, set_status_cb, refresh_stats_cb):
        self.manager        = manager
        self._set_status    = set_status_cb
        self._refresh_stats = refresh_stats_cb
        self._facade        = SmartStudyFacade(theme="light")

        self.frame = tk.Frame(nb)
        nb.add(self.frame, text=" 🏛 Facade ")
        self._build()

    def _build(self):
        f = self.frame

        tk.Label(f, text="FACADE — единый интерфейс ко всей подсистеме",
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14, pady=(10, 0))
        tk.Label(f,
                 text="SmartStudyFacade скрывает Singleton + Factory + Builder + "
                      "Prototype + AbstractFactory.\nКлиент вызывает один объект.",
                 font=("Segoe UI", 9), fg="#555", justify="left"
                 ).pack(anchor="w", padx=14, pady=(2, 8))

        ctrl = tk.Frame(f)
        ctrl.pack(fill="x", padx=14, pady=(0, 6))

        tk.Label(ctrl, text="Предмет:", font=("Segoe UI", 10)).grid(
            row=0, column=0, sticky="w", padx=(0, 4))
        self._subj_var = tk.StringVar(value="Математика")
        ttk.Combobox(ctrl, textvariable=self._subj_var,
                     values=["Математика", "Физика", "Химия", "История", "Информатика"],
                     width=12, font=("Segoe UI", 10)).grid(row=0, column=1, padx=(0, 14))

        tk.Label(ctrl, text="Дней:", font=("Segoe UI", 10)).grid(
            row=0, column=2, sticky="w", padx=(0, 4))
        self._days_var = tk.IntVar(value=10)
        tk.Spinbox(ctrl, from_=3, to=60, textvariable=self._days_var,
                   width=5, font=("Segoe UI", 10)).grid(row=0, column=3, padx=(0, 14))

        self._ptype_var = tk.StringVar(value="intensive")
        tk.Radiobutton(ctrl, text="⚡ Интенсивный",
                       variable=self._ptype_var, value="intensive",
                       font=("Segoe UI", 10)).grid(row=0, column=4)
        tk.Radiobutton(ctrl, text="🌿 Расслабленный",
                       variable=self._ptype_var, value="relaxed",
                       font=("Segoe UI", 10)).grid(row=0, column=5, padx=(0, 14))

        btn_row = tk.Frame(f)
        btn_row.pack(fill="x", padx=14, pady=(0, 6))

        for label, cmd in [
            ("📋 create_full_session()",    self._full_session),
            ("🔁 clone_and_create_task()",  self._clone_task),
            ("🌙 switch_theme(dark)",       lambda: self._switch("dark")),
            ("☀️ switch_theme(light)",      lambda: self._switch("light")),
            ("📊 get_session_summary()",    self._summary),
        ]:
            tk.Button(btn_row, text=label,
                      font=("Segoe UI", 10), relief="flat", padx=8, pady=6,
                      cursor="hand2", command=cmd
                      ).pack(side="left", padx=3)

        tk.Button(btn_row, text="🗑 Очистить",
                  font=("Segoe UI", 9), relief="flat", padx=8, pady=6,
                  cursor="hand2", command=lambda: self.log.clear()
                  ).pack(side="right", padx=4)

        self.log = LogBox(f, height=14)
        self.log.pack(fill="both", expand=True, padx=14, pady=(0, 10))

    def _full_session(self):
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            result = self._facade.create_full_session(
                self._subj_var.get(),
                days=self._days_var.get(),
                daily_hours=3.0,
                plan_type=self._ptype_var.get()
            )
        for line in buf.getvalue().splitlines():
            self.log.write(line)
        self.log.write(f"\n  {result['summary']}")
        self.log.write(f"  Тип плана:     {result['plan'].plan_type}")
        self.log.write(f"  Задач создано: {len(result['tasks'])}")
        self._set_status("🏛 Facade: create_full_session выполнен")
        self._refresh_stats()

    def _clone_task(self):
        keys = ["practice_hard", "revision_quick", "lecture_deep"]
        import random
        key = random.choice(keys)
        msg = self._facade.clone_and_create_task(
            key, self._subj_var.get(), days_until_deadline=self._days_var.get())
        self.log.write(f"\n  {msg}")
        self._set_status("🏛 Facade: clone_and_create_task выполнен")
        self._refresh_stats()

    def _switch(self, theme: str):
        t = self._facade.switch_theme(theme)
        self.log.write(f"\n  switch_theme('{theme}'): тема={t['theme']}, фон={t['root_bg']}")
        self._set_status(f"🏛 Facade: тема переключена → {theme}")

    def _summary(self):
        self.log.clear()
        self.log.write(self._facade.get_session_summary())
        self._set_status("🏛 Facade: get_session_summary выполнен")

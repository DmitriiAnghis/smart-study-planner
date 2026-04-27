import tkinter as tk
from tkinter import ttk
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from patterns.singleton        import StudySessionManager
from patterns.factory_method   import LectureTaskCreator, PracticeTaskCreator, RevisionTaskCreator
from patterns.abstract_factory import LightThemeFactory, ThemeManager
from patterns.builder          import PlannerDirector, IntensivePlanBuilder, RelaxedPlanBuilder
from patterns.prototype        import TemplateRegistry
from patterns.structural.facade import SmartStudyFacade

from gui.tabs.tasks_tab     import TasksTab
from gui.tabs.plans_tab     import PlansTab
from gui.tabs.templates_tab import TemplatesTab
from gui.tabs.stats_tab     import StatsTab
from gui.theme              import ThemeController


class SmartStudyPlannerApp:

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("📚 Smart Study Planner")
        self.root.geometry("1100x720")
        self.root.minsize(900, 600)

        self.manager       = StudySessionManager.get_instance()
        self.theme_manager = ThemeManager(LightThemeFactory())

        self._creators = {
            "Лекция":     LectureTaskCreator(),
            "Практика":   PracticeTaskCreator(),
            "Повторение": RevisionTaskCreator(),
        }

        self.director          = PlannerDirector()
        self.template_registry = TemplateRegistry()
        self._facade           = SmartStudyFacade(theme="light")

        self._build_ui()
        self.theme_ctrl.apply()
        self._refresh_all()

        self.stats_tab.set_role_callback(self._apply_role)
        self._apply_role("admin")

    def _build_ui(self):
        self.header = tk.Frame(self.root, height=64)
        self.header.pack(fill="x", side="top")
        self.header.pack_propagate(False)

        self.title_label = tk.Label(
            self.header,
            text="📚  Smart Study Planner",
            font=("Segoe UI", 17, "bold"), padx=20)
        self.title_label.pack(side="left", pady=12)

        self.facade_btn = tk.Button(
            self.header,
            text="⚡  Быстрый старт",
            font=("Segoe UI", 10, "bold"),
            relief="flat", padx=14, pady=6,
            cursor="hand2",
            command=self._facade_quick_start)
        self.facade_btn.pack(side="left", padx=(0, 4), pady=12)

        self._facade_label = tk.Label(
            self.header,
            text="Facade",
            font=("Segoe UI", 7), fg="#888")
        self._facade_label.pack(side="left", pady=12)

        self.theme_btn = tk.Button(
            self.header,
            text="🌙  Тёмная тема",
            font=("Segoe UI", 10),
            relief="flat", padx=14, pady=6,
            cursor="hand2",
            command=self._toggle_theme)
        self.theme_btn.pack(side="right", padx=16, pady=12)

        style = ttk.Style()
        style.theme_use("clam")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=14, pady=(4, 0))

        self.tasks_tab = TasksTab(
            self.notebook, self.manager, self._creators,
            self._set_status, self._refresh_stats)

        self.plans_tab = PlansTab(
            self.notebook, self.manager, self.director,
            IntensivePlanBuilder, RelaxedPlanBuilder,
            self._set_status, self._refresh_stats)

        self.templates_tab = TemplatesTab(
            self.notebook, self.manager, self._creators,
            self.template_registry, self._set_status,
            self._refresh_stats, self.tasks_tab.refresh)

        self.stats_tab = StatsTab(self.notebook, self.manager)

        self.statusbar = tk.Label(
            self.root,
            text="  ✅  Сессия запущена",
            font=("Segoe UI", 9), anchor="w", padx=10)
        self.statusbar.pack(fill="x", side="bottom", ipady=4)

        self.theme_ctrl = ThemeController(
            root          = self.root,
            theme_manager = self.theme_manager,
            manager       = self.manager,
            header        = self.header,
            title_label   = self.title_label,
            theme_btn     = self.theme_btn,
            statusbar     = self.statusbar,
            notebook      = self.notebook,
            tabs          = [
                self.tasks_tab.frame,
                self.plans_tab.frame,
                self.templates_tab.frame,
                self.stats_tab.frame,
            ],
            text_widgets  = [
                self.plans_tab.plan_detail,
                self.stats_tab.log_text,
            ],
            stat_cards            = self.stats_tab.stat_cards,
            extra_header_widgets  = [self.facade_btn, self._facade_label],
        )

    def _facade_quick_start(self):
        dlg = _QuickStartDialog(self.root)
        self.root.wait_window(dlg)

        if not dlg.result:
            return

        subject, days, plan_type = dlg.result

        result = self._facade.create_full_session(
            subject, days=days, daily_hours=3.0, plan_type=plan_type)

        self._refresh_all()
        self._set_status(f"⚡ Facade: {result['summary']}")

    def _apply_role(self, role: str):
        can_create = role in ("teacher", "admin")
        can_delete = role == "admin"
        can_done   = role in ("teacher", "admin")

        self.tasks_tab.btn_create.configure(
            state="normal" if can_create else "disabled")
        self.tasks_tab.btn_delete.configure(
            state="normal" if can_delete else "disabled")
        self.tasks_tab.btn_done.configure(
            state="normal" if can_done else "disabled")
        self.plans_tab.btn_delete.configure(
            state="normal" if can_delete else "disabled")

        emoji = {"student": "👨‍🎓", "teacher": "👨‍🏫", "admin": "🔑"}.get(role, "")
        self._set_status(
            f"🛡 Proxy: роль {emoji} {role} — "
            f"{'полный доступ' if role == 'admin' else 'ограниченный доступ'}")

    def _toggle_theme(self):
        theme = self.manager.get_theme()
        self._facade.switch_theme("dark" if theme == "light" else "light")
        self.theme_ctrl.toggle(self._set_status)

    def _refresh_all(self):
        self.tasks_tab.refresh()
        self.plans_tab.refresh()
        self.templates_tab.refresh()
        self.stats_tab.refresh()

    def _refresh_stats(self):
        self.stats_tab.refresh()

    def _set_status(self, msg: str):
        self.statusbar.configure(text=f"  {msg}")
        self.root.after(5000, lambda: self.statusbar.configure(
            text="  ✅  Готово"))


# ── ДИАЛОГ БЫСТРОГО СТАРТА ───────────────────────────────────────────────────

class _QuickStartDialog(tk.Toplevel):

    def __init__(self, parent):
        super().__init__(parent)
        self.title("⚡ Быстрый старт (Facade)")
        self.resizable(False, False)
        self.grab_set()
        self.result = None

        x = parent.winfo_x() + 300
        y = parent.winfo_y() + 200
        self.geometry(f"+{x}+{y}")

        subjects = ["Математика", "Физика", "Химия", "Биология",
                    "История", "Информатика", "Литература"]

        tk.Label(self, text="⚡  Быстрый старт",
                 font=("Segoe UI", 13, "bold")).pack(padx=14, pady=(14, 2))

        tk.Label(self,
                 text="Facade запустит Builder + Factory + Singleton\n"
                      "и результат появится в Tasks и Plans",
                 font=("Segoe UI", 9), fg="#666").pack(padx=14, pady=(0, 8))

        tk.Label(self, text="Предмет:", font=("Segoe UI", 10)).pack(anchor="w", padx=14)
        self._subj = tk.StringVar(value=subjects[0])
        ttk.Combobox(self, textvariable=self._subj,
                     values=subjects, width=22,
                     font=("Segoe UI", 10)).pack(padx=14, pady=(2, 8))

        tk.Label(self, text="Дней до экзамена:", font=("Segoe UI", 10)).pack(anchor="w", padx=14)
        self._days = tk.IntVar(value=14)
        tk.Spinbox(self, from_=3, to=60, textvariable=self._days,
                   width=8, font=("Segoe UI", 10)).pack(anchor="w", padx=14, pady=(2, 8))

        tk.Label(self, text="Тип плана:", font=("Segoe UI", 10)).pack(anchor="w", padx=14)
        self._ptype = tk.StringVar(value="intensive")
        row = tk.Frame(self)
        row.pack(padx=14, pady=(2, 12))
        tk.Radiobutton(row, text="⚡ Интенсивный",
                       variable=self._ptype, value="intensive",
                       font=("Segoe UI", 10)).pack(side="left")
        tk.Radiobutton(row, text="🌿 Расслабленный",
                       variable=self._ptype, value="relaxed",
                       font=("Segoe UI", 10)).pack(side="left", padx=8)

        btn_row = tk.Frame(self)
        btn_row.pack(pady=(0, 14))
        tk.Button(btn_row, text="⚡  Запустить",
                  font=("Segoe UI", 11, "bold"),
                  relief="flat", padx=16, pady=8,
                  cursor="hand2", command=self._ok).pack(side="left", padx=6)
        tk.Button(btn_row, text="Отмена",
                  font=("Segoe UI", 10),
                  relief="flat", padx=12, pady=8,
                  cursor="hand2", command=self.destroy).pack(side="left")

    def _ok(self):
        self.result = (self._subj.get(), self._days.get(), self._ptype.get())
        self.destroy()
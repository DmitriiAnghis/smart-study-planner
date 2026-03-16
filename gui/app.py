import tkinter as tk
from tkinter import ttk
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Паттерны
from patterns.singleton        import StudySessionManager
from patterns.factory_method   import LectureTaskCreator, PracticeTaskCreator, RevisionTaskCreator
from patterns.abstract_factory import LightThemeFactory, ThemeManager
from patterns.builder          import PlannerDirector, IntensivePlanBuilder, RelaxedPlanBuilder
from patterns.prototype        import TemplateRegistry

# GUI компоненты
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

        # ── SINGLETON ────────────────────────────────────────────────────────
        self.manager = StudySessionManager.get_instance()

        # ── ABSTRACT FACTORY ─────────────────────────────────────────────────
        self.theme_manager = ThemeManager(LightThemeFactory())

        # ── FACTORY METHOD ───────────────────────────────────────────────────
        self._creators = {
            "Лекция":     LectureTaskCreator(),
            "Практика":   PracticeTaskCreator(),
            "Повторение": RevisionTaskCreator(),
        }

        # ── BUILDER ──────────────────────────────────────────────────────────
        self.director = PlannerDirector()

        # ── PROTOTYPE ────────────────────────────────────────────────────────
        self.template_registry = TemplateRegistry()

        # Строим интерфейс
        self._build_ui()
        self.theme_ctrl.apply()
        self._refresh_all()

    def _build_ui(self):
        # ── ШАПКА ────────────────────────────────────────────────────────────
        self.header = tk.Frame(self.root, height=64)
        self.header.pack(fill="x", side="top")
        self.header.pack_propagate(False)

        self.title_label = tk.Label(
            self.header,
            text="📚  Smart Study Planner",
            font=("Segoe UI", 17, "bold"), padx=20)
        self.title_label.pack(side="left", pady=12)

        self.theme_btn = tk.Button(
            self.header,
            text="🌙  Тёмная тема",
            font=("Segoe UI", 10),
            relief="flat", padx=14, pady=6,
            cursor="hand2",
            command=self._toggle_theme)
        self.theme_btn.pack(side="right", padx=16, pady=12)

        # ── NOTEBOOK ─────────────────────────────────────────────────────────
        style = ttk.Style()
        style.theme_use("clam")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=14, pady=(4, 0))

        # ── ВКЛАДКИ ──────────────────────────────────────────────────────────
        self.tasks_tab = TasksTab(
            self.notebook, self.manager, self._creators,
            self._set_status, self._refresh_stats)

        self.plans_tab = PlansTab(
            self.notebook, self.manager, self.director,
            IntensivePlanBuilder, RelaxedPlanBuilder,
            self._set_status, self._refresh_stats)

        self.templates_tab = TemplatesTab(
            self.notebook, self.manager, self._creators,
            self.template_registry, self._set_status, self._refresh_stats, self.tasks_tab.refresh)

        self.stats_tab = StatsTab(self.notebook, self.manager)

        # ── СТАТУСБАР ────────────────────────────────────────────────────────
        self.statusbar = tk.Label(
            self.root,
            text="  ✅  Сессия запущена",
            font=("Segoe UI", 9), anchor="w", padx=10)
        self.statusbar.pack(fill="x", side="bottom", ipady=4)

        # ── THEME CONTROLLER ─────────────────────────────────────────────────
        self.theme_ctrl = ThemeController(
            root         = self.root,
            theme_manager= self.theme_manager,
            manager      = self.manager,
            header       = self.header,
            title_label  = self.title_label,
            theme_btn    = self.theme_btn,
            statusbar    = self.statusbar,
            notebook     = self.notebook,
            tabs         = [
                self.tasks_tab.frame,
                self.plans_tab.frame,
                self.templates_tab.frame,
                self.stats_tab.frame,
            ],
            text_widgets = [
                self.plans_tab.plan_detail,
                self.stats_tab.log_text,
            ],
            stat_cards   = self.stats_tab.stat_cards,
        )

    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    

    def _toggle_theme(self):
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
        self.root.after(4000, lambda: self.statusbar.configure(
            text="  ✅  Готово"))
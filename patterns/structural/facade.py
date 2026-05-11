"""
================================================================================
  ПАТТЕРН FACADE (ФАСАД) — Структурный паттерн
  Источник: GoF «Design Patterns» стр. 185-193
================================================================================

  НАЗНАЧЕНИЕ (GoF, стр. 185):
    Предоставляет унифицированный интерфейс к множеству интерфейсов
    подсистемы. Определяет интерфейс более высокого уровня,
    упрощающий использование подсистемы.

  СХЕМА (GoF, стр. 185):

                           ┌──────────┐
                           │  Facade  │
                           └────┬─────┘
                                │ знает, каким классам адресовать запрос
                                │
          ┌─────────────────────┼──────────────────────────┐
          ↓          ↓          ↓           ↓              ↓
      ┌────────┐ ┌────────┐ ┌───────┐ ┌─────────┐    ┌─────────┐
      │Singleton│ │Factory │ │Builder│ │Prototype│    │Abstract │
      │Manager │ │Method  │ │Director││Registry │    │Factory  │
      └────────┘ └────────┘ └───────┘ └─────────┘    └─────────┘

  УЧАСТНИКИ (GoF, стр. 185):
    • Facade        — знает, каким классам подсистемы адресовать запрос;
                      делегирует запросы нужным объектам
    • Классы подсистемы — реализуют функциональность;
                          не знают о существовании Facade

  КАК ВСТРОЕН В ПРОЕКТ:
    Подсистема = все 5 существующих паттернов проекта:
      StudySessionManager  (Singleton)
      LectureTaskCreator   (Factory Method)
      PlannerDirector      (Builder)
      TemplateRegistry     (Prototype)
      ThemeManager         (Abstract Factory)

    Facade = SmartStudyFacade
    Один метод create_full_session() запускает всю систему.
    GUI (app.py) может использовать только фасад — не знать о подсистемах.
================================================================================
"""

from datetime import datetime, timedelta
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from patterns.singleton      import StudySessionManager
from patterns.factory_method import (LectureTaskCreator, PracticeTaskCreator,
                                     RevisionTaskCreator)
from patterns.builder        import PlannerDirector, IntensivePlanBuilder, RelaxedPlanBuilder
from patterns.prototype      import TemplateRegistry
from patterns.abstract_factory import LightThemeFactory, DarkThemeFactory, ThemeManager


class SmartStudyFacade:
    """
    Facade (GoF).
    Предоставляет простой высокоуровневый интерфейс ко всей подсистеме
    Smart Study Planner, которая состоит из 5 паттернов.

    «Знает», каким объектам подсистемы адресовать каждый запрос.
    Клиент (GUI, скрипт, тест) видит только методы этого класса.
    Классы подсистемы ничего не знают о Facade — не хранят на него ссылок.
    """

    def __init__(self, theme: str = "light"):
        # Facade создаёт и хранит все объекты подсистемы
        self._manager   = StudySessionManager.get_instance()   # Singleton

        factory         = LightThemeFactory() if theme == "light" else DarkThemeFactory()
        self._theme_mgr = ThemeManager(factory)                # Abstract Factory

        self._creators  = {                                    # Factory Method
            "Лекция":     LectureTaskCreator(),
            "Практика":   PracticeTaskCreator(),
            "Повторение": RevisionTaskCreator(),
        }

        self._director  = PlannerDirector()                    # Builder
        self._registry  = TemplateRegistry()                   # Prototype

    # ─────────────────────────────────────────────────────────────────────
    #  ВЫСОКОУРОВНЕВЫЙ МЕТОД 1 — запустить полную учебную сессию
    #  Внутри координирует Singleton + Factory Method + Builder
    # ─────────────────────────────────────────────────────────────────────
    def create_full_session(self, subject: str, days: int,
                            daily_hours: float = 3.0,
                            plan_type: str = "intensive") -> dict:
        """
        Главный фасадный метод.
        Клиент передаёт 3 параметра — фасад делает всё остальное:
          1. Создаёт план через Builder
          2. Создаёт типовые задачи через Factory Method
          3. Регистрирует всё в Singleton
        Возвращает сводку — клиенту не нужно знать о подсистемах.
        """
        exam_date = datetime.now() + timedelta(days=days)

        # 1. Builder — создаём учебный план
        builder = IntensivePlanBuilder() if plan_type == "intensive" else RelaxedPlanBuilder()
        self._director.set_builder(builder)
        plan = self._director.build_full_plan(subject, exam_date, daily_hours)

        # 2. Factory Method — создаём задачи для плана
        tasks_created = []
        deadline = exam_date - timedelta(days=2)
        for task_info in plan.tasks[:3]:   # берём первые 3 задачи из плана
            ttype   = task_info["type"]
            creator = self._creators.get(ttype, self._creators["Лекция"])
            task    = creator.create_and_register(
                task_info["title"], subject, task_info["duration"], deadline
            )
            tasks_created.append(task)

        # 3. Singleton — получаем актуальную статистику
        stats = self._manager.get_statistics()

        return {
            "plan":    plan,
            "tasks":   tasks_created,
            "stats":   stats,
            "summary": (f"Сессия: [{subject}] | план '{plan.plan_type}' | "
                        f"{len(tasks_created)} задач | "
                        f"итого задач: {stats['total_tasks']}")
        }

    # ─────────────────────────────────────────────────────────────────────
    #  ВЫСОКОУРОВНЕВЫЙ МЕТОД 2 — клонировать шаблон и сразу создать задачу
    #  Внутри: Prototype + Factory Method + Singleton
    # ─────────────────────────────────────────────────────────────────────
    def clone_and_create_task(self, template_key: str,
                               subject: str, days_until_deadline: int) -> str:
        """
        Клонировать шаблон (Prototype) и сразу зарегистрировать задачу.
        Клиент передаёт ключ шаблона и предмет — фасад делает остальное.
        """
        try:
            cloned   = self._registry.clone(template_key).customize(subject=subject)
            deadline = datetime.now() + timedelta(days=days_until_deadline)
            td       = cloned.to_task_dict(deadline)
            creator  = self._creators.get(cloned.task_type, self._creators["Лекция"])
            task     = creator.create_and_register(
                td["title"], td["subject"], td["duration"], td["deadline"]
            )
            return f"✅ Клонирован '{template_key}' → задача '{task.title}'"
        except KeyError as e:
            return f"❌ Ошибка: {e}"

    # ─────────────────────────────────────────────────────────────────────
    #  ВЫСОКОУРОВНЕВЫЙ МЕТОД 3 — переключить тему и получить конфиг
    #  Внутри: Abstract Factory + Singleton
    # ─────────────────────────────────────────────────────────────────────
    def switch_theme(self, theme: str) -> dict:
        """
        Переключить тему одним вызовом.
        Клиент не знает ни об Abstract Factory, ни о ThemeManager.
        """
        factory = LightThemeFactory() if theme == "light" else DarkThemeFactory()
        self._theme_mgr.switch_factory(factory)
        cfg = self._theme_mgr.get_widget_configs()
        return {"theme": cfg["theme_name"], "root_bg": cfg["root_bg"]}

    # ─────────────────────────────────────────────────────────────────────
    #  ВЫСОКОУРОВНЕВЫЙ МЕТОД 4 — получить полную сводку сессии
    # ─────────────────────────────────────────────────────────────────────
    def get_session_summary(self) -> str:
        stats = self._manager.get_statistics()
        plans = self._manager.get_all_plans()
        lines = [
            "╔══ СВОДКА СЕССИИ ══╗",
            f"  Задач всего:    {stats['total_tasks']}",
            f"  Выполнено:      {stats['completed_tasks']}",
            f"  Прогресс:       {stats['progress_percent']}%",
            f"  Планов:         {stats['total_plans']}",
            f"  Тема:           {stats['theme']}",
        ]
        if plans:
            lines.append("  Планы:")
            for p in plans:
                lines.append(f"    • [{p.plan_type}] {p.subject}")
        lines.append("╚═══════════════════╝")
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
#  ДЕМОНСТРАЦИЯ
# ─────────────────────────────────────────────────────────────────────────────
def demo():
    print("=" * 65)
    print("  FACADE — интеграция в Smart Study Planner")
    print("=" * 65)
    print("""
  БЕЗ Facade клиент должен сам работать с:
    StudySessionManager + LectureTaskCreator + PlannerDirector
    + TemplateRegistry + ThemeManager — 5 подсистем, много кода.

  С Facade — один объект, простые вызовы.
""")

    facade = SmartStudyFacade(theme="light")

    print("📌 facade.create_full_session():")
    result = facade.create_full_session("Математика", days=14,
                                         daily_hours=3.0, plan_type="intensive")
    print(f"  {result['summary']}")
    print(f"  Тип плана: {result['plan'].plan_type}")
    print(f"  Задач создано: {len(result['tasks'])}")

    print("\n📌 facade.clone_and_create_task():")
    print(" ", facade.clone_and_create_task("practice_hard", "Физика",
                                             days_until_deadline=5))

    print("\n📌 facade.switch_theme():")
    t = facade.switch_theme("dark")
    print(f"  Тема: {t['theme']}, фон: {t['root_bg']}")

    print("\n📌 facade.get_session_summary():")
    print(facade.get_session_summary())

    print("\n✅ Клиент использовал только facade — подсистемы скрыты.")
    print("   Это и есть Facade.")
    print("=" * 65)


if __name__ == "__main__":
    demo()
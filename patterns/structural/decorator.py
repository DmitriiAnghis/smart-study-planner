"""
================================================================================
  ПАТТЕРН DECORATOR (ДЕКОРАТОР) — Структурный паттерн
  Источник: GoF «Design Patterns» стр. 175-184
================================================================================

  НАЗНАЧЕНИЕ (GoF, стр. 175):
    Динамически добавляет объекту новые обязанности.
    Декораторы — гибкая альтернатива порождению подклассов
    с целью расширения функциональности.

  СХЕМА (GoF, стр. 176):

      ┌──────────────────┐
      │   Component      │◄──────────────────────────────────┐
      │──────────────────│                                   │
      │ Operation()      │                                   │
      └────────┬─────────┘                                   │
               △                                             │
       ┌───────┴────────────────┐             component      │
       │                        │          ──────────────────>│
  ┌────┴──────────┐   ┌─────────┴────────┐
  │ConcreteComp.  │   │    Decorator     │
  │───────────────│   │──────────────────│
  │ Operation()   │   │ Operation() ○────┼──> component->Operation()
  └───────────────┘   └────────┬─────────┘
                                △
                    ┌───────────┴───────────┐
                    │                       │
           ┌────────┴──────┐       ┌────────┴──────────┐
           │ConcreteDecorA │       │ConcreteDecorB     │
           │───────────────│       │───────────────────│
           │ Operation()   │       │ Operation()       │
           │ addedState    │       │ AddedBehavior()   │
           └───────────────┘       └───────────────────┘

  УЧАСТНИКИ (GoF, стр. 176):
    • Component         — интерфейс, которому добавляют обязанности
    • ConcreteComponent — базовый объект (StudyTask из factory_method.py)
    • Decorator         — хранит ссылку «component», совпадает с его интерфейсом
    • ConcreteDecorator — добавляет конкретную обязанность

  КАК ВСТРОЕН В ПРОЕКТ:
    Component         = StudyTask (factory_method.py) — не меняем!
    ConcreteComponent = LectureTask / PracticeTask / RevisionTask
    Декораторы добавляют новое поведение поверх любой задачи:
      UrgentDecorator     — помечает задачу срочной (addedState: reason)
      LoggingDecorator    — логирует выполнение в StudySessionManager
      ReminderDecorator   — напоминание за N дней до дедлайна
      DifficultyDecorator — уровень сложности, пересчитывает duration
      DontWoryDecorator   — помечает задачу не срочной (пользовательский)
================================================================================
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from patterns.factory_method import (
    StudyTask, LectureTask, PracticeTask, RevisionTask,
)
from patterns.singleton import StudySessionManager


# ═══════════════════════════════════════════════════════════════════════════════
#  DECORATOR — абстрактный декоратор (GoF)
#  Хранит ссылку «component» и делегирует ему все вызовы
# ═══════════════════════════════════════════════════════════════════════════════
class TaskDecorator(StudyTask):
    """
    Decorator (GoF).
    Оборачивает любую StudyTask (Component).
    Интерфейс совпадает с Component — клиент (Treeview, Manager) не замечает замены.

    Ключевое: self._component — «component» из GoF-схемы стр.176.
    """

    def __init__(self, component: StudyTask):
        # Не вызываем StudyTask.__init__() — все данные берём из component
        object.__setattr__(self, '_component', component)

    # ── Делегирование всех свойств оригинала ─────────────────────────────
    @property
    def task_id(self):             return self._component.task_id
    @property
    def title(self):               return self._component.title
    @property
    def subject(self):             return self._component.subject
    @property
    def duration_minutes(self):    return self._component.duration_minutes
    @property
    def deadline(self):            return self._component.deadline
    @property
    def completed(self):           return self._component.completed
    @completed.setter
    def completed(self, v):        self._component.completed = v
    @property
    def priority(self):            return self._component.priority
    @property
    def created_at(self):          return self._component.created_at

    # ── Operation() — базовая реализация: просто делегируем (GoF) ────────
    def execute(self) -> str:
        return self._component.execute()

    def get_type(self) -> str:
        return self._component.get_type()

    def get_info(self) -> dict:
        return self._component.get_info()


# ═══════════════════════════════════════════════════════════════════════════════
#  CONCRETE DECORATOR — НЕ СРОЧНАЯ ЗАДАЧА (пользовательский)
# ═══════════════════════════════════════════════════════════════════════════════
class DontWoryDecorator(TaskDecorator):
    """
    Пользовательский декоратор.
    Помечает задачу не срочной — снижает приоритет до НИЗКИЙ.
    addedState: _mass (сообщение).
    """

    def __init__(self, component: StudyTask, mass: str = "Расслабься"):
        super().__init__(component)
        self._mass = mass

    def execute(self) -> str:
        base = self._component.execute()
        return base + f"\n   [НЕ СРОЧНО]: {self._mass}"

    def get_info(self) -> dict:
        info             = self._component.get_info()
        info["priority"] = "НИЗКИЙ"
        info["title"]    = f"  [НЕ СРОЧНО] {info['title']}"
        return info


# ═══════════════════════════════════════════════════════════════════════════════
#  CONCRETE DECORATOR A — СРОЧНАЯ ЗАДАЧА
#  addedState: _reason
# ═══════════════════════════════════════════════════════════════════════════════
class UrgentDecorator(TaskDecorator):
    """
    ConcreteDecoratorA (GoF).
    Добавляет обязанность: пометить задачу срочной.
    Форсирует приоритет ВЫСОКИЙ и добавляет пометку в заголовок.
    Код LectureTask / PracticeTask / RevisionTask — не меняется.
    """

    def __init__(self, component: StudyTask, reason: str = "Дедлайн скоро"):
        super().__init__(component)
        self._reason = reason      # addedState (GoF)

    def execute(self) -> str:
        base = self._component.execute()    # component->Operation()
        return base + f"\n  🚨 [СРОЧНО]: {self._reason}"

    def get_info(self) -> dict:
        info             = self._component.get_info()
        info["priority"] = "ВЫСОКИЙ"
        info["title"]    = f"🚨 {info['title']}"
        return info


# ═══════════════════════════════════════════════════════════════════════════════
#  CONCRETE DECORATOR B — ЛОГИРОВАНИЕ
#  addedState: _log (список событий выполнения)
# ═══════════════════════════════════════════════════════════════════════════════
class LoggingDecorator(TaskDecorator):
    """
    ConcreteDecoratorB (GoF).
    Добавляет обязанность: логировать каждый вызов execute()
    прямо в StudySessionManager (Singleton) — интеграция с существующим кодом проекта.
    """

    def __init__(self, component: StudyTask):
        super().__init__(component)
        self._log: list = []       # addedState (GoF)

    def execute(self) -> str:
        ts = datetime.now().strftime("%H:%M:%S")
        self._log.append({"time": ts, "task": self._component.title})

        # Реальная интеграция: пишем в Singleton StudySessionManager
        StudySessionManager.get_instance()._log_event(
            f"[Decorator/Log] Запущена задача: {self._component.title}"
        )

        result = self._component.execute()   # component->Operation()
        return result + f"\n  📝 [Лог] Зафиксировано в сессии в {ts}"

    def get_log(self) -> list:
        """AddedBehavior() — дополнительный метод, которого нет у Component."""
        return list(self._log)


# ═══════════════════════════════════════════════════════════════════════════════
#  CONCRETE DECORATOR C — НАПОМИНАНИЕ
# ═══════════════════════════════════════════════════════════════════════════════
class ReminderDecorator(TaskDecorator):
    """
    ConcreteDecoratorC (GoF).
    Добавляет обязанность: показывать напоминание когда дедлайн близко.
    «Надевается» поверх любого другого декоратора (матрёшка).
    """

    def __init__(self, component: StudyTask, remind_days_before: int = 2):
        super().__init__(component)
        self._remind_days = remind_days_before

    def execute(self) -> str:
        days_left = (self._component.deadline - datetime.now()).days
        result    = self._component.execute()
        if days_left <= self._remind_days:
            result += (f"\n  🔔 [Reminder] Осталось {days_left} дн. до дедлайна: "
                       f"'{self._component.title}'!")
        return result

    def get_info(self) -> dict:
        info      = self._component.get_info()
        days_left = (self._component.deadline - datetime.now()).days
        if days_left <= self._remind_days:
            info["title"] = f"🔔 {info['title']}"
        return info


# ═══════════════════════════════════════════════════════════════════════════════
#  CONCRETE DECORATOR D — УРОВЕНЬ СЛОЖНОСТИ
# ═══════════════════════════════════════════════════════════════════════════════
class DifficultyDecorator(TaskDecorator):
    """
    ConcreteDecoratorD (GoF).
    Добавляет уровень сложности и автоматически пересчитывает duration_minutes.
    Переопределяет property duration_minutes через цепочку декораторов.
    """

    LEVELS = {"лёгкий": 0.8, "средний": 1.0, "сложный": 1.4, "очень сложный": 1.8}

    def __init__(self, component: StudyTask, level: str = "средний"):
        super().__init__(component)
        self._level      = level
        self._multiplier = self.LEVELS.get(level, 1.0)

    @property
    def duration_minutes(self) -> int:
        # AddedBehavior — переопределяем длительность
        return round(self._component.duration_minutes * self._multiplier)

    def execute(self) -> str:
        base = self._component.execute()
        return (base +
                f"\n  🎯 [Сложность: {self._level}] "
                f"Время скорректировано: {self.duration_minutes} мин (×{self._multiplier})")

    def get_info(self) -> dict:
        info             = self._component.get_info()
        info["duration"] = f"{self.duration_minutes} мин  [{self._level}]"
        return info


# ─────────────────────────────────────────────────────────────────────────────
#  ДЕМОНСТРАЦИЯ
# ─────────────────────────────────────────────────────────────────────────────
def demo():
    print("=" * 65)
    print("  DECORATOR — интеграция в Smart Study Planner")
    print("=" * 65)

    deadline_near = datetime.now() + timedelta(days=1)
    deadline_far  = datetime.now() + timedelta(days=10)

    lecture  = LectureTask("Интегральное исчисление", "Математика", 60, deadline_far)
    practice = PracticeTask("2-й закон Ньютона",       "Физика",     45, deadline_near)
    revision = RevisionTask("Повторение формул",        "Химия",      30, deadline_near)

    print("\n📌 1. Обычная задача (ConcreteComponent, без декораторов):")
    print(lecture.execute())

    print("\n📌 1.1. + DontWoryDecorator:")
    print(DontWoryDecorator(lecture).execute())

    print("\n📌 2. + LoggingDecorator:")
    print(LoggingDecorator(lecture).execute())

    print("\n📌 3. + DifficultyDecorator(сложный) + Logging — матрёшка:")
    hard = DifficultyDecorator(LoggingDecorator(lecture), level="сложный")
    print(hard.execute())
    print(f"  duration через цепочку: {hard.duration_minutes} мин")

    print("\n📌 4. Три слоя: Urgent + Reminder + Logging:")
    full = LoggingDecorator(
               ReminderDecorator(
                   UrgentDecorator(practice, reason="Контрольная завтра!"),
                   remind_days_before=3
               )
           )
    print(full.execute())

    print("\n📌 5. get_info() через цепочку (идёт в Treeview):")
    combo = UrgentDecorator(DifficultyDecorator(revision, "очень сложный"), "Финал")
    for k, v in combo.get_info().items():
        print(f"  {k:12}: {v}")

    print("\n📌 6. Декорированная задача → StudySessionManager (Singleton):")
    manager = StudySessionManager.get_instance()
    manager.add_task(full)
    print(f"  Задач в сессии: {manager.get_statistics()['total_tasks']}")
    print(f"  Последний лог:  {manager.get_event_log()[-1]}")

    print("\n✅ Декораторы комбинировались в любом порядке.")
    print("   Код LectureTask/PracticeTask/RevisionTask не менялся.")
    print("=" * 65)


if __name__ == "__main__":
    demo()
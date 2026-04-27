
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from re import S
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from patterns.factory_method import (
    StudyTask, LectureTask, PracticeTask, RevisionTask,
)
from patterns.singleton import StudySessionManager

class TaskDecorator(StudyTask):
   

    def __init__(self, component: StudyTask):
        object.__setattr__(self, '_component', component)

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

    def execute(self) -> str:
        return self._component.execute()

    def get_type(self) -> str:
        return self._component.get_type()

    def get_info(self) -> dict:
        return self._component.get_info()

class DontWoryDecorator(TaskDecorator):
    def __init__(self, component: StudyTask, mass: str = "Раслабься" ):
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

class UrgentDecorator(TaskDecorator):
   

    def __init__(self, component: StudyTask, reason: str = "Дедлайн скоро"):
        super().__init__(component)
        self._reason = reason      

    def execute(self) -> str:
        base = self._component.execute()   
        return base + f"\n  🚨 [СРОЧНО]: {self._reason}"

    def get_info(self) -> dict:
        info             = self._component.get_info()   
        info["priority"] = "ВЫСОКИЙ"
        info["title"]    = f"🚨 {info['title']}"
        return info

class LoggingDecorator(TaskDecorator):


    def __init__(self, component: StudyTask):
        super().__init__(component)
        self._log: list = []       

    def execute(self) -> str:
        ts = datetime.now().strftime("%H:%M:%S")
        self._log.append({"time": ts, "task": self._component.title})

        StudySessionManager.get_instance()._log_event(
            f"[Decorator/Log] Запущена задача: {self._component.title}"
        )

        result = self._component.execute()   
        return result + f"\n  📝 [Лог] Зафиксировано в сессии в {ts}"

    def get_log(self) -> list:
        """AddedBehavior() — дополнительный метод, которого нет у Component."""
        return list(self._log)


class ReminderDecorator(TaskDecorator):
  

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


class DifficultyDecorator(TaskDecorator):
  

    LEVELS = {"лёгкий": 0.8, "средний": 1.0, "сложный": 1.4, "очень сложный": 1.8}

    def __init__(self, component: StudyTask, level: str = "средний"):
        super().__init__(component)
        self._level      = level
        self._multiplier = self.LEVELS.get(level, 1.0)

    @property
    def duration_minutes(self) -> int:
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

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List


class StudyPlan:

    def __init__(self):
        self.subject        = ""
        self.exam_date      = None
        self.daily_hours    = 0
        self.tasks: List    = []
        self.schedule: List = []
        self.reminders: List= []
        self.priority       = "СРЕДНИЙ"
        self.total_hours    = 0
        self.description    = ""
        self.plan_type      = ""
        self.created_at     = datetime.now()

    def get_summary(self) -> str:
        days_left    = (self.exam_date - datetime.now()).days if self.exam_date else 0
        task_titles  = "\n".join(f"    • {t['title']} ({t['duration']} мин)" for t in self.tasks)
        schedule_str = "\n".join(f"    • {s['day']}: {s['hours']} ч — {s['focus']}" for s in self.schedule[:3])
        reminders_str= "\n".join(f"    • {r}" for r in self.reminders)
        return (
            f"╔══════════════════════════════════════════╗\n"
            f"  УЧЕБНЫЙ ПЛАН: {self.subject}\n"
            f"  Тип:          {self.plan_type}\n"
            f"  Приоритет:    {self.priority}\n"
            f"  До экзамена:  {days_left} дней\n"
            f"  В день:       {self.daily_hours} ч\n"
            f"  Итого:        {self.total_hours} ч\n"
            f"  {self.description}\n"
            f"──────────────────────────────────────────\n"
            f"  ЗАДАЧИ:\n{task_titles}\n"
            f"──────────────────────────────────────────\n"
            f"  РАСПИСАНИЕ (первые 3 дня):\n{schedule_str}\n"
            f"──────────────────────────────────────────\n"
            f"  НАПОМИНАНИЯ:\n{reminders_str}\n"
            f"╚══════════════════════════════════════════╝"
        )

    def __repr__(self):
        return f"StudyPlan('{self.subject}', тип='{self.plan_type}', задач={len(self.tasks)})"


class StudyPlanBuilder(ABC):

    def __init__(self):
        self.reset()

    def reset(self):
        self._plan = StudyPlan()

    @abstractmethod
    def set_subject(self, subject: str, exam_date: datetime) -> "StudyPlanBuilder": pass
    @abstractmethod
    def set_schedule(self, daily_hours: float) -> "StudyPlanBuilder": pass
    @abstractmethod
    def add_tasks(self) -> "StudyPlanBuilder": pass
    @abstractmethod
    def set_priority(self) -> "StudyPlanBuilder": pass
    @abstractmethod
    def set_reminders(self) -> "StudyPlanBuilder": pass

    def get_result(self) -> StudyPlan:
        plan = self._plan
        self.reset()
        return plan


class IntensivePlanBuilder(StudyPlanBuilder):

    def set_subject(self, subject, exam_date) -> "StudyPlanBuilder":
        self._plan.subject     = subject
        self._plan.exam_date   = exam_date
        self._plan.plan_type   = "Интенсивный"
        self._plan.description = "Максимальная нагрузка для быстрой подготовки"
        return self

    def set_schedule(self, daily_hours) -> "StudyPlanBuilder":
        self._plan.daily_hours = daily_hours
        days_left = max(1, (self._plan.exam_date - datetime.now()).days)
        self._plan.total_hours = round(daily_hours * days_left, 1)
        self._plan.schedule = [
            {"day": (datetime.now() + timedelta(days=i)).strftime("%d.%m (%a)"),
             "hours": daily_hours, "focus": "Теория 60% + Практика 40%"}
            for i in range(min(days_left, 7))
        ]
        return self

    def add_tasks(self) -> "StudyPlanBuilder":
        self._plan.tasks = [
            {"title": f"[Лекция] Полный курс: {self._plan.subject}",        "duration": 120, "type": "Лекция"},
            {"title": f"[Практика] Интенсив: задачи повышенной сложности",  "duration": 90,  "type": "Практика"},
            {"title": f"[Практика] Контрольные вопросы: {self._plan.subject}","duration": 60, "type": "Практика"},
            {"title": f"[Повторение] Быстрое повторение всех тем",          "duration": 45,  "type": "Повторение"},
            {"title": f"[Практика] Пробный экзамен: {self._plan.subject}",  "duration": 120, "type": "Практика"},
        ]
        return self

    def set_priority(self) -> "StudyPlanBuilder":
        self._plan.priority = "ВЫСОКИЙ"
        return self

    def set_reminders(self) -> "StudyPlanBuilder":
        self._plan.reminders = [
            "⏰ Каждый день в 08:00 — начало занятий",
            "⏰ Каждые 2 часа — короткий перерыв 10 мин",
            "⚠️  За 3 дня до экзамена — финальное повторение",
            "⚠️  За 1 день до экзамена — только лёгкое повторение",
            "🔔 В день экзамена в 07:00 — последнее напоминание",
        ]
        return self


class RelaxedPlanBuilder(StudyPlanBuilder):

    def set_subject(self, subject, exam_date) -> "StudyPlanBuilder":
        self._plan.subject     = subject
        self._plan.exam_date   = exam_date
        self._plan.plan_type   = "Расслабленный"
        self._plan.description = "Комфортная нагрузка с достаточным отдыхом"
        return self

    def set_schedule(self, daily_hours) -> "StudyPlanBuilder":
        adjusted = round(daily_hours * 0.7, 1)
        self._plan.daily_hours = adjusted
        days_left = max(1, (self._plan.exam_date - datetime.now()).days)
        self._plan.total_hours = round(adjusted * days_left, 1)
        self._plan.schedule = [
            {"day": (datetime.now() + timedelta(days=i)).strftime("%d.%m (%a)"),
             "hours": round(adjusted * 0.5, 1) if i % 3 == 2 else adjusted,
             "focus": "Лёгкое повторение + отдых" if i % 3 == 2 else "Теория 40% + Практика 60%"}
            for i in range(min(days_left, 7))
        ]
        return self

    def add_tasks(self) -> "StudyPlanBuilder":
        self._plan.tasks = [
            {"title": f"[Лекция] Основные темы: {self._plan.subject}",   "duration": 60, "type": "Лекция"},
            {"title": f"[Практика] Базовые упражнения",                  "duration": 45, "type": "Практика"},
            {"title": f"[Повторение] Повторение ключевых концепций",     "duration": 30, "type": "Повторение"},
        ]
        return self

    def set_priority(self) -> "StudyPlanBuilder":
        days_left = (self._plan.exam_date - datetime.now()).days
        self._plan.priority = "ВЫСОКИЙ" if days_left <= 3 else "СРЕДНИЙ"
        return self

    def set_reminders(self) -> "StudyPlanBuilder":
        self._plan.reminders = [
            "⏰ Каждый день в 10:00 — начало занятий",
            "⏰ Каждые 45 минут — перерыв 15 мин",
            "⚠️  За 5 дней до экзамена — активизировать подготовку",
            "🔔 В день экзамена в 08:00 — напоминание",
        ]
        return self


class PlannerDirector:

    def __init__(self):
        self._builder: StudyPlanBuilder = None

    def set_builder(self, builder: StudyPlanBuilder):
        self._builder = builder

    def build_full_plan(self, subject: str, exam_date: datetime, daily_hours: float) -> StudyPlan:
        if not self._builder:
            raise ValueError("Builder не установлен!")
        self._builder \
            .set_subject(subject, exam_date) \
            .set_schedule(daily_hours)       \
            .add_tasks()                     \
            .set_priority()                  \
            .set_reminders()
        plan = self._builder.get_result()
        from patterns.singleton import StudySessionManager
        StudySessionManager.get_instance().add_study_plan(plan)
        return plan

    def build_quick_plan(self, subject: str, exam_date: datetime) -> StudyPlan:
        if not self._builder:
            raise ValueError("Builder не установлен!")
        self._builder \
            .set_subject(subject, exam_date) \
            .set_schedule(2.0)               \
            .add_tasks()                     \
            .set_priority()
        plan = self._builder.get_result()
        from patterns.singleton import StudySessionManager
        StudySessionManager.get_instance().add_study_plan(plan)
        return plan

import copy
from abc import ABC, abstractmethod
from datetime import datetime
import uuid


class TaskTemplate(ABC):

    def __init__(self, template_name: str, subject: str,
                 duration_minutes: int, task_type: str):
        self.template_id      = str(uuid.uuid4())[:8]
        self.template_name    = template_name
        self.subject          = subject
        self.duration_minutes = duration_minutes
        self.task_type        = task_type
        self.tags             = []
        self.notes            = ""
        self.priority         = "СРЕДНИЙ"
        self.created_at       = datetime.now()

    @abstractmethod
    def clone(self) -> "TaskTemplate":
        pass

    def customize(self, subject=None, duration_minutes=None,
                  priority=None, notes=None) -> "TaskTemplate":
        if subject          is not None: self.subject          = subject
        if duration_minutes is not None: self.duration_minutes = duration_minutes
        if priority         is not None: self.priority         = priority
        if notes            is not None: self.notes            = notes
        self.template_id = str(uuid.uuid4())[:8]
        self.created_at  = datetime.now()
        return self

    def to_task_dict(self, deadline: datetime) -> dict:
        return {
            "title":    f"[{self.task_type}] {self.template_name}: {self.subject}",
            "subject":  self.subject,
            "duration": self.duration_minutes,
            "type":     self.task_type,
            "priority": self.priority,
            "notes":    self.notes,
            "deadline": deadline,
        }

    def get_info(self) -> str:
        return (
            f"[{self.task_type}] {self.template_name}\n"
            f"  Предмет:   {self.subject}\n"
            f"  Время:     {self.duration_minutes} мин\n"
            f"  Приоритет: {self.priority}\n"
            f"  Теги:      {', '.join(self.tags) if self.tags else '—'}\n"
            f"  Заметки:   {self.notes if self.notes else '—'}"
        )

    def __repr__(self):
        return (f"Template('{self.template_name}' | "
                f"{self.task_type} | {self.subject} | "
                f"{self.duration_minutes}мин | id={self.template_id})")


class LectureTemplate(TaskTemplate):

    def __init__(self, template_name, subject, duration_minutes):
        super().__init__(template_name, subject, duration_minutes, "Лекция")
        self.lecture_topics = []
        self.key_formulas   = []
        self.pages_count    = 0
        self.tags           = ["теория", "конспект"]

    def clone(self) -> "LectureTemplate":
        return copy.deepcopy(self)

    def set_topics(self, topics: list) -> "LectureTemplate":
        self.lecture_topics = topics
        return self

    def set_formulas(self, formulas: list) -> "LectureTemplate":
        self.key_formulas = formulas
        return self


class PracticeTemplate(TaskTemplate):

    def __init__(self, template_name, subject, duration_minutes):
        super().__init__(template_name, subject, duration_minutes, "Практика")
        self.exercises_count = 10
        self.difficulty      = "средний"
        self.has_solutions   = True
        self.tags            = ["практика", "упражнения"]

    def clone(self) -> "PracticeTemplate":
        return copy.copy(self)

    def set_difficulty(self, difficulty: str) -> "PracticeTemplate":
        self.difficulty = difficulty
        return self


class RevisionTemplate(TaskTemplate):

    def __init__(self, template_name, subject, duration_minutes):
        super().__init__(template_name, subject, duration_minutes, "Повторение")
        self.revision_topics = []
        self.revision_method = "активное чтение"
        self.interval_days   = 1
        self.tags            = ["повторение", "закрепление"]

    def clone(self) -> "RevisionTemplate":
        return copy.deepcopy(self)

    def set_revision_topics(self, topics: list) -> "RevisionTemplate":
        self.revision_topics = topics
        return self

    def set_interval(self, days: int) -> "RevisionTemplate":
        self.interval_days = days
        return self


class TemplateRegistry:

    def __init__(self):
        self._prototypes: dict = {}
        self._register_default_templates()

    def register(self, key: str, prototype: TaskTemplate):
        self._prototypes[key] = prototype

    def unregister(self, key: str):
        if key in self._prototypes:
            del self._prototypes[key]

    def clone(self, key: str) -> TaskTemplate:
        if key not in self._prototypes:
            raise KeyError(f"Прототип '{key}' не найден. Доступные: {list(self._prototypes.keys())}")
        return self._prototypes[key].clone()

    def get_all_keys(self) -> list:
        return list(self._prototypes.keys())

    def _register_default_templates(self):
        lecture_basic = LectureTemplate("Базовая лекция", "Общий", 60)
        lecture_basic.set_topics(["Введение", "Основные понятия", "Примеры"])
        lecture_basic.notes = "Читать внимательно, делать конспект"
        self._prototypes["lecture_basic"] = lecture_basic

        lecture_deep = LectureTemplate("Глубокое изучение", "Общий", 120)
        lecture_deep.set_topics(["Теория", "Доказательства", "Приложения"])
        lecture_deep.pages_count = 20
        lecture_deep.priority = "ВЫСОКИЙ"
        self._prototypes["lecture_deep"] = lecture_deep

        practice_basic = PracticeTemplate("Базовая практика", "Общий", 45)
        practice_basic.exercises_count = 10
        practice_basic.difficulty      = "лёгкий"
        self._prototypes["practice_basic"] = practice_basic

        practice_hard = PracticeTemplate("Сложная практика", "Общий", 90)
        practice_hard.exercises_count = 20
        practice_hard.difficulty      = "сложный"
        practice_hard.priority        = "ВЫСОКИЙ"
        self._prototypes["practice_hard"] = practice_hard

        revision_quick = RevisionTemplate("Быстрое повторение", "Общий", 30)
        revision_quick.set_revision_topics(["Ключевые формулы", "Определения"])
        revision_quick.interval_days = 1
        self._prototypes["revision_quick"] = revision_quick

        revision_full = RevisionTemplate("Полное повторение", "Общий", 60)
        revision_full.set_revision_topics(["Все темы", "Сложные места"])
        revision_full.revision_method = "активное воспроизведение"
        revision_full.interval_days   = 3
        revision_full.priority        = "ВЫСОКИЙ"
        self._prototypes["revision_full"] = revision_full

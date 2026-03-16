from abc import ABC, abstractmethod
from datetime import datetime
import uuid


class StudyTask(ABC):

    def __init__(self, title: str, subject: str, duration_minutes: int, deadline: datetime):
        self.task_id          = str(uuid.uuid4())[:8]
        self.title            = title
        self.subject          = subject
        self.duration_minutes = duration_minutes
        self.deadline         = deadline
        self.completed        = False
        self.created_at       = datetime.now()
        self.priority         = self._calculate_priority()

    def _calculate_priority(self) -> str:
        days_left = (self.deadline - datetime.now()).days
        if days_left <= 1:   return "ВЫСОКИЙ"
        elif days_left <= 3: return "СРЕДНИЙ"
        else:                return "НИЗКИЙ"

    @abstractmethod
    def execute(self) -> str:
        pass

    @abstractmethod
    def get_type(self) -> str:
        pass

    def get_info(self) -> dict:
        return {
            "id":       self.task_id,
            "type":     self.get_type(),
            "title":    self.title,
            "subject":  self.subject,
            "duration": f"{self.duration_minutes} мин",
            "deadline": self.deadline.strftime("%d.%m.%Y %H:%M"),
            "priority": self.priority,
            "done":     "✓" if self.completed else "✗"
        }

    def __repr__(self):
        return f"[{self.get_type()}] {self.title} | {self.subject} | до {self.deadline.strftime('%d.%m')}"


class LectureTask(StudyTask):

    def __init__(self, title, subject, duration_minutes, deadline, lecture_pages=0):
        super().__init__(title, subject, duration_minutes, deadline)
        self.lecture_pages = lecture_pages
        self.notes         = []

    def execute(self) -> str:
        return (
            f"📖 Изучаю лекцию: '{self.title}'\n"
            f"   Предмет: {self.subject}\n"
            f"   Страниц: {self.lecture_pages}\n"
            f"   Время:   {self.duration_minutes} мин"
        )

    def get_type(self) -> str:
        return "Лекция"

    def add_note(self, note: str):
        self.notes.append(note)


class PracticeTask(StudyTask):

    def __init__(self, title, subject, duration_minutes, deadline, exercises_count=0):
        super().__init__(title, subject, duration_minutes, deadline)
        self.exercises_count = exercises_count
        self.solved_count    = 0

    def execute(self) -> str:
        return (
            f"✏️  Практика: '{self.title}'\n"
            f"   Предмет:    {self.subject}\n"
            f"   Упражнений: {self.exercises_count} (решено: {self.solved_count})\n"
            f"   Время:      {self.duration_minutes} мин"
        )

    def get_type(self) -> str:
        return "Практика"

    def solve_exercise(self):
        if self.solved_count < self.exercises_count:
            self.solved_count += 1


class RevisionTask(StudyTask):

    def __init__(self, title, subject, duration_minutes, deadline, topics=None):
        super().__init__(title, subject, duration_minutes, deadline)
        self.topics          = topics if topics else []
        self.revision_number = 1

    def execute(self) -> str:
        topics_str = ", ".join(self.topics) if self.topics else "все темы"
        return (
            f"🔄 Повторение #{self.revision_number}: '{self.title}'\n"
            f"   Предмет: {self.subject}\n"
            f"   Темы:    {topics_str}\n"
            f"   Время:   {self.duration_minutes} мин"
        )

    def get_type(self) -> str:
        return "Повторение"

    def increment_revision(self):
        self.revision_number += 1


class TaskCreator(ABC):

    @abstractmethod
    def factory_method(self, title: str, subject: str,
                       duration_minutes: int, deadline: datetime,
                       **kwargs) -> StudyTask:
        pass

    def create_and_register(self, title: str, subject: str,
                            duration_minutes: int, deadline: datetime,
                            **kwargs) -> StudyTask:
        task = self.factory_method(title, subject, duration_minutes, deadline, **kwargs)
        from patterns.singleton import StudySessionManager
        StudySessionManager.get_instance().add_task(task)
        return task

    def get_task_preview(self, title: str, subject: str,
                         duration_minutes: int, deadline: datetime,
                         **kwargs) -> str:
        task = self.factory_method(title, subject, duration_minutes, deadline, **kwargs)
        return task.execute()


class LectureTaskCreator(TaskCreator):

    def factory_method(self, title, subject, duration_minutes, deadline, **kwargs) -> StudyTask:
        return LectureTask(title, subject, duration_minutes, deadline,
                           kwargs.get("lecture_pages", 0))


class PracticeTaskCreator(TaskCreator):

    def factory_method(self, title, subject, duration_minutes, deadline, **kwargs) -> StudyTask:
        return PracticeTask(title, subject, duration_minutes, deadline,
                            kwargs.get("exercises_count", 0))


class RevisionTaskCreator(TaskCreator):

    def factory_method(self, title, subject, duration_minutes, deadline, **kwargs) -> StudyTask:
        return RevisionTask(title, subject, duration_minutes, deadline,
                            kwargs.get("topics", []))

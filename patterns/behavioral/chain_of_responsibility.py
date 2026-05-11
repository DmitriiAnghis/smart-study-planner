
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from patterns.singleton import StudySessionManager



class ValidationHandler(ABC):
   

    def __init__(self):
        self._next_handler: Optional["ValidationHandler"] = None

    def set_next(self, handler: "ValidationHandler") -> "ValidationHandler":
      
        self._next_handler = handler
        return handler

    def handle(self, request: dict) -> Optional[str]:
       
        if self._next_handler:
            return self._next_handler.handle(request)
        return None

    @abstractmethod
    def handler_name(self) -> str:
        pass


class TitleValidator(ValidationHandler):
   

    def handler_name(self) -> str:
        return "TitleValidator"

    def handle(self, request: dict) -> Optional[str]:
        title = request.get("title", "").strip()
        print(f"  [Chain] TitleValidator: проверяю '{title}'")

        if not title:
            return "❌ Название задачи не может быть пустым"

        if len(title) < 3:
            return "❌ Название слишком короткое: минимум 3 символа"

        if len(title) > 100:
            return "❌ Название слишком длинное: максимум 100 символов"

        print("  [Chain] TitleValidator: ✅ прошло — передаю дальше")
        return super().handle(request)


class DeadlineValidator(ValidationHandler):
   

    def handler_name(self) -> str:
        return "DeadlineValidator"

    def handle(self, request: dict) -> Optional[str]:
        deadline = request.get("deadline")
        print("  [Chain] DeadlineValidator: проверяю дедлайн")

        if deadline is None:
            return "❌ Дедлайн не указан"

        if deadline < datetime.now():
            return f"❌ Дедлайн уже прошёл: {deadline.strftime('%d.%m.%Y')}"

        days_left = (deadline - datetime.now()).days
        if days_left > 365:
            return "❌ Дедлайн слишком далеко: максимум 365 дней"

        print("  [Chain] DeadlineValidator: ✅ прошло — передаю дальше")
        return super().handle(request)


class DuplicateValidator(ValidationHandler):
 

    def __init__(self, manager: StudySessionManager):
        super().__init__()
        self._manager = manager

    def handler_name(self) -> str:
        return "DuplicateValidator"

    def handle(self, request: dict) -> Optional[str]:
        title   = request.get("title", "").strip()
        subject = request.get("subject", "")
        print("  [Chain] DuplicateValidator: проверяю дубликаты")

        existing = self._manager.get_all_tasks()
        for task in existing:
            if (task.title.strip().lower() == title.lower() and
                    task.subject == subject):
                return (f"❌ Задача '{title}' по предмету "
                        f"'{subject}' уже существует")

        print("  [Chain] DuplicateValidator: ✅ прошло — передаю дальше")
        return super().handle(request)


class DurationValidator(ValidationHandler):
  

    MIN_MINUTES = 5
    MAX_MINUTES = 480   

    def handler_name(self) -> str:
        return "DurationValidator"

    def handle(self, request: dict) -> Optional[str]:
        duration = request.get("duration", 0)
        print(f"  [Chain] DurationValidator: проверяю {duration} мин")

        if duration < self.MIN_MINUTES:
            return f"❌ Минимальная длительность: {self.MIN_MINUTES} минут"

        if duration > self.MAX_MINUTES:
            return (f"❌ Максимальная длительность: {self.MAX_MINUTES} мин "
                    f"({self.MAX_MINUTES // 60} часов)")

        print("  [Chain] DurationValidator: ✅ прошло — все проверки пройдены")
        return super().handle(request)



class TaskValidationChain:
    

    def __init__(self, manager: StudySessionManager):
        # Строим цепочку: Title → Deadline → Duplicate → Duration
        self._head = TitleValidator()
        self._head \
            .set_next(DeadlineValidator()) \
            .set_next(DuplicateValidator(manager)) \
            .set_next(DurationValidator())

    def validate(self, title: str, subject: str,
                 duration: int, deadline: datetime) -> Optional[str]:
     
        request = {
            "title":    title,
            "subject":  subject,
            "duration": duration,
            "deadline": deadline,
        }
        return self._head.handle(request)

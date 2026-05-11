from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from patterns.factory_method import (StudyTask, LectureTask, PracticeTask,
                                     RevisionTask, LectureTaskCreator,
                                     PracticeTaskCreator, RevisionTaskCreator)
from patterns.singleton import StudySessionManager



class ITaskImporter(ABC):
   

    @abstractmethod
    def import_tasks(self) -> List[StudyTask]:
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        pass


class GoogleCalendarAPI:
   

    def fetch_events(self) -> list:
        """SpecificRequest() — чужой интерфейс."""
        print("  [GoogleCalendarAPI] fetch_events() → получаем события...")
        return [
            {"summary": "Лекция: Интегралы",    "description": "subject:Математика|type:Лекция|dur:60",   "due": (datetime.now() + timedelta(days=5)).isoformat()},
            {"summary": "Практика: Ньютон",      "description": "subject:Физика|type:Практика|dur:45",    "due": (datetime.now() + timedelta(days=3)).isoformat()},
            {"summary": "Повторение: Химия",     "description": "subject:Химия|type:Повторение|dur:30",   "due": (datetime.now() + timedelta(days=7)).isoformat()},
        ]

    def parse_event(self, event: dict) -> dict:
        """Разбирает description в поля."""
        result = {"title": event["summary"], "due": event["due"]}
        for part in event.get("description", "").split("|"):
            if ":" in part:
                k, v = part.split(":", 1)
                result[k] = v
        return result



class TrelloAPI:
    

    def get_cards(self, board_id: str = "study_board") -> list:
        """SpecificRequest() — чужой интерфейс."""
        print(f"  [TrelloAPI] get_cards(board={board_id}) → загружаем карточки...")
        return [
            {"name": "📖 Читать учебник по физике",   "labels": ["Лекция"],     "subject_tag": "Физика",       "due_days": 4,  "time_min": 90},
            {"name": "✏️ Решить задачи по алгебре",   "labels": ["Практика"],   "subject_tag": "Математика",   "due_days": 2,  "time_min": 60},
            {"name": "🔄 Повторить теорию Дарвина",   "labels": ["Повторение"], "subject_tag": "Биология",     "due_days": 6,  "time_min": 45},
        ]


class PlainTextSchedule:
  

    def read_schedule(self) -> str:
        """SpecificRequest() — возвращает raw-текст."""
        print("  [PlainTextSchedule] read_schedule() → читаем текстовый файл...")
        return (
            "Методы дифференцирования|Математика|Лекция|60|5\n"
            "Контрольная по физике|Физика|Практика|120|2\n"
            "Закрепление материала|Информатика|Повторение|30|8\n"
        )


class GoogleCalendarAdapter(ITaskImporter):


    TYPE_MAP = {"Лекция": LectureTaskCreator, "Практика": PracticeTaskCreator,
                "Повторение": RevisionTaskCreator}

    def __init__(self):
        self._adaptee = GoogleCalendarAPI()     

    def import_tasks(self) -> List[StudyTask]:
        """Request() — адаптируем SpecificRequest() к нашему интерфейсу."""
        raw_events = self._adaptee.fetch_events()   
        tasks = []
        for event in raw_events:
            parsed  = self._adaptee.parse_event(event)
            ttype   = parsed.get("type", "Лекция")
            creator = self.TYPE_MAP.get(ttype, LectureTaskCreator)()
            due     = datetime.fromisoformat(parsed["due"])
            task    = creator.factory_method(parsed["title"], parsed.get("subject", "Общее"),
                                              int(parsed.get("dur", 60)), due)
            tasks.append(task)
        return tasks

    def get_source_name(self) -> str:
        return "Google Calendar"


class TrelloAdapter(ITaskImporter):

    TYPE_MAP = {"Лекция": LectureTaskCreator, "Практика": PracticeTaskCreator,
                "Повторение": RevisionTaskCreator}

    def __init__(self, board_id: str = "study_board"):
        self._adaptee  = TrelloAPI()            
        self._board_id = board_id

    def import_tasks(self) -> List[StudyTask]:
        cards = self._adaptee.get_cards(self._board_id)  
        tasks = []
        for card in cards:
            ttype   = card["labels"][0] if card["labels"] else "Лекция"
            creator = self.TYPE_MAP.get(ttype, LectureTaskCreator)()
            due     = datetime.now() + timedelta(days=card["due_days"])
            task    = creator.factory_method(card["name"], card["subject_tag"],
                                              card["time_min"], due)
            tasks.append(task)
        return tasks

    def get_source_name(self) -> str:
        return "Trello"

class PlainTextAdapter(ITaskImporter):
   

    TYPE_MAP = {"Лекция": LectureTaskCreator, "Практика": PracticeTaskCreator,
                "Повторение": RevisionTaskCreator}

    def __init__(self):
        self._adaptee = PlainTextSchedule()     

    def import_tasks(self) -> List[StudyTask]:
        raw   = self._adaptee.read_schedule()   
        tasks = []
        for line in raw.strip().splitlines():
            parts = line.strip().split("|")
            if len(parts) < 5:
                continue
            title, subject, ttype, minutes, days = parts
            creator = self.TYPE_MAP.get(ttype, LectureTaskCreator)()
            due     = datetime.now() + timedelta(days=int(days))
            task    = creator.factory_method(title, subject, int(minutes), due)
            tasks.append(task)
        return tasks

    def get_source_name(self) -> str:
        return "PlainText (Legacy)"


class ImportService:
   

    def __init__(self, manager: StudySessionManager):
        self._manager = manager

    def run_import(self, importer: ITaskImporter) -> int:
        """Использует только Request() — import_tasks() из Target."""
        print(f"\n  [ImportService] Импорт из: {importer.get_source_name()}")
        tasks = importer.import_tasks()    
        for task in tasks:
            self._manager.add_task(task)
            print(f"    ✅ Добавлена: [{task.get_type()}] {task.title} / {task.subject}")
        return len(tasks)


def demo():
    print("=" * 65)
    print("  ADAPTER — интеграция в Smart Study Planner")
    print("=" * 65)

    manager = StudySessionManager.get_instance()
    service = ImportService(manager)


    total = 0
    total += service.run_import(GoogleCalendarAdapter())
    total += service.run_import(TrelloAdapter())
    total += service.run_import(PlainTextAdapter())

    print(f"\n  Итого импортировано: {total} задач")
    stats = manager.get_statistics()
    print(f"  Всего задач в сессии: {stats['total_tasks']}")

    print("\n📌 Все задачи (Client не знал, откуда они):")
    for task in manager.get_all_tasks():
        print(f"  [{task.get_type():10}] {task.title:35} | {task.subject}")

    print("\n✅ ImportService использовал один интерфейс import_tasks().")
    print("   Adaptee (Google/Trello/PlainText) не менялись — только обёртка.")
    print("   Это и есть Adapter.")
    print("=" * 65)


if __name__ == "__main__":
    demo()
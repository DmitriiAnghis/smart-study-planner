

from abc import ABC, abstractmethod
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))



class TaskState(ABC):
   

    @abstractmethod
    def handle(self, task) -> str:
        
        pass

    @abstractmethod
    def get_label(self) -> str:
        pass

    @abstractmethod
    def can_start(self) -> bool:
        pass

    @abstractmethod
    def can_complete(self) -> bool:
        pass


class NewTaskState(TaskState):
  

    def handle(self, task) -> str:
        if datetime.now() > task.deadline:
            task.set_state(OverdueState())
            return task.state.handle(task)
        return f"📋 Задача '{task.title}' ожидает начала"

    def get_label(self) -> str:
        return "🆕 Новая"

    def can_start(self) -> bool:
        return True

    def can_complete(self) -> bool:
        return False


class InProgressState(TaskState):
   

    def handle(self, task) -> str:
        days_left = (task.deadline - datetime.now()).days
        if datetime.now() > task.deadline:
            task.set_state(OverdueState())
            return task.state.handle(task)
        return (f"⚡ Задача '{task.title}' в работе. "
                f"Осталось {days_left} дн.")

    def get_label(self) -> str:
        return "⚡ В работе"

    def can_start(self) -> bool:
        return False

    def can_complete(self) -> bool:
        return True


class CompletedState(TaskState):
   

    def handle(self, task) -> str:
        return f"✅ Задача '{task.title}' выполнена!"

    def get_label(self) -> str:
        return "✅ Выполнена"

    def can_start(self) -> bool:
        return False

    def can_complete(self) -> bool:
        return False


class OverdueState(TaskState):
  

    def handle(self, task) -> str:
        days_ago = (datetime.now() - task.deadline).days
        return (f"❌ Задача '{task.title}' ПРОСРОЧЕНА "
                f"на {days_ago} дн.!")

    def get_label(self) -> str:
        return "❌ Просрочена"

    def can_start(self) -> bool:
        return False

    def can_complete(self) -> bool:
        return True  


class StudyTaskWithState:
   

    def __init__(self, task):
        self._task  = task
        self._state: TaskState = NewTaskState()  

    def set_state(self, state: TaskState) -> None:
        """Переключить состояние. Вызывается из самих состояний."""
        print(f"  [State] '{self._task.title}': "
              f"{self._state.get_label()} → {state.get_label()}")
        self._state = state

    @property
    def title(self):    return self._task.title
    @property
    def subject(self):  return self._task.subject
    @property
    def deadline(self): return self._task.deadline
    @property
    def priority(self): return self._task.priority
    @property
    def task_id(self):  return self._task.task_id

    def handle(self) -> str:
        """request() из GoF — делегирует текущему состоянию."""
        return self._state.handle(self)

    def get_status_label(self) -> str:
        return self._state.get_label()

    def start(self) -> str:
        if not self._state.can_start():
            return f"  Нельзя начать: задача уже {self._state.get_label()}"
        self.set_state(InProgressState())
        return self._state.handle(self)

    def complete(self) -> str:
        if not self._state.can_complete():
            return f"  Нельзя завершить: задача {self._state.get_label()}"
        self.set_state(CompletedState())
        return self._state.handle(self)

    def check_overdue(self) -> None:
        """Проверить — не просрочена ли задача. Вызывать при refresh()."""
        if (not isinstance(self._state, CompletedState) and
                datetime.now() > self._task.deadline):
            self.set_state(OverdueState())

    def get_info(self) -> dict:
        """Расширяем get_info() оригинала — добавляем статус состояния."""
        info = self._task.get_info()
        info["done"] = self._state.get_label()   
        return info



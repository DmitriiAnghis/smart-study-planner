

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from patterns.singleton import StudySessionManager


class Command(ABC):
    

    @abstractmethod
    def execute(self) -> str:
        """Выполнить команду. Возвращает описание что сделано."""
        pass

    @abstractmethod
    def undo(self) -> str:
        """Отменить команду. Возвращает описание что отменено."""
        pass

    @abstractmethod
    def description(self) -> str:
        """Краткое описание команды для истории."""
        pass


class AddTaskCommand(Command):
   

    def __init__(self, manager: StudySessionManager, task):
        self._manager = manager
        self._task    = task

    def execute(self) -> str:
        self._manager.add_task(self._task)
        return f"Добавлена задача: '{self._task.title}'"

    def undo(self) -> str:
        self._manager.remove_task(self._task.task_id)
        return f"Отменено добавление: '{self._task.title}'"

    def description(self) -> str:
        return f"[+] {self._task.title} [{self._task.get_type()}]"


class RemoveTaskCommand(Command):
    

    def __init__(self, manager: StudySessionManager, task):
        self._manager = manager
        self._task    = task

    def execute(self) -> str:
        self._manager.remove_task(self._task.task_id)
        return f"Удалена задача: '{self._task.title}'"

    def undo(self) -> str:
        self._manager._tasks.append(self._task)
        self._manager._log_event(f"Восстановлена задача: {self._task.title}")
        self._manager.notify("task_added", {"title": self._task.title})
        return f"Восстановлена задача: '{self._task.title}'"

    def description(self) -> str:
        return f"[-] {self._task.title}"


class CompleteTaskCommand(Command):
   

    def __init__(self, manager: StudySessionManager, task):
        self._manager         = manager
        self._task            = task
        self._was_completed   = task.completed

    def execute(self) -> str:
        self._manager.mark_task_completed(self._task.task_id)
        return f"Выполнена: '{self._task.title}'"

    def undo(self) -> str:
        if self._task.completed and not self._was_completed:
            self._task.completed = False
            self._manager._completed_tasks_count = max(
                0, self._manager._completed_tasks_count - 1)
            self._manager._log_event(f"Отменено выполнение: {self._task.title}")
            self._manager.notify("task_completed", {"title": self._task.title})
        return f"Отменено выполнение: '{self._task.title}'"

    def get_task(self):
        """Возвращает задачу — нужен TasksTab чтобы сбросить State."""
        return self._task

    def description(self) -> str:
        return f"[✓] {self._task.title}"



class CommandInvoker:
   

    def __init__(self):
        self._history:  List[Command] = []   
        self._max_history = 20               

    def execute_command(self, command: Command) -> str:
        """Выполнить команду и сохранить в историю."""
        result = command.execute()
        self._history.append(command)
        if len(self._history) > self._max_history:
            self._history.pop(0)
        return result

    def undo(self) -> Optional[str]:
        """Отменить последнюю команду."""
        if not self._history:
            return "Нечего отменять"
        command = self._history.pop()
        return command.undo()

    def get_history(self) -> List[str]:
        """Список выполненных команд для отображения."""
        return [cmd.description() for cmd in reversed(self._history)]

    def can_undo(self) -> bool:
        return len(self._history) > 0


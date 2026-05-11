

from abc import ABC, abstractmethod
from typing import List
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))



class SortStrategy(ABC):


    @abstractmethod
    def sort(self, tasks: list) -> list:
        pass

    @abstractmethod
    def name(self) -> str:
        pass


class FilterStrategy(ABC):


    @abstractmethod
    def filter(self, tasks: list) -> list:
        pass

    @abstractmethod
    def name(self) -> str:
        pass



class SortByDeadline(SortStrategy):


    def sort(self, tasks: list) -> list:
        return sorted(tasks, key=lambda t: t.deadline)

    def name(self) -> str:
        return "📅 По дедлайну"


class SortByPriority(SortStrategy):


    _ORDER = {"ВЫСОКИЙ": 0, "СРЕДНИЙ": 1, "НИЗКИЙ": 2}

    def sort(self, tasks: list) -> list:
        return sorted(tasks, key=lambda t: self._ORDER.get(t.priority, 99))

    def name(self) -> str:
        return "🔴 По приоритету"


class SortBySubject(SortStrategy):


    def sort(self, tasks: list) -> list:
        return sorted(tasks, key=lambda t: t.subject)

    def name(self) -> str:
        return "📚 По предмету"


class SortByType(SortStrategy):

    _ORDER = {"Лекция": 0, "Практика": 1, "Повторение": 2}

    def sort(self, tasks: list) -> list:
        return sorted(tasks, key=lambda t: self._ORDER.get(t.get_type(), 99))

    def name(self) -> str:
        return "📝 По типу"


class SortByNameLength(SortStrategy):
    def sort(self, tasks: list) -> list:
        return sorted(tasks, key=lambda t: len(t.name))
    def name(self) -> str:
        return "🔧 Кастомная сортировка по длине именни"


class FilterAll(FilterStrategy):
    """Показать все задачи — фильтр по умолчанию."""

    def filter(self, tasks: list) -> list:
        return list(tasks)

    def name(self) -> str:
        return "Все задачи"


class FilterPending(FilterStrategy):
    """Только невыполненные задачи."""

    def filter(self, tasks: list) -> list:
        return [t for t in tasks if not t.completed]

    def name(self) -> str:
        return "⬜ Невыполненные"


class FilterCompleted(FilterStrategy):
    """Только выполненные задачи."""

    def filter(self, tasks: list) -> list:
        return [t for t in tasks if t.completed]

    def name(self) -> str:
        return "✅ Выполненные"


class FilterBySubject(FilterStrategy):
    """Только задачи выбранного предмета."""

    def __init__(self, subject: str):
        self._subject = subject

    def filter(self, tasks: list) -> list:
        return [t for t in tasks if t.subject == self._subject]

    def name(self) -> str:
        return f"📖 {self._subject}"


class TaskSorterContext:


    def __init__(self):
        self._sort_strategy:   SortStrategy   = SortByDeadline()
        self._filter_strategy: FilterStrategy = FilterAll()

    def set_sort_strategy(self, strategy: SortStrategy) -> None:
        """Поменять алгоритм сортировки."""
        self._sort_strategy = strategy
        print(f"  [Strategy] Сортировка: {strategy.name()}")

    def set_filter_strategy(self, strategy: FilterStrategy) -> None:
        """Поменять алгоритм фильтрации."""
        self._filter_strategy = strategy
        print(f"  [Strategy] Фильтр: {strategy.name()}")

    def get_tasks(self, tasks: list) -> list:

        filtered = self._filter_strategy.filter(tasks)
        sorted_  = self._sort_strategy.sort(filtered)
        return sorted_

    @property
    def sort_name(self) -> str:
        return self._sort_strategy.name()

    @property
    def filter_name(self) -> str:
        return self._filter_strategy.name()

    @staticmethod
    def available_sort_strategies() -> dict:
        return {
            "📅 По дедлайну":  SortByDeadline(),
            "🔴 По приоритету": SortByPriority(),
            "📚 По предмету":   SortBySubject(),
            "📝 По типу":       SortByType(),
        }

    @staticmethod
    def available_filter_strategies() -> dict:
        return {
            "Все задачи":      FilterAll(),
            "⬜ Невыполненные": FilterPending(),
            "✅ Выполненные":   FilterCompleted(),
        }



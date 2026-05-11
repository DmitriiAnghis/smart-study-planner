
from abc import ABC, abstractmethod
from typing import List


class Observer(ABC):
   

    @abstractmethod
    def update(self, event: str, data: dict) -> None:
       
        pass


class Subject:
    

    def __init__(self):
        self._observers: List[Observer] = []

    def attach(self, observer: Observer) -> None:
        """Подписать наблюдателя."""
        if observer not in self._observers:
            self._observers.append(observer)
            print(f"  [Subject] подписан: {observer.name}")

    def detach(self, observer: Observer) -> None:
        """Отписать наблюдателя."""
        if observer in self._observers:
            self._observers.remove(observer)
            print(f"  [Subject] отписан: {observer.name}")

    def notify(self, event: str, data: dict = None) -> None:
        """Уведомить всех подписчиков о событии."""
        for observer in self._observers:
            observer.update(event, data or {})

class TasksTabObserver(Observer):
    

    def __init__(self, refresh_callback):
        self._refresh = refresh_callback
        self.name     = "TasksTab"

    def update(self, event: str, data: dict) -> None:
        if event in ("task_added", "task_removed", "task_completed"):
            print(f"  [Observer/{self.name}] событие '{event}' → обновляю список задач")
            self._refresh()



class StatsTabObserver(Observer):
    

    def __init__(self, refresh_callback):
        self._refresh = refresh_callback
        self.name     = "StatsTab"

    def update(self, event: str, data: dict) -> None:
        print(f"  [Observer/{self.name}] событие '{event}' → обновляю статистику")
        self._refresh()


class PlansTabObserver(Observer):
   

    def __init__(self, refresh_callback):
        self._refresh = refresh_callback
        self.name     = "PlansTab"

    def update(self, event: str, data: dict) -> None:
        if event in ("plan_added", "plan_removed"):
            print(f"  [Observer/{self.name}] событие '{event}' → обновляю список планов")
            self._refresh()


class StatusBarObserver(Observer):
    

    def __init__(self, set_status_callback):
        self._set_status = set_status_callback
        self.name        = "StatusBar"

    def update(self, event: str, data: dict) -> None:
        messages = {
            "task_added":     f"✅ Добавлена задача: {data.get('title', '')}",
            "task_removed":   f"🗑 Удалена задача",
            "task_completed": f"✅ Задача выполнена: {data.get('title', '')}",
            "plan_added":     f"📅 Добавлен план: {data.get('subject', '')}",
            "theme_changed":  f"🎨 Тема: {data.get('theme', '')}",
        }
        msg = messages.get(event, f"📌 Событие: {event}")
        print(f"  [Observer/{self.name}] {msg}")
        self._set_status(msg)
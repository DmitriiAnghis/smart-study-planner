from datetime import datetime
from typing import List
from patterns.behavioral.observer import Subject, Observer


class StudySessionManager(Subject):

    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def __init__(self):
        if StudySessionManager._instance is not None:
            raise RuntimeError(
                "[Singleton] Нельзя создавать экземпляр напрямую!\n"
                "Используйте: StudySessionManager.get_instance()"
            )

    def _initialize(self):
        self._tasks                 = []
        self._study_plans           = []
        self._event_log             = []
        self._current_theme         = "light"
        self._session_start         = datetime.now()
        self._completed_tasks_count = 0
        self._observers: List       = []     
        self._log_event("Сессия запущена")

    def add_task(self, task):
        self._tasks.append(task)
        self._log_event(f"Добавлена задача: {task.title}")
        self.notify("task_added", {"title": task.title})

    def remove_task(self, task_id):
        before = len(self._tasks)
        self._tasks = [t for t in self._tasks if t.task_id != task_id]
        if len(self._tasks) < before:
            self._log_event(f"Удалена задача ID={task_id}")
            self.notify("task_removed", {"task_id": task_id})

    def get_all_tasks(self):
        return list(self._tasks)

    def get_tasks_by_subject(self, subject):
        return [t for t in self._tasks if t.subject == subject]

    def mark_task_completed(self, task_id):
        for task in self._tasks:
            if task.task_id == task_id:
                task.completed = True
                self._completed_tasks_count += 1
                self._log_event(f"Задача выполнена: {task.title}")
                self.notify("task_completed", {"title": task.title})
                return True
        return False

    def add_study_plan(self, plan):
        self._study_plans.append(plan)
        self._log_event(f"Добавлен план: {plan.subject}")
        self.notify("plan_added", {"subject": plan.subject})

    def get_all_plans(self):
        return list(self._study_plans)

    def _log_event(self, message):
        self._event_log.append({
            "time":    datetime.now().strftime("%H:%M:%S"),
            "message": message
        })

    def get_event_log(self):
        return list(self._event_log)

    def set_theme(self, theme: str):
        self._current_theme = theme
        self._log_event(f"Тема изменена на: {theme}")
        self.notify("theme_changed", {"theme": theme})

    def get_theme(self):
        return self._current_theme

    def get_statistics(self):
        total     = len(self._tasks)
        completed = self._completed_tasks_count
        percent   = (completed / total * 100) if total > 0 else 0
        return {
            "total_tasks":      total,
            "completed_tasks":  completed,
            "progress_percent": round(percent, 1),
            "total_plans":      len(self._study_plans),
            "session_start":    self._session_start.strftime("%H:%M:%S"),
            "theme":            self._current_theme
        }

    @classmethod
    def reset_instance(cls):
        cls._instance = None

    def __repr__(self):
        stats = self.get_statistics()
        return (
            f"StudySessionManager(singleton) | "
            f"tasks={stats['total_tasks']} | "
            f"done={stats['completed_tasks']} | "
            f"theme={stats['theme']}"
        )
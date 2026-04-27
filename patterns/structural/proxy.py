

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from patterns.singleton import StudySessionManager



class ISessionManager(ABC):


    @abstractmethod
    def add_task(self, task) -> None: pass

    @abstractmethod
    def remove_task(self, task_id: str) -> None: pass

    @abstractmethod
    def get_all_tasks(self) -> list: pass

    @abstractmethod
    def mark_task_completed(self, task_id: str) -> bool: pass

    @abstractmethod
    def add_study_plan(self, plan) -> None: pass

    @abstractmethod
    def get_all_plans(self) -> list: pass

    @abstractmethod
    def get_statistics(self) -> dict: pass

    @abstractmethod
    def get_event_log(self) -> list: pass

    @abstractmethod
    def set_theme(self, theme: str) -> None: pass

    @abstractmethod
    def get_theme(self) -> str: pass

class RealSessionManager(ISessionManager):
  

    def __init__(self):
        self._mgr = StudySessionManager.get_instance()

    def add_task(self, task):              self._mgr.add_task(task)
    def remove_task(self, tid):            self._mgr.remove_task(tid)
    def get_all_tasks(self):               return self._mgr.get_all_tasks()
    def mark_task_completed(self, tid):    return self._mgr.mark_task_completed(tid)
    def add_study_plan(self, plan):        self._mgr.add_study_plan(plan)
    def get_all_plans(self):               return self._mgr.get_all_plans()
    def get_statistics(self):              return self._mgr.get_statistics()
    def get_event_log(self):               return self._mgr.get_event_log()
    def set_theme(self, theme):            self._mgr.set_theme(theme)
    def get_theme(self):                   return self._mgr.get_theme()


class ProtectionProxy(ISessionManager):
  

    PERMISSIONS = {
        "student": ["get_all_tasks", "get_all_plans", "get_statistics",
                    "get_event_log", "get_theme"],
        "teacher": ["get_all_tasks", "get_all_plans", "get_statistics",
                    "get_event_log", "get_theme", "add_task", "mark_task_completed"],
        "admin":   "__all__",
    }

    def __init__(self, real_subject: ISessionManager, role: str = "student"):
        self._real = real_subject    
        self._role = role

    def _check(self, action: str) -> bool:
        perms = self.PERMISSIONS.get(self._role, [])
        if perms == "__all__" or action in perms:
            return True
        print(f"  [ProtectionProxy] ❌ '{self._role}' не может выполнить '{action}'")
        return False

    def add_task(self, task):
        if self._check("add_task"):        self._real.add_task(task)

    def remove_task(self, tid):
        if self._check("remove_task"):     self._real.remove_task(tid)

    def get_all_tasks(self):
        if self._check("get_all_tasks"):   return self._real.get_all_tasks()
        return []

    def mark_task_completed(self, tid):
        if self._check("mark_task_completed"): return self._real.mark_task_completed(tid)
        return False

    def add_study_plan(self, plan):
        if self._check("add_study_plan"):  self._real.add_study_plan(plan)

    def get_all_plans(self):
        if self._check("get_all_plans"):   return self._real.get_all_plans()
        return []

    def get_statistics(self):
        if self._check("get_statistics"):  return self._real.get_statistics()
        return {}

    def get_event_log(self):
        if self._check("get_event_log"):   return self._real.get_event_log()
        return []

    def set_theme(self, theme):
        if self._check("set_theme"):       self._real.set_theme(theme)

    def get_theme(self):
        if self._check("get_theme"):       return self._real.get_theme()
        return "light"


class CachingProxy(ISessionManager):


    def __init__(self, real_subject: ISessionManager, ttl_seconds: int = 3):
        self._real         = real_subject   
        self._ttl          = ttl_seconds
        self._stats_cache: Optional[dict]   = None
        self._cache_time:  Optional[datetime] = None
        self._hit_count    = 0
        self._miss_count   = 0

    def _cache_valid(self) -> bool:
        if self._stats_cache is None or self._cache_time is None:
            return False
        age = (datetime.now() - self._cache_time).total_seconds()
        return age < self._ttl

    def get_statistics(self) -> dict:
        if self._cache_valid():
            self._hit_count += 1
            print(f"  [CachingProxy] HIT #{self._hit_count}: статистика из кэша")
            return dict(self._stats_cache)

        self._miss_count += 1
        print(f"  [CachingProxy] MISS #{self._miss_count}: запрос к RealSubject")
        self._stats_cache = self._real.get_statistics()   
        self._cache_time  = datetime.now()
        return dict(self._stats_cache)

    def invalidate(self):
        self._stats_cache = None
        self._cache_time  = None
        print("  [CachingProxy] Кэш сброшен")

    def cache_stats(self) -> str:
        return f"hits={self._hit_count}, misses={self._miss_count}"

    def add_task(self, task):
        self.invalidate()                  
        self._real.add_task(task)

    def remove_task(self, tid):
        self.invalidate()
        self._real.remove_task(tid)

    def get_all_tasks(self):               return self._real.get_all_tasks()
    def mark_task_completed(self, tid):
        self.invalidate()
        return self._real.mark_task_completed(tid)
    def add_study_plan(self, plan):
        self.invalidate()
        self._real.add_study_plan(plan)
    def get_all_plans(self):               return self._real.get_all_plans()
    def get_event_log(self):               return self._real.get_event_log()
    def set_theme(self, t):                self._real.set_theme(t)
    def get_theme(self):                   return self._real.get_theme()

class LoggingProxy(ISessionManager):
   

    def __init__(self, real_subject: ISessionManager):
        self._real = real_subject
        self._audit: list = []

    def _log(self, action: str, detail: str = ""):
        entry = {"time": datetime.now().strftime("%H:%M:%S"),
                 "action": action, "detail": detail}
        self._audit.append(entry)
        print(f"  [LoggingProxy] {entry['time']} | {action}" +
              (f" | {detail}" if detail else ""))

    def add_task(self, task):
        self._log("add_task", task.title)
        self._real.add_task(task)

    def remove_task(self, tid):
        self._log("remove_task", f"id={tid}")
        self._real.remove_task(tid)

    def get_all_tasks(self):
        self._log("get_all_tasks")
        return self._real.get_all_tasks()

    def mark_task_completed(self, tid):
        self._log("mark_task_completed", f"id={tid}")
        return self._real.mark_task_completed(tid)

    def add_study_plan(self, plan):
        self._log("add_study_plan", plan.subject)
        self._real.add_study_plan(plan)

    def get_all_plans(self):
        self._log("get_all_plans")
        return self._real.get_all_plans()

    def get_statistics(self):
        self._log("get_statistics")
        return self._real.get_statistics()

    def get_event_log(self):
        self._log("get_event_log")
        return self._real.get_event_log()

    def set_theme(self, t):
        self._log("set_theme", t)
        self._real.set_theme(t)

    def get_theme(self):
        self._log("get_theme")
        return self._real.get_theme()

    def get_audit(self) -> list:
        return list(self._audit)





from datetime import datetime, timedelta
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from patterns.singleton      import StudySessionManager
from patterns.factory_method import (LectureTaskCreator, PracticeTaskCreator,
                                     RevisionTaskCreator)
from patterns.builder        import PlannerDirector, IntensivePlanBuilder, RelaxedPlanBuilder
from patterns.prototype      import TemplateRegistry
from patterns.abstract_factory import LightThemeFactory, DarkThemeFactory, ThemeManager


class SmartStudyFacade:
   

    def __init__(self, theme: str = "light"):
        self._manager  = StudySessionManager.get_instance()  

        factory        = LightThemeFactory() if theme == "light" else DarkThemeFactory()
        self._theme_mgr = ThemeManager(factory)              

        self._creators = {                                     
            "Лекция":     LectureTaskCreator(),
            "Практика":   PracticeTaskCreator(),
            "Повторение": RevisionTaskCreator(),
        }

        self._director  = PlannerDirector()                    
        self._registry  = TemplateRegistry()                  
  
    def create_full_session(self, subject: str, days: int,
                            daily_hours: float = 3.0,
                            plan_type: str = "intensive") -> dict:
      
        exam_date = datetime.now() + timedelta(days=days)

       
        builder = IntensivePlanBuilder() if plan_type == "intensive" else RelaxedPlanBuilder()
        self._director.set_builder(builder)
        plan = self._director.build_full_plan(subject, exam_date, daily_hours)

        tasks_created = []
        deadline = exam_date - timedelta(days=2)
        for task_info in plan.tasks[:3]:   
            ttype   = task_info["type"]
            creator = self._creators.get(ttype, self._creators["Лекция"])
            task    = creator.create_and_register(
                task_info["title"], subject, task_info["duration"], deadline
            )
            tasks_created.append(task)

        stats = self._manager.get_statistics()

        return {
            "plan":   plan,
            "tasks":  tasks_created,
            "stats":  stats,
            "summary": (f"Сессия: [{subject}] | план '{plan.plan_type}' | "
                        f"{len(tasks_created)} задач | "
                        f"итого задач: {stats['total_tasks']}")
        }

  
    def clone_and_create_task(self, template_key: str,
                               subject: str, days_until_deadline: int) -> str:
        
        try:
            cloned   = self._registry.clone(template_key).customize(subject=subject)
            deadline = datetime.now() + timedelta(days=days_until_deadline)
            td       = cloned.to_task_dict(deadline)
            creator  = self._creators.get(cloned.task_type, self._creators["Лекция"])
            task     = creator.create_and_register(
                td["title"], td["subject"], td["duration"], td["deadline"]
            )
            return f"✅ Клонирован '{template_key}' → задача '{task.title}'"
        except KeyError as e:
            return f"❌ Ошибка: {e}"


    def switch_theme(self, theme: str) -> dict:
       
        factory = LightThemeFactory() if theme == "light" else DarkThemeFactory()
        self._theme_mgr.switch_factory(factory)
        cfg = self._theme_mgr.get_widget_configs()
        return {"theme": cfg["theme_name"], "root_bg": cfg["root_bg"]}

 
    def get_session_summary(self) -> str:
        stats = self._manager.get_statistics()
        plans = self._manager.get_all_plans()
        lines = [
            "╔══ СВОДКА СЕССИИ ══╗",
            f"  Задач всего:    {stats['total_tasks']}",
            f"  Выполнено:      {stats['completed_tasks']}",
            f"  Прогресс:       {stats['progress_percent']}%",
            f"  Планов:         {stats['total_plans']}",
            f"  Тема:           {stats['theme']}",
        ]
        if plans:
            lines.append("  Планы:")
            for p in plans:
                lines.append(f"    • [{p.plan_type}] {p.subject}")
        lines.append("╚═══════════════════╝")
        return "\n".join(lines)



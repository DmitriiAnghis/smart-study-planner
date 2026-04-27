

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from patterns.factory_method import StudyTask, LectureTask, PracticeTask, RevisionTask
from patterns.singleton import StudySessionManager


class PlanComponent(ABC):
   

    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    def operation(self, indent: int = 0) -> str:
        """Operation() из GoF — рекурсивный обход."""
        pass

    @abstractmethod
    def get_total_minutes(self) -> int: pass

    @abstractmethod
    def get_task_count(self) -> int: pass

    @abstractmethod
    def get_completed_count(self) -> int: pass

    def add(self, component: "PlanComponent") -> None:
        raise NotImplementedError(f"{self.__class__.__name__}: add() не поддерживается")

    def remove(self, component: "PlanComponent") -> None:
        raise NotImplementedError(f"{self.__class__.__name__}: remove() не поддерживается")

    def get_child(self, i: int) -> "PlanComponent":
        raise NotImplementedError(f"{self.__class__.__name__}: get_child() не поддерживается")

    def is_composite(self) -> bool:
        return False


class TaskLeaf(PlanComponent):
  

    def __init__(self, task: StudyTask):
        super().__init__(task.title)
        self._task = task

    @property
    def task(self) -> StudyTask:
        return self._task

    def operation(self, indent: int = 0) -> str:
        prefix = "  " * indent
        status = "✅" if self._task.completed else "⬜"
        return (f"{prefix}{status} [{self._task.get_type():10}] "
                f"{self._task.title} ({self._task.duration_minutes} мин) "
                f"[{self._task.priority}]")

    def get_total_minutes(self) -> int:
        return self._task.duration_minutes

    def get_task_count(self) -> int:
        return 1

    def get_completed_count(self) -> int:
        return 1 if self._task.completed else 0

class StudyPlanSection(PlanComponent):
    

    def __init__(self, name: str, icon: str = "📁"):
        super().__init__(name)
        self._icon     = icon
        self._children: List[PlanComponent] = []   

    def is_composite(self) -> bool:
        return True

    def add(self, component: PlanComponent) -> "StudyPlanSection":
        self._children.append(component)
        return self  

    def remove(self, component: PlanComponent) -> None:
        self._children.remove(component)

    def get_child(self, i: int) -> PlanComponent:
        return self._children[i]

    def operation(self, indent: int = 0) -> str:
        prefix = "  " * indent
        total  = self.get_total_minutes()
        done   = self.get_completed_count()
        total_tasks = self.get_task_count()
        progress = f"{done}/{total_tasks}" if total_tasks else "0/0"
        lines = [f"{prefix}{self._icon} {self._name} "
                 f"[{total} мин | {progress} выполнено]"]
        for child in self._children:
            lines.append(child.operation(indent + 1))
        return "\n".join(lines)

    def get_total_minutes(self) -> int:
        return sum(c.get_total_minutes() for c in self._children)

    def get_task_count(self) -> int:
        return sum(c.get_task_count() for c in self._children)

    def get_completed_count(self) -> int:
        return sum(c.get_completed_count() for c in self._children)

    def get_all_task_leaves(self) -> List[TaskLeaf]:
        leaves = []
        for c in self._children:
            if isinstance(c, TaskLeaf):
                leaves.append(c)
            elif c.is_composite():
                leaves.extend(c.get_all_task_leaves())
        return leaves


class PlanTreeBuilder:
  

    @staticmethod
    def build_intensive(subject: str, deadline) -> StudyPlanSection:
        from datetime import timedelta
        root = StudyPlanSection(f"📚 Интенсивный план: {subject}", "📚")

        theory = StudyPlanSection("Теория", "📖")
        theory.add(TaskLeaf(LectureTask(f"Полный курс: {subject}",
                                        subject, 120, deadline)))
        theory.add(TaskLeaf(LectureTask(f"Ключевые концепции: {subject}",
                                        subject, 60, deadline)))

        practice = StudyPlanSection("Практика", "✏️")
        practice.add(TaskLeaf(PracticeTask(f"Задачи повышенной сложности",
                                            subject, 90, deadline)))
        practice.add(TaskLeaf(PracticeTask(f"Пробный экзамен: {subject}",
                                            subject, 120, deadline)))

        revision = StudyPlanSection("Повторение", "🔄")
        revision.add(TaskLeaf(RevisionTask(f"Быстрое повторение всех тем",
                                            subject, 45, deadline)))

        root.add(theory).add(practice).add(revision)
        return root

    @staticmethod
    def build_relaxed(subject: str, deadline) -> StudyPlanSection:
        root = StudyPlanSection(f"🌿 Расслабленный план: {subject}", "🌿")
        root.add(TaskLeaf(LectureTask(f"Основные темы: {subject}", subject, 60, deadline)))
        root.add(TaskLeaf(PracticeTask(f"Базовые упражнения", subject, 45, deadline)))
        root.add(TaskLeaf(RevisionTask(f"Повторение ключевых концепций", subject, 30, deadline)))
        return root


def demo():
    from datetime import timedelta

    print("=" * 65)
    print("  COMPOSITE — интеграция в Smart Study Planner")
    print("=" * 65)

    deadline = datetime.now() + timedelta(days=14)

    math_tree    = PlanTreeBuilder.build_intensive("Математика", deadline)
    physics_tree = PlanTreeBuilder.build_relaxed("Физика", deadline)

    print("\n📌 1. Интенсивный план (Composite из Composite + Leaf):")
    print(math_tree.operation())
    print(f"\n  Итого: {math_tree.get_task_count()} задач, "
          f"{math_tree.get_total_minutes()} мин")

    print("\n📌 2. Расслабленный план:")
    print(physics_tree.operation())

    print("\n📌 3. Корень — весь семестр (два плана как дети):")
    semester = StudyPlanSection("🎓 Весь семестр", "🎓")
    semester.add(math_tree)
    semester.add(physics_tree)
    from patterns.factory_method import PracticeTaskCreator
    exam_task = PracticeTask("Финальный экзамен", "Все предметы", 180, deadline)
    semester.add(TaskLeaf(exam_task))
    print(semester.operation())

    print(f"\n  Итого по семестру: {semester.get_task_count()} задач, "
          f"{semester.get_total_minutes()} мин "
          f"({semester.get_total_minutes()/60:.1f} ч)")

    print("\n📌 4. Отмечаем задачи выполненными:")
    leaves = math_tree.get_all_task_leaves()
    leaves[0].task.completed = True
    leaves[1].task.completed = True
    print(math_tree.operation())

    print("\n📌 5. Регистрируем все задачи из дерева в StudySessionManager:")
    manager = StudySessionManager.get_instance()
    all_leaves = semester.get_all_task_leaves()
    for leaf in all_leaves:
        manager.add_task(leaf.task)
    stats = manager.get_statistics()
    print(f"  Задач в сессии: {stats['total_tasks']}")
    print(f"  Выполнено:      {stats['completed_tasks']}")

    print("\n✅ Client обращался к semester, math_tree и exam_task")
    print("   через один интерфейс operation() — это и есть Composite.")
    print("=" * 65)


if __name__ == "__main__":
    demo()

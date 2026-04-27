"""
================================================================================
  ТЕСТ СТРУКТУРНЫХ ПАТТЕРНОВ — Smart Study Planner
  Запуск: python test_structural.py
  
  Проверяет все 5 структурных паттернов по очереди.
  Если паттерн работает — увидишь ✅ в конце его блока.
  Если упал — увидишь ❌ и текст ошибки.
================================================================================
"""

import sys
import os
import traceback

# ── чтобы импорты работали из корня проекта ───────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── сбрасываем Singleton между тестами ────────────────────────────────────────
def reset_singleton():
    from patterns.singleton import StudySessionManager
    StudySessionManager.reset_instance()


RESULTS = {}


def run_pattern(name: str, module_path: str):
    """Запускает demo() одного паттерна и ловит любые ошибки."""
    print("\n")
    print("█" * 65)
    print(f"  ЗАПУСК: {name}")
    print("█" * 65)

    reset_singleton()   # чистый менеджер для каждого теста

    try:
        # Динамически импортируем модуль
        import importlib
        mod = importlib.import_module(module_path)
        mod.demo()
        RESULTS[name] = "✅  PASSED"
    except Exception as e:
        RESULTS[name] = f"❌  FAILED — {e}"
        print(f"\n  ОШИБКА в {name}:")
        traceback.print_exc()


# ══════════════════════════════════════════════════════════════════════════════
#  ЗАПУСКАЕМ ВСЕ 5 ПАТТЕРНОВ
#  Измени путь если положил файлы в patterns/structural/
#  Например: "patterns.structural.decorator"
# ══════════════════════════════════════════════════════════════════════════════

run_pattern("Decorator", "patterns.structural.decorator")
run_pattern("Facade",    "patterns.structural.facade")
run_pattern("Proxy",     "patterns.structural.proxy")
run_pattern("Composite", "patterns.structural.composite")
run_pattern("Adapter",   "patterns.structural.adapter")


# ── Итоговая таблица ──────────────────────────────────────────────────────────
print("\n")
print("═" * 65)
print("  ИТОГИ ТЕСТИРОВАНИЯ")
print("═" * 65)
all_passed = True
for name, result in RESULTS.items():
    print(f"  {result:6}  {name}")
    if "FAILED" in result:
        all_passed = False

print("─" * 65)
if all_passed:
    print("  ВСЕ ПАТТЕРНЫ РАБОТАЮТ КОРРЕКТНО 🎉")
else:
    print("  ЕСТЬ ОШИБКИ — см. вывод выше ☝️")
print("═" * 65)

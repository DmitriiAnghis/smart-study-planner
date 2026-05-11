"""
================================================================================
  ТЕСТ ПОВЕДЕНЧЕСКИХ ПАТТЕРНОВ — Smart Study Planner
  Запуск: python test_behavioral.py

  Проверяет все 5 поведенческих паттернов по очереди.
  Если паттерн работает — увидишь ✅ в конце его блока.
  Если упал — увидишь ❌ и текст ошибки.
================================================================================
"""

import sys
import os
import traceback

# ── чтобы импорты работали из корня проекта ──────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ── сбрасываем Singleton между тестами ───────────────────────────────────────
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

    reset_singleton()

    try:
        import importlib
        if module_path in sys.modules:
            mod = importlib.reload(sys.modules[module_path])
        else:
            mod = importlib.import_module(module_path)
        mod.demo()
        RESULTS[name] = "✅  PASSED"
    except Exception as e:
        RESULTS[name] = f"❌  FAILED — {e}"
        print(f"\n  ОШИБКА в {name}:")
        traceback.print_exc()


# ══════════════════════════════════════════════════════════════════════════════
#  ЗАПУСКАЕМ ВСЕ 5 ПОВЕДЕНЧЕСКИХ ПАТТЕРНОВ
# ══════════════════════════════════════════════════════════════════════════════

run_pattern("Observer",                "patterns.behavioral.observer")
run_pattern("Command",                 "patterns.behavioral.command")
run_pattern("Strategy",                "patterns.behavioral.strategy")
run_pattern("State",                   "patterns.behavioral.state")
run_pattern("Chain of Responsibility", "patterns.behavioral.chain_of_responsibility")


# ── Итоговая таблица ──────────────────────────────────────────────────────────
print("\n")
print("═" * 65)
print("  ИТОГИ ТЕСТИРОВАНИЯ — BEHAVIORAL PATTERNS")
print("═" * 65)
all_passed = True
for name, result in RESULTS.items():
    print(f"  {result}  {name}")
    if "FAILED" in result:
        all_passed = False

print("─" * 65)
if all_passed:
    print("  ВСЕ ПАТТЕРНЫ РАБОТАЮТ КОРРЕКТНО 🎉")
else:
    print("  ЕСТЬ ОШИБКИ — см. вывод выше ☝️")
print("═" * 65)

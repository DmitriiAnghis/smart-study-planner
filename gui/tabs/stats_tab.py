import tkinter as tk
from tkinter import ttk


class StatsTab:
   

    def __init__(self, notebook, manager):
       
        self.manager = manager

        self.frame = tk.Frame(notebook)
        notebook.add(self.frame, text="  📊  Статистика  ")

        self._build()

    def _build(self):
        tab = self.frame

        tk.Label(tab, text="Статистика сессии (Singleton)",
                 font=("Segoe UI", 13, "bold")).pack(
                     anchor="w", padx=16, pady=(14, 10))

        # Карточки
        cards_frame = tk.Frame(tab)
        cards_frame.pack(fill="x", padx=16, pady=(0, 10))

        self.stat_cards = {}
        card_defs = [
            ("total_tasks", "Всего задач",  "📝"),
            ("completed",   "Выполнено",    "✅"),
            ("progress",    "Прогресс",     "📈"),
            ("plans",       "Планов",       "📅"),
        ]
        for key, label, icon in card_defs:
            card = tk.Frame(cards_frame, relief="flat", padx=18, pady=14)
            card.pack(side="left", padx=6, fill="y")
            tk.Label(card, text=icon, font=("Segoe UI", 22)).pack()
            val_lbl = tk.Label(card, text="0", font=("Segoe UI", 20, "bold"))
            val_lbl.pack()
            tk.Label(card, text=label, font=("Segoe UI", 9)).pack()
            self.stat_cards[key] = val_lbl

        # Лог событий
        tk.Label(tab, text="Лог событий сессии:",
                 font=("Segoe UI", 11, "bold")).pack(
                     anchor="w", padx=16, pady=(6, 4))

        log_frame = tk.Frame(tab)
        log_frame.pack(fill="both", expand=True, padx=16, pady=(0, 14))

        self.log_text = tk.Text(log_frame, font=("Consolas", 9),
                                 relief="flat", state="disabled", wrap="word")
        sc = ttk.Scrollbar(log_frame, orient="vertical",
                           command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=sc.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        sc.pack(side="right", fill="y")

        # Кнопка обновить
        tk.Button(tab, text="🔄  Обновить",
                  font=("Segoe UI", 10),
                  relief="flat", padx=12, pady=6,
                  cursor="hand2",
                  command=self.refresh).pack(padx=16, pady=(0, 14))

    def refresh(self):
        stats = self.manager.get_statistics()
        self.stat_cards["total_tasks"].config(text=str(stats["total_tasks"]))
        self.stat_cards["completed"].config(text=str(stats["completed_tasks"]))
        self.stat_cards["progress"].config(text=f"{stats['progress_percent']}%")
        self.stat_cards["plans"].config(text=str(stats["total_plans"]))

        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        for entry in reversed(self.manager.get_event_log()):
            self.log_text.insert(
                "end", f"[{entry['time']}]  {entry['message']}\n")
        self.log_text.configure(state="disabled")
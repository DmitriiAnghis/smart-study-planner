import tkinter as tk
from tkinter import ttk
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from patterns.structural.proxy import RealSessionManager, ProtectionProxy, CachingProxy


# права, которые разрешены каждой роли
_ROLE_PERMS = {
    "student": ["просмотр задач", "просмотр планов", "статистика"],
    "teacher": ["просмотр задач", "просмотр планов", "статистика",
                "добавить задачу", "отметить выполненной"],
    "admin":   ["всё"],
}

# что заблокировано для роли (для подсказки)
_ROLE_BLOCKED = {
    "student": "добавление / удаление задач",
    "teacher": "удаление задач и планов",
    "admin":   "ничего — полный доступ",
}


class StatsTab:

    def __init__(self, notebook, manager):
        self.manager = manager

        # Proxy-слои поверх реального менеджера
        self._real          = RealSessionManager()
        self._caching_proxy = CachingProxy(self._real, ttl_seconds=5)
        self._active_proxy  = self._real          # по умолчанию — прямой доступ

        # переменная роли — используется в app.py для блокировки кнопок Tasks
        self.role_var = tk.StringVar(value="admin")

        self.frame = tk.Frame(notebook)
        notebook.add(self.frame, text="  📊  Статистика  ")
        self._build()

    def _build(self):
        tab = self.frame

        # ── Заголовок + PROXY — переключатель роли ───────────────────────
        top = tk.Frame(tab)
        top.pack(fill="x", padx=16, pady=(14, 0))

        tk.Label(top, text="Статистика сессии  (Singleton)",
                 font=("Segoe UI", 13, "bold")).pack(side="left")

        proxy_frame = tk.LabelFrame(
            top, text=" 🛡 Proxy — роль пользователя ",
            font=("Segoe UI", 9, "bold"), padx=8, pady=4)
        proxy_frame.pack(side="right")

        for role in ["student", "teacher", "admin"]:
            tk.Radiobutton(proxy_frame, text=role,
                           variable=self.role_var, value=role,
                           font=("Segoe UI", 9),
                           command=self._on_role_change
                           ).pack(side="left", padx=4)

        # строка с описанием текущих прав
        self._role_label = tk.Label(tab, text="",
                                     font=("Segoe UI", 8), fg="#888", anchor="e")
        self._role_label.pack(fill="x", padx=16)
        self._update_role_label()

        # ── Карточки статистики ───────────────────────────────────────────
        cards_frame = tk.Frame(tab)
        cards_frame.pack(fill="x", padx=16, pady=(8, 0))

        self.stat_cards = {}
        card_defs = [
            ("total_tasks", "Всего задач", "📝"),
            ("completed",   "Выполнено",   "✅"),
            ("progress",    "Прогресс",    "📈"),
            ("plans",       "Планов",      "📅"),
        ]
        for key, label, icon in card_defs:
            card = tk.Frame(cards_frame, relief="flat", padx=18, pady=14)
            card.pack(side="left", padx=6, fill="y")
            tk.Label(card, text=icon, font=("Segoe UI", 22)).pack()
            val_lbl = tk.Label(card, text="0", font=("Segoe UI", 20, "bold"))
            val_lbl.pack()
            tk.Label(card, text=label, font=("Segoe UI", 9)).pack()
            self.stat_cards[key] = val_lbl

        # ── Лог событий ──────────────────────────────────────────────────
        log_header = tk.Frame(tab)
        log_header.pack(fill="x", padx=16, pady=(10, 2))
        tk.Label(log_header, text="Лог событий сессии:",
                 font=("Segoe UI", 11, "bold")).pack(side="left")

        # индикатор Proxy активен / не активен
        self._proxy_badge = tk.Label(
            log_header, text="",
            font=("Segoe UI", 8), padx=6, pady=2, relief="flat")
        self._proxy_badge.pack(side="right")
        self._update_proxy_badge()

        log_frame = tk.Frame(tab)
        log_frame.pack(fill="both", expand=True, padx=16, pady=(0, 4))

        self.log_text = tk.Text(log_frame, font=("Consolas", 9),
                                 relief="flat", state="disabled", wrap="word")
        sc = ttk.Scrollbar(log_frame, orient="vertical",
                           command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=sc.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        sc.pack(side="right", fill="y")

        # ── Кнопки ───────────────────────────────────────────────────────
        btn_row = tk.Frame(tab)
        btn_row.pack(fill="x", padx=16, pady=(0, 10))

        tk.Button(btn_row, text="🔄  Обновить",
                  font=("Segoe UI", 10),
                  relief="flat", padx=12, pady=6,
                  cursor="hand2",
                  command=self.refresh).pack(side="left")

        tk.Button(btn_row, text="⚡  Вкл. CachingProxy",
                  font=("Segoe UI", 9),
                  relief="flat", padx=8, pady=6,
                  cursor="hand2",
                  command=self._enable_caching).pack(side="left", padx=8)

        tk.Button(btn_row, text="🔓  Прямой доступ",
                  font=("Segoe UI", 9),
                  relief="flat", padx=8, pady=6,
                  cursor="hand2",
                  command=self._disable_caching).pack(side="left")

        self._cache_label = tk.Label(btn_row, text="",
                                      font=("Segoe UI", 8), fg="#888")
        self._cache_label.pack(side="right")


    def _on_role_change(self):
        """Вызывается при смене роли — обновляет подсказку и сигнализирует app."""
        self._update_role_label()
        self._update_proxy_badge()
        # публичный callback — app.py подключает его к обновлению кнопок Tasks
        if hasattr(self, "_on_role_cb") and self._on_role_cb:
            self._on_role_cb(self.role_var.get())

    def set_role_callback(self, cb):
        """app.py передаёт функцию, которая реагирует на смену роли."""
        self._on_role_cb = cb

    def get_protection_proxy(self):
        """Возвращает ProtectionProxy с текущей ролью — для использования в Tasks."""
        return ProtectionProxy(self._real, role=self.role_var.get())

    def _update_role_label(self):
        role = self.role_var.get()
        perms = ", ".join(_ROLE_PERMS[role])
        blocked = _ROLE_BLOCKED[role]
        self._role_label.configure(
            text=f"Разрешено: {perms}   |   Заблокировано: {blocked}")

    def _update_proxy_badge(self):
        role = self.role_var.get()
        colors = {"student": ("#ffeeba", "#856404"),
                  "teacher": ("#d4edda", "#155724"),
                  "admin":   ("#d1ecf1", "#0c5460")}
        bg, fg = colors.get(role, ("#eee", "#333"))
        self._proxy_badge.configure(
            text=f"🛡 ProtectionProxy  role={role}",
            bg=bg, fg=fg)

    def _enable_caching(self):
        self._active_proxy = self._caching_proxy
        self._cache_label.configure(text="⚡ CachingProxy активен (TTL=5с)")
        self.refresh()

    def _disable_caching(self):
        self._active_proxy = self._real
        self._caching_proxy.invalidate()
        self._cache_label.configure(text="🔓 Прямой доступ к Singleton")
        self.refresh()


    def refresh(self):
        # статистика через активный proxy (Real или Caching)
        stats = self._active_proxy.get_statistics()
        self.stat_cards["total_tasks"].config(text=str(stats.get("total_tasks", 0)))
        self.stat_cards["completed"].config(text=str(stats.get("completed_tasks", 0)))
        self.stat_cards["progress"].config(text=f"{stats.get('progress_percent', 0)}%")
        self.stat_cards["plans"].config(text=str(stats.get("total_plans", 0)))

        # обновляем подпись кэша если он активен
        if self._active_proxy is self._caching_proxy:
            cs = self._caching_proxy.cache_stats()
            self._cache_label.configure(text=f"⚡ CachingProxy  {cs}")

        # лог событий — всегда напрямую
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        for entry in reversed(self.manager.get_event_log()):
            self.log_text.insert(
                "end", f"[{entry['time']}]  {entry['message']}\n")
        self.log_text.configure(state="disabled")
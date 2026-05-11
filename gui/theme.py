from patterns.abstract_factory import LightThemeFactory, DarkThemeFactory


class ThemeController:

    def __init__(self, root, theme_manager, manager,
                 header, title_label, theme_btn, statusbar,
                 notebook, tabs, text_widgets, stat_cards,
                 extra_header_widgets=None):

        self.root                  = root
        self.theme_manager         = theme_manager
        self.manager               = manager
        self.header                = header
        self.title_label           = title_label
        self.theme_btn             = theme_btn
        self.statusbar             = statusbar
        self.notebook              = notebook
        self.tabs                  = tabs
        self.text_widgets          = text_widgets
        self.stat_cards            = stat_cards
        # доп. виджеты в шапке (кнопка Facade и её подпись)
        self.extra_header_widgets  = extra_header_widgets or []

    def toggle(self, set_status_cb):
        current = self.manager.get_theme()
        if current == "light":
            self.theme_manager.switch_factory(DarkThemeFactory())
        else:
            self.theme_manager.switch_factory(LightThemeFactory())
        self.apply()
        set_status_cb(f"Тема изменена: {self.manager.get_theme()}")

    def apply(self):
        from tkinter import ttk
        cfg     = self.theme_manager.get_widget_configs()
        bg      = cfg["root_bg"]
        btn_cfg = cfg["button"]
        pan_cfg = cfg["panel"]
        lbl_cfg = cfg["label"]
        ent_cfg = cfg["entry"]
        t_name  = cfg["theme_name"]
        acc_fg  = cfg["label_accent"]["fg"]

        is_dark = (t_name == "dark")
        txt_bg  = "#1e2124" if is_dark else "#FFFFFF"
        card_bg = "#36393f" if is_dark else "#FFFFFF"

        self.root.configure(bg=bg)

        # шапка
        self.header.configure(bg=pan_cfg["bg"])
        self.title_label.configure(
            bg=pan_cfg["bg"],
            fg=pan_cfg.get("fg", lbl_cfg["fg"]),
            font=("Segoe UI", 17, "bold"))
        self.theme_btn.configure(
            bg=btn_cfg["bg"], fg=btn_cfg["fg"],
            activebackground=btn_cfg["activebackground"],
            font=btn_cfg["font"],
            text="☀️  Светлая тема" if is_dark else "🌙  Тёмная тема")
        self.statusbar.configure(bg=pan_cfg["bg"], fg=lbl_cfg["fg"])

        # доп. виджеты шапки (Facade-кнопка и подпись)
        facade_accent = "#f39c12" if not is_dark else "#f1c40f"
        for w in self.extra_header_widgets:
            try:
                wtype = w.winfo_class()
                if wtype == "Button":
                    w.configure(
                        bg=facade_accent, fg="#FFFFFF",
                        activebackground="#d68910",
                        font=("Segoe UI", 10, "bold"))
                elif wtype == "Label":
                    w.configure(bg=pan_cfg["bg"], fg=facade_accent,
                                font=("Segoe UI", 7))
            except Exception:
                pass

        # Notebook
        style   = ttk.Style()
        tab_bg  = "#40444b" if is_dark else "#e0e6ef"
        tab_fg  = "#ffffff" if is_dark else "#2c3e50"
        style.configure("TNotebook", background=pan_cfg["bg"], borderwidth=0)
        style.configure("TNotebook.Tab",
                         background=tab_bg, foreground=tab_fg,
                         font=("Segoe UI", 10), padding=[10, 5])
        style.map("TNotebook.Tab",
                  background=[("selected", bg)],
                  foreground=[("selected", acc_fg)])

        # Treeview
        tree_bg   = "#2f3136" if is_dark else "#FFFFFF"
        tree_fg   = "#dcddde" if is_dark else "#2c3e50"
        tree_head = "#40444b" if is_dark else "#dce3ec"
        tree_sel  = "#5865f2" if is_dark else "#4a90d9"
        style.configure("Treeview",
                         background=tree_bg, foreground=tree_fg,
                         rowheight=26, fieldbackground=tree_bg,
                         font=("Segoe UI", 9))
        style.configure("Treeview.Heading",
                         background=tree_head, foreground=tree_fg,
                         font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", tree_sel)])

        style.configure("TCombobox",
                         fieldbackground=ent_cfg["bg"],
                         background=ent_cfg["bg"],
                         foreground=ent_cfg["fg"],
                         selectbackground=btn_cfg["bg"])
        style.configure("Vertical.TScrollbar",
                         background=pan_cfg["bg"],
                         troughcolor=pan_cfg["bg"])

        for frame in self.tabs:
            self._apply_recursive(frame, bg, lbl_cfg, btn_cfg,
                                   ent_cfg, txt_bg, card_bg)

        for tw in self.text_widgets:
            try:
                tw.configure(bg=txt_bg, fg=lbl_cfg["fg"],
                             insertbackground=lbl_cfg["fg"])
            except Exception:
                pass

        for key, lbl in self.stat_cards.items():
            lbl.master.configure(bg=card_bg)
            for child in lbl.master.winfo_children():
                try:
                    child.configure(bg=card_bg, fg=lbl_cfg["fg"])
                except Exception:
                    pass
            lbl.configure(fg=acc_fg)

    def _apply_recursive(self, widget, bg, lbl_cfg, btn_cfg,
                          ent_cfg, txt_bg, card_bg):
        try:
            wtype = widget.winfo_class()
            if wtype in ("Frame", "Labelframe"):
                widget.configure(bg=bg)
            elif wtype == "Label":
                widget.configure(bg=bg, fg=lbl_cfg["fg"])
            elif wtype == "Button":
                widget.configure(
                    bg=btn_cfg["bg"], fg=btn_cfg["fg"],
                    activebackground=btn_cfg["activebackground"],
                    activeforeground=btn_cfg["fg"])
            elif wtype == "Entry":
                widget.configure(
                    bg=ent_cfg["bg"], fg=ent_cfg["fg"],
                    insertbackground=ent_cfg["fg"],
                    relief="solid", borderwidth=1)
            elif wtype == "Spinbox":
                widget.configure(
                    bg=ent_cfg["bg"], fg=ent_cfg["fg"],
                    insertbackground=ent_cfg["fg"])
            elif wtype == "Radiobutton":
                widget.configure(
                    bg=bg, fg=lbl_cfg["fg"],
                    activebackground=bg,
                    selectcolor=btn_cfg["bg"])
            elif wtype == "Checkbutton":
                widget.configure(bg=bg, fg=lbl_cfg["fg"],
                                  activebackground=bg)
            elif wtype == "Text":
                widget.configure(bg=txt_bg, fg=lbl_cfg["fg"],
                                  insertbackground=lbl_cfg["fg"])
        except Exception:
            pass

        for child in widget.winfo_children():
            self._apply_recursive(child, bg, lbl_cfg, btn_cfg,
                                   ent_cfg, txt_bg, card_bg)
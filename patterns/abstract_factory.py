from abc import ABC, abstractmethod


class AbstractButton(ABC):
    @abstractmethod
    def render(self) -> dict: pass

    @abstractmethod
    def get_hover_config(self) -> dict: pass

    def __repr__(self): return f"{self.__class__.__name__}"


class AbstractPanel(ABC):
    @abstractmethod
    def render(self) -> dict: pass

    @abstractmethod
    def get_title_config(self) -> dict: pass


class AbstractLabel(ABC):
    @abstractmethod
    def render(self) -> dict: pass

    @abstractmethod
    def render_accent(self) -> dict: pass


class AbstractEntry(ABC):
    @abstractmethod
    def render(self) -> dict: pass


class LightButton(AbstractButton):
    def render(self) -> dict:
        return {
            "bg": "#4A90D9", "fg": "#FFFFFF",
            "font": ("Segoe UI", 10, "bold"),
            "relief": "flat", "padx": 16, "pady": 8,
            "cursor": "hand2", "borderwidth": 0,
            "activebackground": "#357ABD", "activeforeground": "#FFFFFF",
        }
    def get_hover_config(self) -> dict: return {"bg": "#357ABD"}


class LightPanel(AbstractPanel):
    def render(self) -> dict:
        return {"bg": "#F5F7FA", "relief": "flat", "borderwidth": 0, "padx": 12, "pady": 12}
    def get_title_config(self) -> dict:
        return {"bg": "#F5F7FA", "fg": "#2C3E50", "font": ("Segoe UI", 13, "bold")}


class LightLabel(AbstractLabel):
    def render(self) -> dict:
        return {"bg": "#F5F7FA", "fg": "#2C3E50", "font": ("Segoe UI", 10)}
    def render_accent(self) -> dict:
        return {"bg": "#F5F7FA", "fg": "#E74C3C", "font": ("Segoe UI", 10, "bold")}


class LightEntry(AbstractEntry):
    def render(self) -> dict:
        return {"bg": "#FFFFFF", "fg": "#2C3E50", "font": ("Segoe UI", 10),
                "relief": "solid", "borderwidth": 1, "insertbackground": "#2C3E50"}


class DarkButton(AbstractButton):
    def render(self) -> dict:
        return {
            "bg": "#5865F2", "fg": "#FFFFFF",
            "font": ("Segoe UI", 10, "bold"),
            "relief": "flat", "padx": 16, "pady": 8,
            "cursor": "hand2", "borderwidth": 0,
            "activebackground": "#4752C4", "activeforeground": "#FFFFFF",
        }
    def get_hover_config(self) -> dict: return {"bg": "#4752C4"}


class DarkPanel(AbstractPanel):
    def render(self) -> dict:
        return {"bg": "#2C2F33", "relief": "flat", "borderwidth": 0, "padx": 12, "pady": 12}
    def get_title_config(self) -> dict:
        return {"bg": "#2C2F33", "fg": "#FFFFFF", "font": ("Segoe UI", 13, "bold")}


class DarkLabel(AbstractLabel):
    def render(self) -> dict:
        return {"bg": "#2C2F33", "fg": "#DCDDDE", "font": ("Segoe UI", 10)}
    def render_accent(self) -> dict:
        return {"bg": "#2C2F33", "fg": "#FF6B6B", "font": ("Segoe UI", 10, "bold")}


class DarkEntry(AbstractEntry):
    def render(self) -> dict:
        return {"bg": "#40444B", "fg": "#DCDDDE", "font": ("Segoe UI", 10),
                "relief": "solid", "borderwidth": 1, "insertbackground": "#DCDDDE"}


class UIThemeFactory(ABC):
    @abstractmethod
    def create_button(self) -> AbstractButton: pass
    @abstractmethod
    def create_panel(self) -> AbstractPanel: pass
    @abstractmethod
    def create_label(self) -> AbstractLabel: pass
    @abstractmethod
    def create_entry(self) -> AbstractEntry: pass
    @abstractmethod
    def get_theme_name(self) -> str: pass
    @abstractmethod
    def get_root_bg(self) -> str: pass


class LightThemeFactory(UIThemeFactory):
    def create_button(self) -> AbstractButton: return LightButton()
    def create_panel(self)  -> AbstractPanel:  return LightPanel()
    def create_label(self)  -> AbstractLabel:  return LightLabel()
    def create_entry(self)  -> AbstractEntry:  return LightEntry()
    def get_theme_name(self) -> str: return "light"
    def get_root_bg(self)    -> str: return "#F5F7FA"


class DarkThemeFactory(UIThemeFactory):
    def create_button(self) -> AbstractButton: return DarkButton()
    def create_panel(self)  -> AbstractPanel:  return DarkPanel()
    def create_label(self)  -> AbstractLabel:  return DarkLabel()
    def create_entry(self)  -> AbstractEntry:  return DarkEntry()
    def get_theme_name(self) -> str: return "dark"
    def get_root_bg(self)    -> str: return "#23272A"


class ThemeManager:

    def __init__(self, factory: UIThemeFactory):
        self._factory = factory
        self.button   = self._factory.create_button()
        self.panel    = self._factory.create_panel()
        self.label    = self._factory.create_label()
        self.entry    = self._factory.create_entry()
        from patterns.singleton import StudySessionManager
        StudySessionManager.get_instance().set_theme(factory.get_theme_name())

    def switch_factory(self, new_factory: UIThemeFactory):
        self._factory = new_factory
        self.button   = self._factory.create_button()
        self.panel    = self._factory.create_panel()
        self.label    = self._factory.create_label()
        self.entry    = self._factory.create_entry()
        from patterns.singleton import StudySessionManager
        StudySessionManager.get_instance().set_theme(new_factory.get_theme_name())

    def get_widget_configs(self) -> dict:
        return {
            "button":       self.button.render(),
            "button_hover": self.button.get_hover_config(),
            "panel":        self.panel.render(),
            "panel_title":  self.panel.get_title_config(),
            "label":        self.label.render(),
            "label_accent": self.label.render_accent(),
            "entry":        self.entry.render(),
            "root_bg":      self._factory.get_root_bg(),
            "theme_name":   self._factory.get_theme_name(),
        }


def get_theme_factory(theme: str) -> UIThemeFactory:
    factories = {"light": LightThemeFactory, "dark": DarkThemeFactory}
    if theme not in factories:
        raise ValueError(f"Неизвестная тема: '{theme}'")
    return factories[theme]()

"""
Компоненты GUI - переиспользуемые виджеты
"""

import customtkinter as ctk
from typing import Optional, Callable, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class StatusIndicator(ctk.CTkFrame):
    """Индикатор статуса с цветом."""
    
    def __init__(
        self,
        master,
        text: str = "",
        status: str = "idle",
        width: int = 120,
        height: int = 30,
        **kwargs
    ):
        super().__init__(master, width=width, height=height, **kwargs)
        self.pack_propagate(False)
        
        self._status_colors = {
            "idle": "#95a5a6",
            "working": "#3498db",
            "waiting": "#f39c12",
            "error": "#e74c3c",
            "stopped": "#7f8c8d",
            "success": "#2ecc71",
        }
        
        # Индикатор (кружок)
        self.indicator = ctk.CTkLabel(
            self,
            text="●",
            font=ctk.CTkFont(size=16),
            text_color=self._status_colors.get(status, "#95a5a6")
        )
        self.indicator.pack(side="left", padx=(5, 0))
        
        # Текст
        self.label = ctk.CTkLabel(
            self,
            text=text,
            font=ctk.CTkFont(size=12),
            text_color="#ecf0f1"
        )
        self.label.pack(side="left", padx=(5, 0))
        
        self._current_status = status
    
    def set_status(self, status: str, text: Optional[str] = None):
        """Установка статуса."""
        self._current_status = status
        color = self._status_colors.get(status, "#95a5a6")
        self.indicator.configure(text_color=color)
        
        if text:
            self.label.configure(text=text)


class ToolCard(ctk.CTkFrame):
    """Карточка инструмента."""
    
    def __init__(
        self,
        master,
        name: str,
        description: str,
        icon: str = "🔧",
        enabled: bool = True,
        risk_level: str = "safe",
        on_toggle: Optional[Callable[[bool], None]] = None,
        **kwargs
    ):
        super().__init__(master, fg_color="#2b2b2b", **kwargs)
        
        self.on_toggle = on_toggle
        self.enabled = enabled
        
        self._risk_colors = {
            "safe": "#2ecc71",
            "review": "#f39c12",
            "dangerous": "#e74c3c",
        }
        
        self._create_widgets(name, description, icon, risk_level)
    
    def _create_widgets(self, name: str, description: str, icon: str, risk_level: str):
        """Создание виджетов карточки."""
        # Верхняя строка с иконкой и названием
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # Иконка
        icon_label = ctk.CTkLabel(
            top_frame,
            text=icon,
            font=ctk.CTkFont(size=20)
        )
        icon_label.pack(side="left")
        
        # Название
        name_label = ctk.CTkLabel(
            top_frame,
            text=name,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ecf0f1"
        )
        name_label.pack(side="left", padx=(10, 0))
        
        # Индикатор риска
        risk_color = self._risk_colors.get(risk_level, "#95a5a6")
        risk_indicator = ctk.CTkLabel(
            top_frame,
            text="●",
            font=ctk.CTkFont(size=10),
            text_color=risk_color
        )
        risk_indicator.pack(side="right")
        
        # Описание
        desc_label = ctk.CTkLabel(
            self,
            text=description,
            font=ctk.CTkFont(size=11),
            text_color="#7f8c8d",
            wraplength=250,
            justify="left"
        )
        desc_label.pack(anchor="w", padx=40, pady=(0, 10))
        
        # Переключатель
        toggle_frame = ctk.CTkFrame(self, fg_color="transparent")
        toggle_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.toggle_switch = ctk.CTkSwitch(
            toggle_frame,
            text="",
            command=self._on_toggle,
            onvalue=True,
            offvalue=False
        )
        self.toggle_switch.pack(side="right")
        self.toggle_switch.select() if self.enabled else self.toggle_switch.deselect()
    
    def _on_toggle(self):
        """Обработчик переключения."""
        self.enabled = self.toggle_switch.get()
        if self.on_toggle:
            self.on_toggle(self.enabled)
    
    def set_enabled(self, enabled: bool):
        """Установка состояния."""
        self.enabled = enabled
        if enabled:
            self.toggle_switch.select()
        else:
            self.toggle_switch.deselect()


class AgentCard(ctk.CTkFrame):
    """Карточка агента."""
    
    def __init__(
        self,
        master,
        name: str,
        role: str,
        status: str = "idle",
        tasks_completed: int = 0,
        success_rate: float = 100.0,
        on_remove: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(master, fg_color="#34495e", **kwargs)
        
        self.on_remove = on_remove
        
        self._status_colors = {
            "idle": "#95a5a6",
            "working": "#3498db",
            "waiting": "#f39c12",
            "error": "#e74c3c",
        }
        
        self._role_icons = {
            "main": "👑",
            "researcher": "🔍",
            "coder": "💻",
            "writer": "✍️",
            "reviewer": "✅",
            "custom": "🤖",
        }
        
        self._create_widgets(name, role, status, tasks_completed, success_rate)
    
    def _create_widgets(self, name: str, role: str, status: str, 
                       tasks_completed: int, success_rate: float):
        """Создание виджетов карточки."""
        # Заголовок
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=10)
        
        # Иконка роли
        icon = self._role_icons.get(role.lower(), "🤖")
        icon_label = ctk.CTkLabel(
            header_frame,
            text=icon,
            font=ctk.CTkFont(size=24)
        )
        icon_label.pack(side="left")
        
        # Информация об агенте
        info_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        info_frame.pack(side="left", padx=(10, 0))
        
        name_label = ctk.CTkLabel(
            info_frame,
            text=name,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ecf0f1"
        )
        name_label.pack(anchor="w")
        
        role_label = ctk.CTkLabel(
            info_frame,
            text=role,
            font=ctk.CTkFont(size=11),
            text_color="#7f8c8d"
        )
        role_label.pack(anchor="w")
        
        # Статус
        status_color = self._status_colors.get(status.lower(), "#95a5a6")
        status_label = ctk.CTkLabel(
            header_frame,
            text="●",
            font=ctk.CTkFont(size=14),
            text_color=status_color
        )
        status_label.pack(side="right")
        
        # Статистика
        stats_frame = ctk.CTkFrame(self, fg_color="#2c3e50")
        stats_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        stats_label = ctk.CTkLabel(
            stats_frame,
            text=f"Задач: {tasks_completed}  |  Успех: {success_rate:.1f}%",
            font=ctk.CTkFont(size=11),
            text_color="#bdc3c7"
        )
        stats_label.pack(pady=5)
        
        # Кнопка удаления (если не главный агент)
        if name != "Главный агент" and self.on_remove:
            remove_btn = ctk.CTkButton(
                self,
                text="Удалить",
                width=80,
                height=25,
                fg_color="#e74c3c",
                hover_color="#c0392b",
                command=self.on_remove,
                font=ctk.CTkFont(size=11)
            )
            remove_btn.pack(anchor="e", padx=10, pady=(0, 10))


class ProgressBar(ctk.CTkFrame):
    """Прогресс бар с текстом."""
    
    def __init__(
        self,
        master,
        label: str = "",
        width: int = 300,
        height: int = 40,
        **kwargs
    ):
        super().__init__(master, width=width, height=height, **kwargs)
        self.pack_propagate(False)
        
        # Метка
        self.label = ctk.CTkLabel(
            self,
            text=label,
            font=ctk.CTkFont(size=12),
            text_color="#ecf0f1"
        )
        self.label.pack(anchor="w", padx=5, pady=(5, 0))
        
        # Прогресс бар
        self.progressbar = ctk.CTkProgressBar(
            self,
            width=width - 10,
            mode="determinate"
        )
        self.progressbar.pack(padx=5, pady=(0, 5))
        self.progressbar.set(0)
    
    def set_progress(self, value: float, label: Optional[str] = None):
        """Установка прогресса (0.0 - 1.0)."""
        self.progressbar.set(value)
        if label:
            self.label.configure(text=label)


class InfoPanel(ctk.CTkScrollableFrame):
    """Панель информации с возможностью прокрутки."""
    
    def __init__(
        self,
        master,
        title: str = "",
        width: int = 400,
        height: int = 300,
        **kwargs
    ):
        super().__init__(master, width=width, height=height, **kwargs)
        
        # Заголовок
        if title:
            title_label = ctk.CTkLabel(
                self,
                text=title,
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color="#ecf0f1"
            )
            title_label.pack(anchor="w", pady=(0, 10))
        
        self._content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._content_frame.pack(fill="both", expand=True)
    
    def add_text(self, text: str, font_size: int = 12, color: str = "#bdc3c7"):
        """Добавление текста."""
        label = ctk.CTkLabel(
            self._content_frame,
            text=text,
            font=ctk.CTkFont(size=font_size),
            text_color=color,
            wraplength=self.winfo_width() - 20,
            justify="left"
        )
        label.pack(anchor="w", pady=2)
        return label
    
    def add_code(self, code: str, language: str = ""):
        """Добавление блока кода."""
        frame = ctk.CTkFrame(self._content_frame, fg_color="#1e1e1e")
        frame.pack(fill="x", pady=5)
        
        if language:
            lang_label = ctk.CTkLabel(
                frame,
                text=language,
                font=ctk.CTkFont(size=10),
                text_color="#7f8c8d"
            )
            lang_label.pack(anchor="w", padx=5, pady=(5, 0))
        
        code_label = ctk.CTkLabel(
            frame,
            text=code,
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color="#ecf0f1",
            wraplength=self.winfo_width() - 40,
            justify="left"
        )
        code_label.pack(anchor="w", padx=5, pady=(0, 5))
        return code_label
    
    def clear(self):
        """Очистка содержимого."""
        for widget in self._content_frame.winfo_children():
            widget.destroy()

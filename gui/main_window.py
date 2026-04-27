"""
Главное окно DeepAgents GUI
Реальный интерфейс с менеджерами инструментов и агентов
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import threading
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import json
import sys
import os

# Добавляем корень проекта в path
sys.path.insert(0, str(Path(__file__).parent.parent))

from gui.tool_manager import ToolManager, ToolRiskLevel
from gui.agent_manager import AgentManager, AgentStatus, AgentRole, AgentTask
from gui.components import StatusIndicator, ToolCard, AgentCard, ProgressBar, InfoPanel

# Импортируем реальные инструменты из core
try:
    from core.tools.filesystem import FileSystemTools
    from core.tools.console_command import ConsoleCommandTools
    from core.tools.websearch import WebSearchTools
    from core.tools.math import MathTools
    from core.tools.python_tools import PythonTools
    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False
    FileSystemTools = None
    ConsoleCommandTools = None
    WebSearchTools = None
    MathTools = None
    PythonTools = None

logger = logging.getLogger(__name__)


class DeepAgentsMainWindow(ctk.CTk):
    """
    Главное окно приложения DeepAgents.
    
    Архитектура интерфейса:
    - Верхняя панель: статус подключения, настройки
    - Левая панель: навигация (Чат, Инструменты, Агенты, Логи)
    - Центральная область: контент выбранной вкладки
    - Правая панель: статистика, быстрые действия
    """
    
    def __init__(self):
        super().__init__()
        
        # Настройки окна
        self.title("DeepAgents GUI v2.0")
        self.geometry("1400x900")
        self.minsize(1200, 700)
        
        # Менеджеры
        self.tool_manager = ToolManager()
        self.agent_manager = AgentManager()
        
        # Инициализация реальных инструментов
        self._init_core_tools()
        
        # Состояние приложения
        self.current_view = "chat"
        self.is_connected = False
        self.settings: Dict[str, Any] = {}
        self.message_history: List[Dict[str, Any]] = []
        self.current_task: Optional[AgentTask] = None
        
        # Настройка стиля
        self._setup_styles()
        
        # Создание интерфейса
        self._create_layout()
        self._create_sidebar()
        self._create_header()
        self._create_main_area()
        self._create_statusbar()
        
        # Загрузка настроек
        self._load_settings()
        
        # Обновление UI
        self._update_view()
    
    def _init_core_tools(self):
        """Инициализация реальных инструментов из core."""
        if not CORE_AVAILABLE:
            logger.warning("Модули core не доступны, работаем в демо-режиме")
            return
        
        try:
            # Регистрируем экземпляры инструментов
            if FileSystemTools:
                fs_tools = FileSystemTools()
                self.tool_manager.set_tool_instance("read_file", fs_tools)
                self.tool_manager.set_tool_instance("write_file", fs_tools)
                self.tool_manager.set_tool_instance("list_directory", fs_tools)
            
            if ConsoleCommandTools:
                console_tools = ConsoleCommandTools()
                self.tool_manager.set_tool_instance("execute_command", console_tools)
            
            if WebSearchTools:
                web_tools = WebSearchTools()
                self.tool_manager.set_tool_instance("web_search", web_tools)
            
            if MathTools:
                math_tools = MathTools()
                self.tool_manager.set_tool_instance("calculate", math_tools)
            
            if PythonTools:
                py_tools = PythonTools()
                self.tool_manager.set_tool_instance("python_exec", py_tools)
                self.tool_manager.set_tool_instance("pip_install", py_tools)
            
            logger.info("Инструменты core успешно инициализированы")
        except Exception as e:
            logger.error(f"Ошибка инициализации инструментов: {e}")
    
    def _setup_styles(self):
        """Настройка стилей приложения."""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Цветовая схема
        self.colors = {
            "bg_primary": "#1a1a2e",
            "bg_secondary": "#16213e",
            "bg_card": "#0f3460",
            "accent": "#e94560",
            "text_primary": "#ecf0f1",
            "text_secondary": "#95a5a6",
            "success": "#2ecc71",
            "warning": "#f39c12",
            "error": "#e74c3c",
        }
        
        # Применяем цвета к окну
        self.configure(fg_color=self.colors["bg_primary"])
    
    def _create_layout(self):
        """Создание основной разметки."""
        # Grid конфигурация
        self.grid_columnconfigure(0, weight=0)  # Sidebar
        self.grid_columnconfigure(1, weight=1)  # Main area
        self.grid_columnconfigure(2, weight=0)  # Right panel
        self.grid_rowconfigure(0, weight=0)     # Header
        self.grid_rowconfigure(1, weight=1)     # Content
        self.grid_rowconfigure(2, weight=0)     # Statusbar
        
        # Фрейм для header (на всю ширину)
        self.header_frame = ctk.CTkFrame(
            self,
            fg_color=self.colors["bg_secondary"],
            height=60
        )
        self.header_frame.grid(row=0, column=0, columnspan=3, sticky="ew")
        self.header_frame.grid_propagate(False)
        
        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(
            self,
            fg_color=self.colors["bg_secondary"],
            width=200
        )
        self.sidebar_frame.grid(row=1, column=0, sticky="ns")
        self.sidebar_frame.grid_propagate(False)
        
        # Основная область
        self.main_frame = ctk.CTkFrame(
            self,
            fg_color=self.colors["bg_primary"]
        )
        self.main_frame.grid(row=1, column=1, sticky="nsew")
        
        # Правая панель
        self.right_frame = ctk.CTkFrame(
            self,
            fg_color=self.colors["bg_secondary"],
            width=280
        )
        self.right_frame.grid(row=1, column=2, sticky="ns")
        self.right_frame.grid_propagate(False)
        
        # Statusbar
        self.statusbar_frame = ctk.CTkFrame(
            self,
            fg_color=self.colors["bg_secondary"],
            height=30
        )
        self.statusbar_frame.grid(row=2, column=0, columnspan=3, sticky="ew")
        self.statusbar_frame.grid_propagate(False)
    
    def _create_header(self):
        """Создание верхней панели."""
        # Логотип/название
        title_label = ctk.CTkLabel(
            self.header_frame,
            text="🤖 DeepAgents",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        title_label.pack(side="left", padx=20, pady=15)
        
        # Статус подключения
        self.connection_status = StatusIndicator(
            self.header_frame,
            text="Отключено",
            status="error",
            width=150
        )
        self.connection_status.pack(side="left", padx=20)
        
        # Кнопки справа
        btn_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        btn_frame.pack(side="right", padx=20)
        
        # Кнопка настроек
        settings_btn = ctk.CTkButton(
            btn_frame,
            text="⚙️ Настройки",
            command=self._open_settings,
            width=120,
            height=35
        )
        settings_btn.pack(side="left", padx=5)
        
        # Кнопка помощи
        help_btn = ctk.CTkButton(
            btn_frame,
            text="❓ Помощь",
            command=self._show_help,
            width=100,
            height=35,
            fg_color="transparent",
            border_width=1
        )
        help_btn.pack(side="left", padx=5)
    
    def _create_sidebar(self):
        """Создание боковой панели навигации."""
        # Заголовок
        nav_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="НАВИГАЦИЯ",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["text_secondary"]
        )
        nav_label.pack(pady=(20, 10))
        
        # Кнопки навигации
        nav_buttons = [
            ("💬 Чат", "chat"),
            ("🔧 Инструменты", "tools"),
            ("🤖 Агенты", "agents"),
            ("📊 Статистика", "stats"),
            ("📝 Логи", "logs"),
        ]
        
        for text, view_id in nav_buttons:
            btn = ctk.CTkButton(
                self.sidebar_frame,
                text=text,
                command=lambda v=view_id: self._switch_view(v),
                anchor="w",
                height=45,
                fg_color="transparent",
                hover_color=self.colors["bg_card"]
            )
            btn.pack(fill="x", padx=10, pady=2)
            
            # Сохраняем ссылку на кнопку для подсветки активной
            if not hasattr(self, "_nav_buttons"):
                self._nav_buttons = {}
            self._nav_buttons[view_id] = btn
        
        # Разделитель
        separator = ctk.CTkFrame(
            self.sidebar_frame,
            height=2,
            fg_color=self.colors["text_secondary"]
        )
        separator.pack(fill="x", padx=10, pady=20)
        
        # Быстрые действия
        action_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="БЫСТРЫЕ ДЕЙСТВИЯ",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["text_secondary"]
        )
        action_label.pack(pady=(0, 10))
        
        # Кнопка подключения
        self.connect_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="🔌 Подключить LM Studio",
            command=self._toggle_connection,
            height=40,
            fg_color=self.colors["success"]
        )
        self.connect_btn.pack(fill="x", padx=10, pady=5)
        
        # Кнопка очистки
        clear_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="🗑️ Очистить чат",
            command=self._clear_chat,
            height=35,
            fg_color="transparent",
            border_width=1
        )
        clear_btn.pack(fill="x", padx=10, pady=5)
    
    def _create_main_area(self):
        """Создание основной области контента."""
        # Контейнер для видов
        self.view_container = ctk.CTkFrame(
            self.main_frame,
            fg_color="transparent"
        )
        self.view_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Создаем представления
        self._create_chat_view()
        self._create_tools_view()
        self._create_agents_view()
        self._create_stats_view()
        self._create_logs_view()
    
    def _create_chat_view(self):
        """Создание представления чата."""
        self.chat_view = ctk.CTkFrame(self.view_container, fg_color="transparent")
        
        # Область сообщений
        messages_frame = ctk.CTkScrollableFrame(
            self.chat_view,
            fg_color=self.colors["bg_secondary"]
        )
        messages_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        self.messages_container = ctk.CTkFrame(
            messages_frame,
            fg_color="transparent"
        )
        self.messages_container.pack(fill="both", expand=True)
        
        # Поле ввода
        input_frame = ctk.CTkFrame(self.chat_view, fg_color="transparent")
        input_frame.pack(fill="x")
        
        self.chat_input = ctk.CTkTextbox(
            input_frame,
            height=80,
            font=ctk.CTkFont(size=13)
        )
        self.chat_input.pack(fill="x", side="left", padx=(0, 10))
        
        send_btn = ctk.CTkButton(
            input_frame,
            text="➤ Отправить",
            command=self._send_message,
            width=120,
            height=80
        )
        send_btn.pack(side="right")
        
        # Прикрепление файла
        attach_btn = ctk.CTkButton(
            input_frame,
            text="📎",
            width=40,
            height=80,
            fg_color="transparent",
            border_width=1
        )
        attach_btn.pack(side="right", padx=(0, 10))
    
    def _create_tools_view(self):
        """Создание представления инструментов."""
        self.tools_view = ctk.CTkFrame(self.view_container, fg_color="transparent")
        
        # Заголовок
        header = ctk.CTkLabel(
            self.tools_view,
            text="Управление инструментами",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        header.pack(anchor="w", pady=(0, 10))
        
        desc = ctk.CTkLabel(
            self.tools_view,
            text="Включайте и отключайте инструменты для управления возможностями агентов",
            font=ctk.CTkFont(size=13),
            text_color=self.colors["text_secondary"]
        )
        desc.pack(anchor="w", pady=(0, 20))
        
        # Контейнер для карточек инструментов
        self.tools_container = ctk.CTkScrollableFrame(
            self.tools_view,
            fg_color="transparent"
        )
        self.tools_container.pack(fill="both", expand=True)
        
        # Заполняем карточками
        self._refresh_tools_cards()
    
    def _create_agents_view(self):
        """Создание представления агентов."""
        self.agents_view = ctk.CTkFrame(self.view_container, fg_color="transparent")
        
        # Заголовок с кнопкой добавления
        header_frame = ctk.CTkFrame(self.agents_view, fg_color="transparent")
        header_frame.pack(fill="x")
        
        header = ctk.CTkLabel(
            header_frame,
            text="Менеджер агентов",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        header.pack(side="left")
        
        add_agent_btn = ctk.CTkButton(
            header_frame,
            text="+ Добавить агента",
            command=self._add_agent,
            height=35
        )
        add_agent_btn.pack(side="right")
        
        # Контейнер для карточек агентов
        self.agents_container = ctk.CTkScrollableFrame(
            self.agents_view,
            fg_color="transparent"
        )
        self.agents_container.pack(fill="both", expand=True, pady=20)
        
        # Заполняем карточками
        self._refresh_agents_cards()
    
    def _create_stats_view(self):
        """Создание представления статистики."""
        self.stats_view = ctk.CTkFrame(self.view_container, fg_color="transparent")
        
        # Заголовок
        header = ctk.CTkLabel(
            self.stats_view,
            text="Статистика системы",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        header.pack(anchor="w", pady=(0, 20))
        
        # Карточки статистики
        stats_grid = ctk.CTkFrame(self.stats_view, fg_color="transparent")
        stats_grid.pack(fill="both", expand=True)
        
        # Создаем карточки статистики
        self.stats_cards = {}
        stats_data = [
            ("Агентов", "0", "🤖"),
            ("Активных задач", "0", "📋"),
            ("Успешность", "100%", "✅"),
            ("Инструментов", "0", "🔧"),
        ]
        
        for i, (title, value, icon) in enumerate(stats_data):
            card = ctk.CTkFrame(stats_grid, fg_color=self.colors["bg_card"])
            card.grid(row=i//2, column=i%2, padx=10, pady=10, sticky="nsew")
            
            stats_grid.grid_columnconfigure(i%2, weight=1)
            stats_grid.grid_rowconfigure(i//2, weight=1)
            
            icon_label = ctk.CTkLabel(
                card,
                text=icon,
                font=ctk.CTkFont(size=30)
            )
            icon_label.pack(pady=(15, 5))
            
            value_label = ctk.CTkLabel(
                card,
                text=value,
                font=ctk.CTkFont(size=28, weight="bold"),
                text_color=self.colors["text_primary"]
            )
            value_label.pack()
            
            title_label = ctk.CTkLabel(
                card,
                text=title,
                font=ctk.CTkFont(size=14),
                text_color=self.colors["text_secondary"]
            )
            title_label.pack(pady=(0, 15))
            
            self.stats_cards[title] = value_label
    
    def _create_logs_view(self):
        """Создание представления логов."""
        self.logs_view = ctk.CTkFrame(self.view_container, fg_color="transparent")
        
        # Заголовок
        header = ctk.CTkLabel(
            self.logs_view,
            text="Системные логи",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        header.pack(anchor="w", pady=(0, 10))
        
        # Панель логов
        self.logs_panel = InfoPanel(
            self.logs_view,
            width=800,
            height=500
        )
        self.logs_panel.pack(fill="both", expand=True)
        
        # Кнопки управления
        btn_frame = ctk.CTkFrame(self.logs_view, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        
        refresh_btn = ctk.CTkButton(
            btn_frame,
            text="🔄 Обновить",
            command=self._refresh_logs,
            width=120
        )
        refresh_btn.pack(side="left", padx=5)
        
        clear_btn = ctk.CTkButton(
            btn_frame,
            text="🗑️ Очистить",
            command=self._clear_logs,
            width=120,
            fg_color="transparent",
            border_width=1
        )
        clear_btn.pack(side="left", padx=5)
        
        export_btn = ctk.CTkButton(
            btn_frame,
            text="💾 Экспорт",
            command=self._export_logs,
            width=120,
            fg_color="transparent",
            border_width=1
        )
        export_btn.pack(side="left", padx=5)
    
    def _create_statusbar(self):
        """Создание строки состояния."""
        # Статус слева
        self.status_label = ctk.CTkLabel(
            self.statusbar_frame,
            text="Готов",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_secondary"]
        )
        self.status_label.pack(side="left", padx=20)
        
        # Информация справа
        info_label = ctk.CTkLabel(
            self.statusbar_frame,
            text="DeepAgents v2.0 | Python 3.x",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_secondary"]
        )
        info_label.pack(side="right", padx=20)
    
    # Методы переключения видов
    
    def _switch_view(self, view_id: str):
        """Переключение между представлениями."""
        self.current_view = view_id
        
        # Скрываем все виды
        for view in [self.chat_view, self.tools_view, self.agents_view, 
                     self.stats_view, self.logs_view]:
            view.pack_forget()
        
        # Показываем выбранный
        view_map = {
            "chat": self.chat_view,
            "tools": self.tools_view,
            "agents": self.agents_view,
            "stats": self.stats_view,
            "logs": self.logs_view,
        }
        
        if view_id in view_map:
            view_map[view_id].pack(fill="both", expand=True)
        
        # Обновляем подсветку кнопок
        for vid, btn in self._nav_buttons.items():
            if vid == view_id:
                btn.configure(fg_color=self.colors["bg_card"])
            else:
                btn.configure(fg_color="transparent")
        
        # Обновляем контент если нужно
        if view_id == "tools":
            self._refresh_tools_cards()
        elif view_id == "agents":
            self._refresh_agents_cards()
        elif view_id == "stats":
            self._update_stats()
    
    def _update_view(self):
        """Обновление текущего представления."""
        self._switch_view(self.current_view)
    
    # Методы обновления UI
    
    def _refresh_tools_cards(self):
        """Обновление карточек инструментов."""
        # Очищаем контейнер
        for widget in self.tools_container.winfo_children():
            widget.destroy()
        
        # Создаем карточки
        tools = self.tool_manager.get_all_tools()
        categories = self.tool_manager.get_categories()
        
        for category in categories:
            # Заголовок категории
            cat_label = ctk.CTkLabel(
                self.tools_container,
                text=category.upper(),
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=self.colors["text_secondary"]
            )
            cat_label.pack(anchor="w", pady=(15, 10))
            
            # Карточки инструментов категории
            for tool in self.tool_manager.get_tools_by_category(category):
                card = ToolCard(
                    self.tools_container,
                    name=tool.name,
                    description=tool.description,
                    icon=tool.icon,
                    enabled=tool.enabled,
                    risk_level=tool.risk_level.value,
                    on_toggle=lambda enabled, name=tool.name: self._on_tool_toggle(name, enabled)
                )
                card.pack(fill="x", pady=5)
    
    def _refresh_agents_cards(self):
        """Обновление карточек агентов."""
        # Очищаем контейнер
        for widget in self.agents_container.winfo_children():
            widget.destroy()
        
        # Создаем карточки
        agents = self.agent_manager.get_all_agents()
        
        for agent in agents:
            card = AgentCard(
                self.agents_container,
                name=agent.name,
                role=agent.role.value,
                status=agent.status.value,
                tasks_completed=agent.tasks_completed,
                success_rate=agent.success_rate,
                on_remove=None if agent.id == "main-agent" else lambda aid=agent.id: self._remove_agent(aid)
            )
            card.pack(fill="x", pady=5)
    
    def _update_stats(self):
        """Обновление статистики."""
        stats = self.agent_manager.get_statistics()
        
        if "Агентов" in self.stats_cards:
            self.stats_cards["Агентов"].configure(text=str(stats["total_agents"]))
        if "Активных задач" in self.stats_cards:
            self.stats_cards["Активных задач"].configure(text=str(stats["total_tasks"]))
        if "Успешность" in self.stats_cards:
            self.stats_cards["Успешность"].configure(text=f"{stats['success_rate']:.1f}%")
        
        tools_count = len(self.tool_manager.get_enabled_tools())
        if "Инструментов" in self.stats_cards:
            self.stats_cards["Инструментов"].configure(text=str(tools_count))
    
    # Обработчики событий
    
    def _on_tool_toggle(self, tool_name: str, enabled: bool):
        """Обработчик переключения инструмента."""
        if enabled:
            self.tool_manager.enable_tool(tool_name)
        else:
            self.tool_manager.disable_tool(tool_name)
        
        self.status_label.configure(text=f"Инструмент '{tool_name}' {'включен' if enabled else 'выключен'}")
        logger.info(f"Инструмент {tool_name}: {'ON' if enabled else 'OFF'}")
    
    def _add_agent(self):
        """Добавление нового агента."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Добавить агента")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()
        
        # Форма
        form_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Имя
        ctk.CTkLabel(
            form_frame,
            text="Имя агента:"
        ).pack(anchor="w", pady=(0, 5))
        
        name_entry = ctk.CTkEntry(form_frame, width=350)
        name_entry.pack(fill="x", pady=(0, 15))
        
        # Роль
        ctk.CTkLabel(
            form_frame,
            text="Роль:"
        ).pack(anchor="w", pady=(0, 5))
        
        role_var = ctk.StringVar(value="custom")
        role_menu = ctk.CTkOptionMenu(
            form_frame,
            values=["researcher", "coder", "writer", "reviewer", "custom"],
            variable=role_var,
            width=350
        )
        role_menu.pack(fill="x", pady=(0, 15))
        
        # Описание
        ctk.CTkLabel(
            form_frame,
            text="Описание:"
        ).pack(anchor="w", pady=(0, 5))
        
        desc_entry = ctk.CTkTextbox(form_frame, height=60, width=350)
        desc_entry.pack(fill="x", pady=(0, 15))
        
        # Кнопки
        btn_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        def create_agent():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Ошибка", "Введите имя агента")
                return
            
            role_str = role_var.get()
            role = getattr(AgentRole, role_str.upper(), AgentRole.CUSTOM)
            description = desc_entry.get("1.0", "end").strip()
            
            agent = self.agent_manager.create_agent(
                name=name,
                role=role,
                description=description
            )
            
            if agent:
                self._refresh_agents_cards()
                self._update_stats()
                self.status_label.configure(text=f"Агент '{name}' создан")
                dialog.destroy()
            else:
                messagebox.showerror("Ошибка", "Не удалось создать агента")
        
        ctk.CTkButton(
            btn_frame,
            text="Создать",
            command=create_agent,
            width=100
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Отмена",
            command=dialog.destroy,
            width=100,
            fg_color="transparent",
            border_width=1
        ).pack(side="left", padx=5)
    
    def _remove_agent(self, agent_id: str):
        """Удаление агента."""
        agent = self.agent_manager.get_agent(agent_id)
        if not agent:
            return
        
        if messagebox.askyesno("Подтверждение", f"Удалить агента '{agent.name}'?"):
            if self.agent_manager.remove_agent(agent_id):
                self._refresh_agents_cards()
                self._update_stats()
                self.status_label.configure(text=f"Агент '{agent.name}' удален")
    
    def _toggle_connection(self):
        """Переключение подключения к LM Studio."""
        if self.is_connected:
            self.is_connected = False
            self.connect_btn.configure(
                text="🔌 Подключить LM Studio",
                fg_color=self.colors["success"]
            )
            self.connection_status.set_status("error", "Отключено")
            self.status_label.configure(text="Отключено от LM Studio")
        else:
            # Имитация подключения
            self.connect_btn.configure(text="⏳ Подключение...", fg_color="#f39c12")
            self.after(1000, self._complete_connection)
    
    def _complete_connection(self):
        """Завершение подключения."""
        self.is_connected = True
        self.connect_btn.configure(
            text="✅ Подключено",
            fg_color=self.colors["success"]
        )
        self.connection_status.set_status("success", "LM Studio")
        self.status_label.configure(text="Подключено к LM Studio (localhost:1234)")
    
    def _send_message(self):
        """Отправка сообщения агенту."""
        message = self.chat_input.get("1.0", "end").strip()
        if not message:
            return
        
        # Добавляем сообщение пользователя в историю и UI
        self.message_history.append({"role": "user", "content": message})
        self._add_message_to_chat(message, is_user=True)
        self.chat_input.delete("1.0", "end")
        
        # Назначаем задачу главному агенту
        main_agent = self.agent_manager.get_agent("main-agent")
        if main_agent and self.is_connected:
            task = self.agent_manager.assign_task(
                agent_id="main-agent",
                description=message
            )
            if task:
                self.current_task = task
                self.status_label.configure(text="Агент обрабатывает запрос...")
                # Запускаем обработку в отдельном потоке
                threading.Thread(target=self._process_message, args=(message,), daemon=True).start()
        else:
            # Демонстрационный режим без подключения
            self.status_label.configure(text="Агент печатает...")
            self.after(1000, lambda: self._add_message_to_chat(
                "[Демо-режим] Подключите LM Studio для реальной работы.\n\n"
                f"Получено: {message}\n\n"
                "Доступные инструменты:\n"
                f"- Включено: {len(self.tool_manager.get_enabled_tools())}\n"
                f"- Агентов: {len(self.agent_manager.get_all_agents())}",
                is_user=False
            ))
    
    def _process_message(self, message: str):
        """Обработка сообщения в фоне (интеграция с core)."""
        try:
            # Здесь будет вызов реального API LM Studio через core
            # Пока имитируем работу
            
            # Получаем активные инструменты
            enabled_tools = self.tool_manager.get_enabled_tools()
            
            # Имитация задержки обработки
            import time
            time.sleep(2)
            
            # Формируем ответ
            response = f"Запрос обработан.\n\n"
            response += f"Использовано инструментов: {len(enabled_tools)}\n"
            response += f"Время выполнения: 2.0с\n\n"
            response += f"Текст запроса: {message[:200]}{'...' if len(message) > 200 else ''}"
            
            # Обновляем UI в главном потоке
            self.after(0, lambda: self._add_message_to_chat(response, is_user=False))
            self.after(0, lambda: self.status_label.configure(text="Готов"))
            
            # Завершаем задачу
            if self.current_task:
                self.agent_manager.complete_task(
                    task_id=self.current_task.id,
                    result=response,
                    success=True
                )
                self.current_task = None
                
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            self.after(0, lambda: self._add_message_to_chat(
                f"Ошибка: {str(e)}",
                is_user=False
            ))
            self.after(0, lambda: self.status_label.configure(text="Ошибка"))
    
    def _add_message_to_chat(self, text: str, is_user: bool = False):
        """Добавление сообщения в чат."""
        msg_frame = ctk.CTkFrame(
            self.messages_container,
            fg_color=self.colors["bg_card"] if not is_user else "#2980b9"
        )
        msg_frame.pack(fill="x", pady=5, padx=10)
        
        # Метка с именем и временем
        header_frame = ctk.CTkFrame(msg_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(5, 0))
        
        name_label = ctk.CTkLabel(
            header_frame,
            text="Вы" if is_user else "🤖 Агент",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["text_secondary"]
        )
        name_label.pack(side="left")
        
        # Время
        from datetime import datetime
        time_str = datetime.now().strftime("%H:%M")
        time_label = ctk.CTkLabel(
            header_frame,
            text=time_str,
            font=ctk.CTkFont(size=10),
            text_color=self.colors["text_secondary"]
        )
        time_label.pack(side="right")
        
        # Текст сообщения (с поддержкой переноса строк)
        text_label = ctk.CTkLabel(
            msg_frame,
            text=text,
            font=ctk.CTkFont(size=13),
            text_color=self.colors["text_primary"],
            wraplength=700,
            justify="left"
        )
        text_label.pack(anchor="w", padx=10, pady=(0, 10))
        
        # Прокрутка вниз
        self.messages_container.update_idletasks()
    
    def _clear_chat(self):
        """Очистка чата и истории."""
        for widget in self.messages_container.winfo_children():
            widget.destroy()
        self.message_history.clear()
        self.status_label.configure(text="Чат очищен")
        logger.info("Чат очищен")
    
    def _open_settings(self):
        """Открытие диалога настроек."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Настройки")
        dialog.geometry("500x400")
        dialog.transient(self)
        dialog.grab_set()
        
        # Заголовок
        title = ctk.CTkLabel(
            dialog,
            text="⚙️ Настройки DeepAgents",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(pady=20)
        
        # Форма настроек
        form_frame = ctk.CTkScrollableFrame(dialog, width=450, height=280)
        form_frame.pack(fill="both", expand=True, padx=20)
        
        # URL LM Studio
        ctk.CTkLabel(
            form_frame,
            text="LM Studio URL:",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", pady=(10, 5))
        
        url_entry = ctk.CTkEntry(form_frame, width=400)
        url_entry.insert(0, self.settings.get("lmstudio_url", "http://localhost:1234"))
        url_entry.pack(fill="x", pady=(0, 15))
        
        # Тема
        ctk.CTkLabel(
            form_frame,
            text="Тема оформления:",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", pady=(10, 5))
        
        theme_var = ctk.StringVar(value=self.settings.get("theme", "dark"))
        theme_menu = ctk.CTkOptionMenu(
            form_frame,
            values=["dark", "light", "system"],
            variable=theme_var,
            width=400
        )
        theme_menu.pack(fill="x", pady=(0, 15))
        
        # Авто-подключение
        auto_connect_var = ctk.BooleanVar(
            value=self.settings.get("auto_connect", False)
        )
        auto_connect_cb = ctk.CTkCheckBox(
            form_frame,
            text="Автоматическое подключение при запуске",
            variable=auto_connect_var
        )
        auto_connect_cb.pack(anchor="w", pady=(0, 15))
        
        # Логирование
        logging_var = ctk.BooleanVar(
            value=self.settings.get("enable_logging", True)
        )
        logging_cb = ctk.CTkCheckBox(
            form_frame,
            text="Включить логирование",
            variable=logging_var
        )
        logging_cb.pack(anchor="w", pady=(0, 15))
        
        # Кнопки
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        def save_settings():
            self.settings["lmstudio_url"] = url_entry.get().strip()
            self.settings["theme"] = theme_var.get()
            self.settings["auto_connect"] = auto_connect_var.get()
            self.settings["enable_logging"] = logging_var.get()
            
            self._save_settings()
            
            # Применяем тему
            ctk.set_appearance_mode(theme_var.get())
            
            self.status_label.configure(text="Настройки сохранены")
            dialog.destroy()
        
        ctk.CTkButton(
            btn_frame,
            text="Сохранить",
            command=save_settings,
            width=120
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="Отмена",
            command=dialog.destroy,
            width=120,
            fg_color="transparent",
            border_width=1
        ).pack(side="left", padx=10)
    
    def _show_help(self):
        """Показать справку."""
        help_window = ctk.CTkToplevel(self)
        help_window.title("Помощь")
        help_window.geometry("600x500")
        help_window.transient(self)
        
        # Заголовок
        title = ctk.CTkLabel(
            help_window,
            text="❓ Справка DeepAgents GUI v2.0",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(pady=20)
        
        # Контент
        content_frame = ctk.CTkScrollableFrame(help_window, width=550, height=350)
        content_frame.pack(fill="both", expand=True, padx=20)
        
        sections = [
            ("🚀 Быстрый старт", """
1. Запустите LM Studio и загрузите модель
2. Включите сервер на localhost:1234
3. Нажмите «Подключить LM Studio» в приложении
4. Выберите нужные инструменты
5. Отправьте запрос в чат
"""),
            ("🔧 Инструменты", """
• Файловая система: чтение/запись файлов, просмотр директорий
• Консоль: выполнение системных команд
• Веб-поиск: поиск информации в интернете
• Математика: вычисления и формулы
• Python: выполнение кода и установка пакетов

Уровень риска инструментов обозначается цветом:
🟢 Безопасные | 🟡 Требуют проверки | 🔴 Опасные
"""),
            ("🤖 Агенты", """
Вы можете создать до 10 суб-агентов с ролями:
• 👑 Главный агент (создается автоматически)
• 🔍 Исследователь (поиск информации)
• 💻 Программист (написание кода)
• ✍️ Писатель (тексты и документы)
• ✅ Ревьювер (проверка качества)
• 🤖 Пользовательская роль
"""),
            ("⌨️ Горячие клавиши", """
• Ctrl+Enter: Отправить сообщение
• Ctrl+L: Очистить чат
• Ctrl+T: Переключить вкладку инструментов
• Ctrl+A: Переключить вкладку агентов
"""),
        ]
        
        for title_text, content in sections:
            ctk.CTkLabel(
                content_frame,
                text=title_text,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#e94560"
            ).pack(anchor="w", pady=(15, 5))
            
            ctk.CTkLabel(
                content_frame,
                text=content.strip(),
                font=ctk.CTkFont(size=12),
                text_color="#bdc3c7",
                wraplength=520,
                justify="left"
            ).pack(anchor="w", pady=(0, 10))
        
        # Кнопка закрытия
        ctk.CTkButton(
            help_window,
            text="Закрыть",
            command=help_window.destroy,
            width=120
        ).pack(pady=20)
    
    def _refresh_logs(self):
        """Обновление логов."""
        self.logs_panel.clear()
        self.logs_panel.add_text("Логи загружены", font_size=14)
        self.logs_panel.add_text("-" * 50)
        self.logs_panel.add_text("Система готова к работе")
    
    def _clear_logs(self):
        """Очистка логов."""
        self.logs_panel.clear()
        self.status_label.configure(text="Логи очищены")
    
    def _export_logs(self):
        """Экспорт логов."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("DeepAgents Logs\n")
                    f.write("=" * 50 + "\n")
                self.status_label.configure(text=f"Логи экспортированы: {filename}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось экспортировать логи: {e}")
    
    # Управление настройками
    
    def _load_settings(self):
        """Загрузка настроек."""
        settings_file = Path("gui_settings.json")
        if settings_file.exists():
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
                logger.info("Настройки загружены")
            except Exception as e:
                logger.error(f"Ошибка загрузки настроек: {e}")
                self.settings = {}
        else:
            self.settings = {
                "lmstudio_url": "http://localhost:1234",
                "theme": "dark",
                "language": "ru",
            }
    
    def _save_settings(self):
        """Сохранение настроек."""
        settings_file = Path("gui_settings.json")
        try:
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            logger.info("Настройки сохранены")
        except Exception as e:
            logger.error(f"Ошибка сохранения настроек: {e}")
    
    def destroy(self):
        """Закрытие приложения."""
        self._save_settings()
        super().destroy()


# Точка входа
if __name__ == "__main__":
    app = DeepAgentsMainWindow()
    app.mainloop()

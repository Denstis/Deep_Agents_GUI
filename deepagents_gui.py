#!/usr/bin/env python3
"""
DeepAgents GUI - A full-featured customtkinter GUI for DeepAgents using LM Studio server.

This application provides a complete graphical interface for interacting with DeepAgents
using only LM Studio server and local models. No external API keys required.

Features:
- Chat interface with streaming responses
- Tool execution visualization
- Sub-agent management
- File system operations
- Configurable LM Studio connection
- Thread/conversation management
- Real-time status updates
- Todo list tracking
- Memory management
- Web search capabilities
- Calculator and math tools
- Debug logging
"""

import asyncio
import json
import os
import sys
import threading
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional
from functools import wraps

import customtkinter as ctk
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool, tool
import httpx

# Import modular components
from core.utils import LMStudioClient
from core.tools import SimpleFilesystemTools, get_execute_command_tool, WebSearchTools, MathTools
from core.gui import ChatWindow, MessageBubble

# Note: Old message_bubble.py module replaced by core.gui package
# from message_bubble import MessageBubble, calculate_text_height  # DEPRECATED

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deepagents_gui.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Try to import additional tools
try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
    logger.info("DuckDuckGo search available")
except ImportError:
    DDGS_AVAILABLE = False
    logger.warning("DuckDuckGo search not available - install with: pip install duckduckgo-search")

try:
    from sympy import symbols, Eq, solve, sympify
    SYMPY_AVAILABLE = True
    logger.info("SymPy math solver available")
except ImportError:
    SYMPY_AVAILABLE = False
    logger.warning("SymPy not available - install with: pip install sympy")

try:
    from PIL import Image
    PIL_AVAILABLE = True
    logger.info("Pillow image processing available")
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("Pillow not available - install with: pip install Pillow")

# Configure customtkinter appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# Try to import deepagents if available
try:
    from core import create_deep_agent
    DEEPAGENTS_AVAILABLE = True
    logger.info("DeepAgents package loaded successfully")
except ImportError:
    DEEPAGENTS_AVAILABLE = False
    logger.warning("DeepAgents package not installed. Using basic LangGraph agent.")


# Remove duplicate class definitions - now imported from deepagents package
# LMStudioClient, SimpleFilesystemTools, WebSearchTools, MathTools are imported above


class ImageTools:
    """Image processing tools using Pillow."""
    
    @staticmethod
    @tool
    def get_image_info(image_path: str) -> str:
        """Get information about an image file.
        
        Args:
            image_path: Path to the image file.
            
        Returns:
            Image metadata including format, size, mode, etc.
        """
        if not PIL_AVAILABLE:
            logger.warning("Image info requested but Pillow not available")
            return "Error: Image processing is not available. Please install Pillow package."
        
        try:
            logger.info(f"Getting image info: '{image_path}'")
            path = Path(image_path)
            if not path.exists():
                return f"Error: Image file '{image_path}' does not exist."
            
            with Image.open(path) as img:
                info = {
                    "format": img.format,
                    "mode": img.mode,
                    "size": img.size,
                    "width": img.width,
                    "height": img.height
                }
                result = f"Image info for '{image_path}':\n"
                result += "\n".join(f"  {k}: {v}" for k, v in info.items())
                logger.info(f"Image info retrieved: {info}")
                return result
        except Exception as e:
            logger.error(f"Image info failed: {str(e)}")
            return f"Error getting image info: {str(e)}"


# Note: Filesystem tools are now available via core.tools module
# Import them with: from core.tools import create_filesystem_tools


# Old MessageBubble class has been moved to message_bubble.py module
# The new implementation provides:
# - Full-width messages with proper alignment
# - Dynamic height calculation based on font metrics
# - No hardcoded pixel heights
# - Efficient layout management

class SettingsDialog(ctk.CTkToplevel):
    """Расширенные настройки с управлением инструментами и безопасностью."""
    
    def __init__(self, parent, current_settings: dict, save_callback: Callable):
        super().__init__(parent)
        
        self.title("Настройки DeepAgents")
        self.geometry("900x700")
        self.resizable(True, True)
        self.minsize(700, 500)
        
        self.save_callback = save_callback
        self.current_settings = current_settings.copy()
        
        # Инициализация настроек инструментов
        if "tools_settings" not in self.current_settings:
            self.current_settings["tools_settings"] = {
                "filesystem_enabled": True,
                "websearch_enabled": DDGS_AVAILABLE,
                "math_enabled": SYMPY_AVAILABLE,
                "image_enabled": PIL_AVAILABLE,
                "command_full_access": False,  # По умолчанию ограниченный доступ
                "allowed_commands": ["ls", "dir", "cat", "head", "tail", "pwd", "echo", "find", "grep"],
            }
        
        # Modal behavior
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        """Create settings widgets with tabs."""
        # Создаем систему вкладок
        self.tabview = ctk.CTkTabview(self, width=850, height=600)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Вкладка 1: LM Studio
        self.lmstudio_tab = self.tabview.add("LM Studio")
        self._create_lmstudio_widgets(self.lmstudio_tab)
        
        # Вкладка 2: Инструменты
        self.tools_tab = self.tabview.add("Инструменты")
        self._create_tools_widgets(self.tools_tab)
        
        # Вкладка 3: Безопасность
        self.security_tab = self.tabview.add("Безопасность")
        self._create_security_widgets(self.security_tab)
        
        # Кнопки внизу
        self._create_buttons()
    
    def _create_lmstudio_widgets(self, parent):
        """Виджеты настроек LM Studio."""
        main_frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title = ctk.CTkLabel(
            main_frame,
            text="Настройки LM Studio",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=(0, 20))
        
        # LM Studio URL
        url_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        url_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            url_frame,
            text="LM Studio Server URL:",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w")
        
        self.url_entry = ctk.CTkEntry(
            url_frame,
            width=400,
            placeholder_text="http://localhost:1234"
        )
        self.url_entry.pack(fill="x", pady=5)
        if self.current_settings.get("lmstudio_url", ""):
            self.url_entry.insert(0, self.current_settings.get("lmstudio_url", "http://localhost:1234"))
        
        # Model name
        model_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        model_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            model_frame,
            text="Model Name (опционально):",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w")
        
        self.model_entry = ctk.CTkEntry(
            model_frame,
            width=400,
            placeholder_text="Оставить пустым для значения по умолчанию"
        )
        self.model_entry.pack(fill="x", pady=5)
        if self.current_settings.get("model_name", ""):
            self.model_entry.insert(0, self.current_settings.get("model_name", ""))
        
        # Temperature
        temp_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        temp_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            temp_frame,
            text="Temperature (креативность):",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w")
        
        self.temp_slider = ctk.CTkSlider(
            temp_frame,
            from_=0.0,
            to=2.0,
            number_of_steps=20,
            command=lambda v: self.temp_value.configure(text=f"{v:.2f}")
        )
        self.temp_slider.pack(fill="x", pady=5)
        self.temp_slider.set(self.current_settings.get("temperature", 0.7))
        
        self.temp_value = ctk.CTkLabel(
            temp_frame,
            text=f"{self.current_settings.get('temperature', 0.7):.2f}",
            font=ctk.CTkFont(size=12)
        )
        self.temp_value.pack(anchor="e")
        
        # Max tokens
        tokens_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        tokens_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            tokens_frame,
            text="Max Tokens (лимит ответа):",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w")
        
        self.max_tokens_entry = ctk.CTkEntry(
            tokens_frame,
            width=150,
            placeholder_text="4096"
        )
        self.max_tokens_entry.pack(anchor="w", pady=5)
        if self.current_settings.get("max_tokens"):
            self.max_tokens_entry.insert(0, str(self.current_settings["max_tokens"]))
        
        # Timeout
        timeout_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        timeout_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            timeout_frame,
            text="Timeout (секунды на запрос):",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w")
        
        self.timeout_entry = ctk.CTkEntry(
            timeout_frame,
            width=150,
            placeholder_text="120"
        )
        self.timeout_entry.pack(anchor="w", pady=5)
        if self.current_settings.get("timeout_seconds"):
            self.timeout_entry.insert(0, str(self.current_settings["timeout_seconds"]))
        
        # Retry attempts
        retry_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        retry_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            retry_frame,
            text="Попытки повтора при ошибке:",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w")
        
        self.retry_entry = ctk.CTkEntry(
            retry_frame,
            width=150,
            placeholder_text="3"
        )
        self.retry_entry.pack(anchor="w", pady=5)
        if self.current_settings.get("retry_attempts"):
            self.retry_entry.insert(0, str(self.current_settings["retry_attempts"]))
        
        # Working directory
        workdir_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        workdir_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            workdir_frame,
            text="Рабочая директория:",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w")
        
        workdir_entry_frame = ctk.CTkFrame(workdir_frame, fg_color="transparent")
        workdir_entry_frame.pack(fill="x", pady=5)
        
        self.workdir_entry = ctk.CTkEntry(
            workdir_entry_frame,
            width=320,
            placeholder_text=str(Path.cwd())
        )
        self.workdir_entry.pack(side="left", fill="x", expand=True)
        if self.current_settings.get("working_dir", ""):
            self.workdir_entry.insert(0, self.current_settings.get("working_dir", str(Path.cwd())))
        
        browse_btn = ctk.CTkButton(
            workdir_entry_frame,
            text="Обзор...",
            command=self._browse_workdir,
            width=80
        )
        browse_btn.pack(side="right", padx=(10, 0))
    
    def _create_tools_widgets(self, parent):
        """Виджеты управления инструментами."""
        main_frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        title = ctk.CTkLabel(
            main_frame,
            text="Управление инструментами",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=(0, 20))
        
        desc = ctk.CTkLabel(
            main_frame,
            text="Включайте/выключайте инструменты для контроля возможностей агента",
            font=ctk.CTkFont(size=12),
            text_color="#7f8c8d"
        )
        desc.pack(pady=(0, 20))
        
        tools = self.current_settings.get("tools_settings", {})
        
        # Файловая система
        self._create_tool_toggle(
            main_frame,
            "📁 Файловая система",
            "Чтение/запись файлов, просмотр директорий",
            "filesystem_enabled",
            tools.get("filesystem_enabled", True)
        )
        
        # Веб-поиск
        self._create_tool_toggle(
            main_frame,
            "🌐 Веб-поиск",
            "Поиск информации в интернете через DuckDuckGo",
            "websearch_enabled",
            tools.get("websearch_enabled", DDGS_AVAILABLE),
            disabled=not DDGS_AVAILABLE,
            disabled_text="Требуется пакет duckduckgo-search"
        )
        
        # Математика
        self._create_tool_toggle(
            main_frame,
            "🧮 Математика",
            "Вычисления и решение уравнений через SymPy",
            "math_enabled",
            tools.get("math_enabled", SYMPY_AVAILABLE),
            disabled=not SYMPY_AVAILABLE,
            disabled_text="Требуется пакет sympy"
        )
        
        # Изображения
        self._create_tool_toggle(
            main_frame,
            "🖼️ Обработка изображений",
            "Получение информации об изображениях",
            "image_enabled",
            tools.get("image_enabled", PIL_AVAILABLE),
            disabled=not PIL_AVAILABLE,
            disabled_text="Требуется пакет Pillow"
        )
        
        # Командная строка
        self._create_tool_toggle(
            main_frame,
            "💻 Командная строка",
            "Выполнение системных команд",
            "command_line_enabled",
            tools.get("command_line_enabled", True)
        )
    
    def _create_tool_toggle(self, parent, title, description, setting_key, enabled, disabled=False, disabled_text=""):
        """Создание переключателя инструмента."""
        frame = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        frame.pack(fill="x", pady=5, padx=5)
        
        # Название и описание
        info_frame = ctk.CTkFrame(frame, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=15, pady=10)
        
        ctk.CTkLabel(
            info_frame,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#3498db" if enabled else "#7f8c8d"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            info_frame,
            text=description,
            font=ctk.CTkFont(size=11),
            text_color="#7f8c8d"
        ).pack(anchor="w")
        
        if disabled and disabled_text:
            ctk.CTkLabel(
                info_frame,
                text=f"⚠ {disabled_text}",
                font=ctk.CTkFont(size=10),
                text_color="#e74c3c"
            ).pack(anchor="w", pady=(5, 0))
        
        # Переключатель
        switch_var = ctk.BooleanVar(value=enabled and not disabled)
        setattr(self, f"_{setting_key}_var", switch_var)
        
        switch = ctk.CTkSwitch(
            frame,
            variable=switch_var,
            text="Вкл" if enabled else "Выкл",
            command=lambda v=switch_var, t=title: t.configure(text="Вкл" if v.get() else "Выкл"),
            state="disabled" if disabled else "normal"
        )
        switch.pack(side="right", padx=15, pady=10)
    
    def _create_security_widgets(self, parent):
        """Виджеты настроек безопасности."""
        main_frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        title = ctk.CTkLabel(
            main_frame,
            text="Настройки безопасности",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=(0, 20))
        
        warning = ctk.CTkLabel(
            main_frame,
            text="⚠ ВНИМАНИЕ: Полные права могут быть опасны!\nУбедитесь, что доверяете используемой модели.",
            font=ctk.CTkFont(size=12),
            text_color="#e74c3c",
            justify="left"
        )
        warning.pack(pady=(0, 20), anchor="w")
        
        tools = self.current_settings.get("tools_settings", {})
        
        # Полный доступ к командной строке
        security_frame = ctk.CTkFrame(main_frame, fg_color="#2b2b2b")
        security_frame.pack(fill="x", pady=10, padx=5)
        
        ctk.CTkLabel(
            security_frame,
            text="💻 Полный доступ к командной строке",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#e74c3c"
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        ctk.CTkLabel(
            security_frame,
            text="Разрешить выполнение ЛЮБЫХ команд (включая rm, del, format и т.д.)",
            font=ctk.CTkFont(size=11),
            text_color="#7f8c8d"
        ).pack(anchor="w", padx=15, pady=(0, 10))
        
        self.full_access_var = ctk.BooleanVar(value=tools.get("command_full_access", False))
        self.full_access_switch = ctk.CTkSwitch(
            security_frame,
            variable=self.full_access_var,
            text="Полный доступ" if self.full_access_var.get() else "Ограниченный доступ",
            command=self._toggle_full_access
        )
        self.full_access_switch.pack(side="right", padx=15, pady=10)
        
        # Список разрешённых команд (для ограниченного режима)
        self.allowed_commands_frame = ctk.CTkFrame(main_frame, fg_color="#2b2b2b")
        self.allowed_commands_frame.pack(fill="both", expand=True, pady=10, padx=5)
        
        ctk.CTkLabel(
            self.allowed_commands_frame,
            text="Разрешённые команды (ограниченный режим):",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        ctk.CTkLabel(
            self.allowed_commands_frame,
            text="Введите команды через запятую (например: ls, dir, cat, pwd)",
            font=ctk.CTkFont(size=10),
            text_color="#7f8c8d"
        ).pack(anchor="w", padx=15, pady=(0, 5))
        
        allowed_commands = tools.get("allowed_commands", ["ls", "dir", "cat", "head", "tail", "pwd", "echo", "find", "grep"])
        self.allowed_commands_entry = ctk.CTkEntry(
            self.allowed_commands_frame,
            font=ctk.CTkFont(size=12),
            height=30
        )
        self.allowed_commands_entry.pack(fill="x", expand=True, padx=15, pady=5)
        self.allowed_commands_entry.insert(0, ", ".join(allowed_commands))
        
        # Обновить состояние UI
        self._update_security_ui()
    
    def _toggle_full_access(self):
        """Переключение полного доступа."""
        is_full = self.full_access_var.get()
        self.full_access_switch.configure(
            text="Полный доступ ⚠" if is_full else "Ограниченный доступ"
        )
        self._update_security_ui()
    
    def _update_security_ui(self):
        """Обновление состояния UI безопасности."""
        is_full = self.full_access_var.get()
        
        # Блокируем список команд при полном доступе
        if is_full:
            self.allowed_commands_entry.configure(state="disabled", fg_color="#1a1a1a")
        else:
            self.allowed_commands_entry.configure(state="normal", fg_color="#2b2b2b")
    
    def _create_buttons(self):
        """Кнопки сохранения/отмены."""
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Отмена",
            command=self.destroy,
            width=100
        )
        cancel_btn.pack(side="left", padx=10)
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="Сохранить",
            command=self._save_settings,
            width=100,
            fg_color="#27ae60"
        )
        save_btn.pack(side="right", padx=10)
    
    def _save_settings(self):
        """Save settings and close dialog."""
        self.current_settings["lmstudio_url"] = self.url_entry.get() or "http://localhost:1234"
        self.current_settings["model_name"] = self.model_entry.get() or None
        self.current_settings["temperature"] = self.temp_slider.get()
        self.current_settings["working_dir"] = self.workdir_entry.get() or str(Path.cwd())
        
        # Сохранение расширенных настроек модели
        max_tokens_str = self.max_tokens_entry.get().strip()
        if max_tokens_str:
            try:
                self.current_settings["max_tokens"] = int(max_tokens_str)
            except ValueError:
                self.current_settings["max_tokens"] = 4096
        
        timeout_str = self.timeout_entry.get().strip()
        if timeout_str:
            try:
                self.current_settings["timeout_seconds"] = int(timeout_str)
            except ValueError:
                self.current_settings["timeout_seconds"] = 120
        
        retry_str = self.retry_entry.get().strip()
        if retry_str:
            try:
                self.current_settings["retry_attempts"] = int(retry_str)
            except ValueError:
                self.current_settings["retry_attempts"] = 3
        
        # Сохранение настроек инструментов
        tools_settings = {
            "filesystem_enabled": getattr(self, "_filesystem_enabled_var", ctk.BooleanVar(value=True)).get(),
            "websearch_enabled": getattr(self, "_websearch_enabled_var", ctk.BooleanVar(value=False)).get(),
            "math_enabled": getattr(self, "_math_enabled_var", ctk.BooleanVar(value=False)).get(),
            "image_enabled": getattr(self, "_image_enabled_var", ctk.BooleanVar(value=False)).get(),
            "command_line_enabled": getattr(self, "_command_line_enabled_var", ctk.BooleanVar(value=True)).get(),
            "command_full_access": self.full_access_var.get(),
            "allowed_commands": [
                cmd.strip() 
                for cmd in self.allowed_commands_entry.get().split(",") 
                if cmd.strip()
            ],
        }
        self.current_settings["tools_settings"] = tools_settings
        
        logger.info(f"Settings saved: tools={tools_settings}")
        self.save_callback(self.current_settings)
        self.destroy()
    
    def _browse_workdir(self):
        """Open file dialog to select working directory."""
        import tkinter.filedialog as fd
        dirname = fd.askdirectory(initialdir=self.current_settings.get("working_dir", str(Path.cwd())))
        if dirname:
            self.workdir_entry.delete(0, 'end')
            self.workdir_entry.insert(0, dirname)
    
    def _browse_project(self):
        """Open file dialog to select project folder."""
        import tkinter.filedialog as fd
        initial_dir = self.current_settings.get("project_folder", "") or self.current_settings.get("working_dir", str(Path.cwd()))
        dirname = fd.askdirectory(initialdir=initial_dir)
        if dirname:
            self.project_entry.delete(0, 'end')
            self.project_entry.insert(0, dirname)


class DeepAgentsGUI(ctk.CTk):
    """Main DeepAgents GUI Application."""
    
    def __init__(self):
        super().__init__()
        
        self.title("DeepAgents GUI - LM Studio")
        self.geometry("1200x800")
        self.minsize(900, 600)
        
        # Settings
        self.settings = {
            "lmstudio_url": "http://localhost:1234",
            "model_name": None,
            "temperature": 0.7,
            "max_tokens": 4096,  # Default value, will be updated from LM Studio
            "timeout_seconds": 120,
            "retry_attempts": 3,
            "working_dir": str(Path.cwd()),
        }
        
        # Reference to settings dialog (for updating fields)
        self._settings_dialog = None
        
        # State
        self.lmstudio_client = LMStudioClient(self.settings["lmstudio_url"])
        self.conversation_history: list = []
        self.is_processing = False
        self.current_tool_calls: list = []
        self.current_tool_names: list = []  # Store available tool names for display
        self.tasks: list = []  # List of tasks/conversations
        self.last_assistant_bubble = None  # Track last assistant bubble for updates
        
        # Setup UI
        self._setup_ui()
        
        # Check connection on startup
        self.after(1000, self._check_lmstudio_connection)
    
    def _setup_ui(self):
        """Setup the user interface."""
        # Configure grid weights
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        self._create_header()
        
        # Main content area
        self._create_main_area()
        
        # Status bar
        self._create_status_bar()
    
    def _create_header(self):
        """Create header with controls."""
        header = ctk.CTkFrame(self, height=60, fg_color="#2b2b2b")
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        # Configure grid columns for header elements
        header.grid_columnconfigure(0, weight=1)  # Title section (expandable)
        header.grid_columnconfigure(1, weight=0)  # Connection indicator
        header.grid_columnconfigure(2, weight=0)  # Connect button
        header.grid_columnconfigure(3, weight=0)  # Model dropdown
        header.grid_columnconfigure(4, weight=0)  # New Task button
        header.grid_columnconfigure(5, weight=0)  # Settings button
        header.grid_columnconfigure(6, weight=0)  # Clear button
        
        # Logo/Title
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        ctk.CTkLabel(
            title_frame,
            text="🤖 DeepAgents GUI",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#3498db"
        ).pack(side="left")
        
        ctk.CTkLabel(
            title_frame,
            text="  |  Powered by LM Studio",
            font=ctk.CTkFont(size=14),
            text_color="#7f8c8d"
        ).pack(side="left")
        
        # Connection status
        self.connection_indicator = ctk.CTkLabel(
            header,
            text="●",
            font=ctk.CTkFont(size=24),
            text_color="#e74c3c"  # Red (disconnected)
        )
        self.connection_indicator.grid(row=0, column=1, sticky="e", padx=10)
        
        self.connection_label = ctk.CTkLabel(
            header,
            text="Disconnected",
            font=ctk.CTkFont(size=12),
            text_color="#e74c3c"
        )
        self.connection_label.grid(row=0, column=1, sticky="e", padx=(10, 5))
        
        # Connect/Refresh button
        self.connect_btn = ctk.CTkButton(
            header,
            text="🔄 Connect",
            command=self._check_lmstudio_connection,
            width=90,
            height=30
        )
        self.connect_btn.grid(row=0, column=2, padx=5, pady=10)
        
        # Model selection dropdown
        self.model_var = ctk.StringVar(value="Select model...")
        self.model_dropdown = ctk.CTkOptionMenu(
            header,
            variable=self.model_var,
            values=[],
            command=self._on_model_selected,
            width=150,
            height=30
        )
        self.model_dropdown.grid(row=0, column=3, padx=10, pady=10)
        
        # New Task button
        new_task_btn = ctk.CTkButton(
            header,
            text="📄 New Task",
            command=self._new_task,
            width=80,
            height=30
        )
        new_task_btn.grid(row=0, column=4, padx=10, pady=10)
        
        # Settings button
        settings_btn = ctk.CTkButton(
            header,
            text="⚙ Settings",
            command=self._open_settings,
            width=80,
            height=30
        )
        settings_btn.grid(row=0, column=5, padx=10, pady=10)
        
        # Clear chat button
        clear_btn = ctk.CTkButton(
            header,
            text="🗑 Clear Chat",
            command=self._clear_chat,
            width=80,
            height=30,
            fg_color="#e74c3c"
        )
        clear_btn.grid(row=0, column=6, padx=10, pady=10)
    
    def _create_main_area(self):
        """Create main content area with chat and tools."""
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Chat area
        chat_container = ctk.CTkFrame(main_frame, fg_color="#1e1e1e")
        chat_container.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        chat_container.grid_columnconfigure(0, weight=1)
        chat_container.grid_rowconfigure(0, weight=1)
        
        # Scrollable chat frame using new ChatWindow component
        self.chat_canvas = ChatWindow(
            chat_container,
            max_messages=200,
            fg_color="transparent"
        )
        self.chat_canvas.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Welcome message
        self._add_welcome_message()
        
        # Input area
        input_frame = ctk.CTkFrame(main_frame, height=100, fg_color="#2b2b2b")
        input_frame.grid(row=1, column=0, sticky="ew", padx=0, pady=(10, 0))
        input_frame.grid_columnconfigure(0, weight=1)
        
        # Text input
        self.input_text = ctk.CTkTextbox(
            input_frame,
            height=60,
            font=ctk.CTkFont(size=13),
            wrap="word"
        )
        self.input_text.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.input_text.bind("<Return>", lambda e: self._on_enter_pressed(e))
        self.input_text.bind("<Shift-Return>", lambda e: None)  # Allow new line
        
        # Send button
        self.send_btn = ctk.CTkButton(
            input_frame,
            text="➤ Send",
            command=self._send_message,
            height=40,
            width=100,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.send_btn.grid(row=0, column=1, padx=10, pady=10)
        
        # Bind Enter key
        self.input_text.bind("<Control-Return>", lambda e: self._send_message())
    
    def _create_status_bar(self):
        """Create status bar at bottom."""
        status_bar = ctk.CTkFrame(self, height=30, fg_color="#2b2b2b")
        status_bar.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        status_bar.grid_columnconfigure(1, weight=1)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            status_bar,
            text="Ready",
            font=ctk.CTkFont(size=11),
            text_color="#7f8c8d"
        )
        self.status_label.grid(row=0, column=0, padx=10, pady=5)
        
        # Token count / info
        self.info_label = ctk.CTkLabel(
            status_bar,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#7f8c8d"
        )
        self.info_label.grid(row=0, column=1, padx=10, pady=5, sticky="e")
    
    def _add_welcome_message(self):
        """Add welcome message to chat."""
        tools_available = []
        tools_available.append("File operations")  # Always available
        tools_available.append("Command execution")  # Always available
        if DDGS_AVAILABLE:
            tools_available.extend(["Web search", "News search"])
        if SYMPY_AVAILABLE:
            tools_available.extend(["Calculator", "Equation solver"])
        if PIL_AVAILABLE:
            tools_available.append("Image info")
        
        welcome_text = (
            f"Welcome to DeepAgents GUI! 🎉\n\n"
            f"I'm connected to LM Studio and ready to help you with various tasks.\n\n"
            f"Available tools:\n"
        )
        
        for tool in tools_available:
            welcome_text += f"• {tool}\n"
        
        welcome_text += "\nConfigure tools in Settings > Tools tab\nTo get started, simply type your message below!"
        
        logger.info(f"Displaying welcome message, tools available: {tools_available}")
        
        # Use new ChatWindow method
        self.chat_canvas.add_message(welcome_text, is_user=False, immediate=True)
    
    def _add_message_bubble(self, message: str, role: str = "user") -> MessageBubble:
        """Add a message bubble to the chat."""
        logger.debug(f"Adding {role} message bubble, message length: {len(message)}")
        
        # Use new ChatWindow method instead of direct MessageBubble creation
        is_user = (role == "user")
        self.chat_canvas.add_message(message, is_user=is_user, immediate=True)
        
        # Return None or last bubble if needed
        return self.chat_canvas._bubbles[-1] if self.chat_canvas._bubbles else None
    
    def _update_status(self, status: str):
        """Update status bar text."""
        logger.debug(f"Status update: {status}")
        self.status_label.configure(text=status)
    
    def _check_lmstudio_connection(self):
        """Check LM Studio connection asynchronously."""
        logger.info("Checking LM Studio connection...")
        async def check():
            connected = await self.lmstudio_client.check_connection()
            if connected:
                logger.info("LM Studio connection successful")
                self.connection_indicator.configure(text="●", text_color="#2ecc71")
                self.connection_label.configure(text="Connected", text_color="#2ecc71")
                self._update_status("Connected to LM Studio")
                
                # Get available models
                logger.debug("Fetching available models...")
                models = await self.lmstudio_client.get_available_models()
                if models:
                    logger.info(f"Found {len(models)} models from LM Studio")
                    self.info_label.configure(text=f"Available models: {len(models)}")
                    # Populate model dropdown
                    self.model_dropdown.configure(values=models)
                    if self.settings.get("model_name") and self.settings["model_name"] in models:
                        self.model_var.set(self.settings["model_name"])
                    else:
                        self.model_var.set(models[0] if models else "Select model...")
                    # Update connect button text
                    self.connect_btn.configure(text="🔄 Refresh")
                    
                    # Fetch and apply model parameters (max_tokens) for the selected model
                    selected_model = self.model_var.get()
                    if selected_model and selected_model in models:
                        await self._fetch_and_apply_model_params(selected_model)
            else:
                logger.warning("LM Studio connection failed")
                self.connection_indicator.configure(text="●", text_color="#e74c3c")
                self.connection_label.configure(text="Disconnected", text_color="#e74c3c")
                self._update_status("Cannot connect to LM Studio - Please start the server")
                self.model_dropdown.configure(values=[])
                self.model_var.set("No connection")
                # Update connect button text
                self.connect_btn.configure(text="🔄 Connect")
        
        # Run async function in a new thread with its own event loop
        def run_async_check():
            try:
                logger.debug("Starting async connection check in thread")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(check())
                loop.close()
            except Exception as e:
                logger.error(f"Connection check thread error: {str(e)}")
                self.after(0, lambda: self._update_status(f"Connection error: {str(e)}"))
        
        thread = threading.Thread(target=run_async_check, daemon=True)
        thread.start()
    
    async def _fetch_and_apply_model_params(self, model_id: str):
        """Fetch model parameters from LM Studio and apply to settings fields."""
        logger.info(f"Fetching parameters for model: {model_id}")
        try:
            model_info = await self.lmstudio_client.get_model_info(model_id)
            if model_info:
                # Extract max_tokens from model info
                # LM Studio returns different structures, check common paths
                max_tokens = None
                
                # Try different possible paths for max_tokens
                if 'max_tokens' in model_info:
                    max_tokens = model_info['max_tokens']
                elif 'context_length' in model_info:
                    max_tokens = model_info['context_length']
                elif 'meta' in model_info and 'max_tokens' in model_info['meta']:
                    max_tokens = model_info['meta']['max_tokens']
                elif 'capabilities' in model_info and 'max_tokens' in model_info['capabilities']:
                    max_tokens = model_info['capabilities']['max_tokens']
                
                if max_tokens:
                    logger.info(f"Model {model_id} max_tokens: {max_tokens}")
                    # Update the max_tokens field in settings dialog if open
                    # Store in main settings for later use
                    self.settings["max_tokens"] = max_tokens
                    
                    # If settings dialog is open, update the field
                    if hasattr(self, '_settings_dialog') and self._settings_dialog:
                        try:
                            self._settings_dialog.max_tokens_entry.delete(0, 'end')
                            self._settings_dialog.max_tokens_entry.insert(0, str(max_tokens))
                            self.after(0, lambda: self._update_status(f"Max tokens для {model_id}: {max_tokens}"))
                        except Exception as e:
                            logger.error(f"Failed to update settings dialog: {e}")
                    else:
                        self.after(0, lambda: self._update_status(f"Max tokens для {model_id}: {max_tokens}"))
                else:
                    logger.warning(f"Could not find max_tokens in model info for {model_id}")
        except Exception as e:
            logger.error(f"Error fetching model parameters: {e}")
    
    def _on_model_selected(self, selected_model: str):
        """Handle model selection from dropdown."""
        if selected_model and selected_model not in ("Select model...", "No connection"):
            self.settings["model_name"] = selected_model
            self._update_status(f"Model selected: {selected_model}")
            # Update connect button to show Refresh since we have a model selected
            if hasattr(self, 'connect_btn'):
                self.connect_btn.configure(text="🔄 Refresh")
            
            # Fetch and apply model parameters for the newly selected model
            async def fetch_params():
                await self._fetch_and_apply_model_params(selected_model)
            
            # Run in a new thread with its own event loop
            def run_fetch():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(fetch_params())
                    loop.close()
                except Exception as e:
                    logger.error(f"Error fetching model params: {e}")
            
            thread = threading.Thread(target=run_fetch, daemon=True)
            thread.start()
    
    def _open_settings(self):
        """Open settings dialog."""
        self._settings_dialog = SettingsDialog(self, self.settings, self._save_settings)
    
    def _save_settings(self, new_settings: dict):
        """Save settings and reconnect."""
        self.settings = new_settings
        self.lmstudio_client = LMStudioClient(self.settings["lmstudio_url"])
        
        # Log tool settings
        tools_settings = self.settings.get("tools_settings", {})
        logger.info(f"Settings updated: tools={tools_settings}")
        
        self._settings_dialog = None  # Clear reference when dialog is closed
        self._check_lmstudio_connection()
        self._update_status("Настройки сохранены")
    
    def _new_task(self):
        """Create a new task/conversation."""
        if self.is_processing:
            self._update_status("Cannot create new task while processing...")
            return
        
        # Save current conversation to tasks list (optional - could be expanded)
        if self.conversation_history:
            self.tasks.append({
                "history": self.conversation_history.copy(),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "name": f"Task {len(self.tasks) + 1}"
            })
        
        # Clear current conversation
        self._clear_chat()
        self._update_status("New task created")
    
    def _clear_chat(self):
        """Clear chat history."""
        self.conversation_history.clear()
        
        # Clear UI
        for widget in self.chat_canvas.winfo_children():
            widget.destroy()
        
        self._add_welcome_message()
        self._update_status("Chat cleared")
    
    def _on_enter_pressed(self, event):
        """Handle Enter key press."""
        if event.state & 0x1:  # Shift key
            return  # Allow new line
        self._send_message()
        return "break"  # Prevent default newline
    
    def _send_message(self):
        """Send message to agent."""
        if self.is_processing:
            return
        
        message = self.input_text.get("1.0", "end-1c").strip()
        if not message:
            return
        
        # Add user message to UI using new ChatWindow (immediate=True для главного потока)
        self.chat_canvas.add_message(message, is_user=True, immediate=True)
        self.conversation_history.append(HumanMessage(content=message))
        
        # Clear input
        self.input_text.delete("1.0", "end")
        
        # Process message
        self.is_processing = True
        self.send_btn.configure(state="disabled")
        self._update_status("Processing...")
        
        # Run in thread to avoid blocking UI
        thread = threading.Thread(target=self._process_message, args=(message,))
        thread.daemon = True
        thread.start()
    
    def _get_configured_tools(self):
        """Get tools based on current settings."""
        tools_settings = self.settings.get("tools_settings", {})
        tools = []
        
        # Get security settings
        full_access = tools_settings.get("command_full_access", False)
        allowed_commands = tools_settings.get("allowed_commands", ["ls", "dir", "cat", "head", "tail", "pwd", "echo", "find", "grep"])
        
        # Файловая система
        if tools_settings.get("filesystem_enabled", True):
            tools.extend([
                SimpleFilesystemTools.read_file,
                SimpleFilesystemTools.write_file,
                SimpleFilesystemTools.list_directory,
            ])
            logger.debug("Added filesystem tools")
        
        # Командная строка (всегда добавляем, но с проверкой прав внутри)
        if tools_settings.get("command_line_enabled", True):
            # Используем вспомогательную функцию для создания инструмента с настройками безопасности
            execute_cmd = get_execute_command_tool(
                full_access=full_access,
                allowed_commands=allowed_commands
            )
            tools.append(execute_cmd)
            logger.debug(f"Added command tool (full_access={full_access})")
        
        # Веб-поиск
        if tools_settings.get("websearch_enabled", DDGS_AVAILABLE) and DDGS_AVAILABLE:
            tools.extend([
                WebSearchTools.web_search,
                WebSearchTools.news_search,
            ])
            logger.debug("Added web search tools")
        
        # Математика
        if tools_settings.get("math_enabled", SYMPY_AVAILABLE) and SYMPY_AVAILABLE:
            tools.extend([
                MathTools.calculate,
                MathTools.solve_equation,
            ])
            logger.debug("Added math tools")
        
        # Изображения
        if tools_settings.get("image_enabled", PIL_AVAILABLE) and PIL_AVAILABLE:
            tools.append(ImageTools.get_image_info)
            logger.debug("Added image tools")
        
        logger.info(f"Total tools configured: {len(tools)}")
        return tools
    
    def _process_message(self, message: str):
        """Process message in background thread."""
        try:
            logger.info(f"Processing message: {message[:50]}...")
            
            # Get model - use selected model from dropdown if available
            model_name = self.settings.get("model_name")
            # If no model selected in settings but we have a selection from dropdown, use that
            if not model_name and hasattr(self, 'model_var'):
                selected = self.model_var.get()
                if selected and selected not in ("Select model...", "No connection"):
                    model_name = selected
            
            logger.info(f"Using model: {model_name or 'local-model'}")
            model = self.lmstudio_client.get_chat_model(
                model_name,
                self.settings["temperature"]
            )
            
            # Get tools based on current settings
            tools = self._get_configured_tools()
            
            logger.info(f"Total tools available: {len(tools)}")
            tool_names = [getattr(t, 'name', getattr(t, '__name__', 'unknown')) for t in tools]
            logger.debug(f"Tool names: {tool_names}")
            
            # Store tool names for display during agent execution
            self.current_tool_names = tool_names
            
            # Create agent - use deepagents if available, otherwise basic LangGraph
            if DEEPAGENTS_AVAILABLE:
                # Use full DeepAgents with all features
                logger.info("Creating DeepAgent with all tools")
                agent = create_deep_agent(
                    model=model,
                    tools=tools,
                    system_prompt=(
                        "You are a helpful AI assistant with access to multiple tools including:\n"
                        "- Filesystem operations (read/write files, list directories)\n"
                        "- Web search for current information\n"
                        "- Mathematical calculations and equation solving\n"
                        "- Image information retrieval\n"
                        "- Safe shell command execution\n"
                        "Always be helpful and thorough in completing tasks. Use tools when appropriate."
                    )
                )
            else:
                # Fallback to basic LangGraph ReAct agent
                logger.info("Creating LangGraph ReAct agent (deepagents not available)")
                from langgraph.prebuilt import create_react_agent
                agent = create_react_agent(model, tools)
            
            # Run agent with tool call tracking
            config = {"recursion_limit": 100}
            logger.info("Invoking agent...")
            
            # Track tool usage for display
            self.after(0, lambda: self._update_status(f"Processing... Tools: {', '.join(self.current_tool_names[:3])}..."))
            
            response = agent.invoke(
                {"messages": self.conversation_history},
                config=config
            )
            logger.info("Agent invocation complete")
            
            # Get assistant response
            assistant_message = response["messages"][-1]
            assistant_content = assistant_message.content if hasattr(assistant_message, 'content') else str(assistant_message)
            logger.info(f"Response length: {len(assistant_content)} characters")
            
            # Add to history
            self.conversation_history.append(AIMessage(content=assistant_content))
            
            # Update UI in main thread
            self.after(0, lambda: self._display_assistant_response(assistant_content))
            
        except Exception as e:
            logger.error(f"Message processing failed: {str(e)}", exc_info=True)
            error_msg = f"Error: {str(e)}\n\nPlease ensure LM Studio is running and a model is loaded."
            self.after(0, lambda: self._display_assistant_response(error_msg))
        
        finally:
            self.is_processing = False
            self.after(0, lambda: self.send_btn.configure(state="normal"))
            self.after(0, lambda: self._update_status("Ready"))
    
    def _display_assistant_response(self, content: str):
        """Display assistant response in chat."""
        # Use new ChatWindow method with immediate=True для вызова из главного потока
        self.chat_canvas.add_message(content, is_user=False, immediate=True)


def main():
    """Main entry point."""
    app = DeepAgentsGUI()
    app.mainloop()


if __name__ == "__main__":
    main()

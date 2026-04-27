#!/usr/bin/env python3
"""
DeepAgents GUI - Модуль настроек и диалоговых окон.

Этот модуль содержит класс SettingsDialog для управления настройками приложения,
включая конфигурацию LM Studio, управление инструментами и настройки безопасности.
"""

import customtkinter as ctk
from pathlib import Path
from typing import Callable


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
                "websearch_enabled": False,
                "math_enabled": False,
                "python_enabled": True,
                "image_enabled": False,
                "command_full_access": False,
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
            tools.get("websearch_enabled", False),
            disabled=False,
            disabled_text="Требуется пакет duckduckgo-search"
        )
        
        # Математика
        self._create_tool_toggle(
            main_frame,
            "🧮 Математика",
            "Вычисления и решение уравнений через SymPy",
            "math_enabled",
            tools.get("math_enabled", False),
            disabled=False,
            disabled_text="Требуется пакет sympy"
        )
        
        # Python инструменты
        self._create_tool_toggle(
            main_frame,
            "🐍 Python инструменты",
            "Установка pip, выполнение скриптов, проверка синтаксиса, форматирование",
            "python_enabled",
            tools.get("python_enabled", True)
        )
        
        # Изображения
        self._create_tool_toggle(
            main_frame,
            "🖼️ Обработка изображений",
            "Получение информации об изображениях",
            "image_enabled",
            tools.get("image_enabled", False),
            disabled=False,
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
        
        # Label frame
        label_frame = ctk.CTkFrame(frame, fg_color="transparent")
        label_frame.pack(side="left", fill="both", expand=True)
        
        # Title
        ctk.CTkLabel(
            label_frame,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")
        
        # Description
        ctk.CTkLabel(
            label_frame,
            text=description,
            font=ctk.CTkFont(size=11),
            text_color="#7f8c8d"
        ).pack(anchor="w")
        
        # Disabled text
        if disabled and disabled_text:
            ctk.CTkLabel(
                label_frame,
                text=disabled_text,
                font=ctk.CTkFont(size=10),
                text_color="#e74c3c"
            ).pack(anchor="w")
        
        # Toggle switch
        switch = ctk.CTkSwitch(
            frame,
            text="",
            command=lambda: None,
            variable=ctk.BooleanVar(value=enabled),
            state="disabled" if disabled else "normal"
        )
        switch.select() if enabled else switch.deselect()
        switch.pack(side="right", padx=10, pady=10)
        
        # Store reference for later retrieval
        setattr(self, f"_{setting_key}_switch", switch)
        setattr(self, f"_{setting_key}_var", switch.cget("variable"))
    
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
        
        desc = ctk.CTkLabel(
            main_frame,
            text="Контролируйте доступ к опасным операциям",
            font=ctk.CTkFont(size=12),
            text_color="#7f8c8d"
        )
        desc.pack(pady=(0, 20))
        
        tools = self.current_settings.get("tools_settings", {})
        
        # Command line access mode
        access_frame = ctk.CTkFrame(main_frame)
        access_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            access_frame,
            text="Режим доступа к командной строке:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=10, pady=10)
        
        self.command_access_var = ctk.StringVar(value="restricted" if not tools.get("command_full_access", False) else "full")
        
        access_mode_frame = ctk.CTkFrame(access_frame, fg_color="transparent")
        access_mode_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkRadioButton(
            access_mode_frame,
            text="Ограниченный (только безопасные команды)",
            variable=self.command_access_var,
            value="restricted"
        ).pack(anchor="w", pady=5)
        
        ctk.CTkRadioButton(
            access_mode_frame,
            text="Полный доступ (все команды)",
            variable=self.command_access_var,
            value="full"
        ).pack(anchor="w", pady=5)
        
        # Allowed commands list
        allowed_frame = ctk.CTkFrame(main_frame)
        allowed_frame.pack(fill="both", expand=True, pady=10)
        
        ctk.CTkLabel(
            allowed_frame,
            text="Разрешенные команды (через запятую):",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.allowed_commands_entry = ctk.CTkTextbox(
            allowed_frame,
            height=150,
            font=ctk.CTkFont(size=12)
        )
        self.allowed_commands_entry.pack(fill="both", expand=True, padx=10, pady=10)
        
        allowed_commands = tools.get("allowed_commands", [])
        self.allowed_commands_entry.insert("0.0", ", ".join(allowed_commands))
        
        # Warning
        warning_label = ctk.CTkLabel(
            main_frame,
            text="⚠️ Полный доступ к командной строке может быть опасен!\nИспользуйте только в доверенной среде.",
            font=ctk.CTkFont(size=11),
            text_color="#e74c3c",
            justify="left"
        )
        warning_label.pack(anchor="w", padx=10, pady=10)
    
    def _create_buttons(self):
        """Create dialog buttons."""
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Save button
        save_btn = ctk.CTkButton(
            button_frame,
            text="Сохранить",
            command=self._save_settings,
            width=120
        )
        save_btn.pack(side="right", padx=10)
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Отмена",
            command=self.destroy,
            fg_color="transparent",
            border_width=2,
            width=120
        )
        cancel_btn.pack(side="right", padx=10)
    
    def _browse_workdir(self):
        """Browse for working directory."""
        from tkinter import filedialog
        directory = filedialog.askdirectory(initialdir=self.workdir_entry.get() or Path.cwd())
        if directory:
            self.workdir_entry.delete(0, 'end')
            self.workdir_entry.insert(0, directory)
    
    def _save_settings(self):
        """Save settings and close dialog."""
        # Gather settings from all tabs
        settings = {
            "lmstudio_url": self.url_entry.get() or "http://localhost:1234",
            "model_name": self.model_entry.get(),
            "temperature": self.temp_slider.get(),
            "max_tokens": int(self.max_tokens_entry.get()) if self.max_tokens_entry.get() else 4096,
            "timeout_seconds": int(self.timeout_entry.get()) if self.timeout_entry.get() else 120,
            "retry_attempts": int(self.retry_entry.get()) if self.retry_entry.get() else 3,
            "working_dir": self.workdir_entry.get() or str(Path.cwd()),
            "tools_settings": {}
        }
        
        # Gather tool settings
        tools_settings = self.current_settings.get("tools_settings", {})
        for key in ["filesystem_enabled", "websearch_enabled", "math_enabled", 
                    "python_enabled", "image_enabled", "command_line_enabled"]:
            var = getattr(self, f"_{key}_var", None)
            if var:
                tools_settings[key] = var.get()
        
        # Security settings
        tools_settings["command_full_access"] = self.command_access_var.get() == "full"
        allowed_text = self.allowed_commands_entry.get("0.0", "end").strip()
        tools_settings["allowed_commands"] = [cmd.strip() for cmd in allowed_text.split(",") if cmd.strip()]
        
        settings["tools_settings"] = tools_settings
        
        # Call save callback
        self.save_callback(settings)
        self.destroy()

"""
Модуль ProcessWindow для отображения процесса выполнения задач агентом.

Требования:
- Отображение действий агента в реальном времени
- Визуализация использования инструментов
- Показ промежуточных сообщений и статуса
- Прокручиваемый лог событий
- Цветовая индикация типов событий
"""

import customtkinter as ctk
import tkinter as tk
from typing import Optional, Dict, Any, List
from datetime import datetime
import queue
import threading


class ProcessWindow(ctk.CTkScrollableFrame):
    """
    Окно отображения процесса выполнения задач агентом.
    
    Атрибуты:
        max_events (int): Максимальное количество событий в логе (500)
        event_queue (queue.Queue): Очередь для потокобезопасного обновления
    """
    
    # Цвета для разных типов событий
    EVENT_COLORS = {
        'action': '#3498db',      # Синий - действия
        'tool': '#9b59b6',        # Фиолетовый - инструменты
        'message': '#2ecc71',     # Зеленый - сообщения
        'info': '#95a5a6',        # Серый - информация
        'warning': '#f39c12',     # Оранжевый - предупреждения
        'error': '#e74c3c',       # Красный - ошибки
        'success': '#27ae60',     # Темно-зеленый - успех
    }
    
    # Иконки для типов событий
    EVENT_ICONS = {
        'action': '⚡',
        'tool': '🔧',
        'message': '💬',
        'info': 'ℹ️',
        'warning': '⚠️',
        'error': '❌',
        'success': '✅',
    }
    
    def __init__(
        self,
        master: any,
        max_events: int = 500,
        **kwargs
    ):
        # Устанавливаем цвета по умолчанию
        if 'fg_color' not in kwargs:
            kwargs['fg_color'] = '#1e1e1e'
        if 'scrollbar_button_color' not in kwargs:
            kwargs['scrollbar_button_color'] = '#555555'
        if 'scrollbar_button_hover_color' not in kwargs:
            kwargs['scrollbar_button_hover_color'] = '#777777'
        
        super().__init__(master, **kwargs)
        
        self.max_events = max_events
        
        # Очередь для потокобезопасных обновлений
        self.event_queue: queue.Queue = queue.Queue()
        
        # Хранилище ссылок на элементы событий
        self._events: List[ctk.CTkFrame] = []
        
        # Флаг активности процесса
        self._is_active = False
        self._stop_event = threading.Event()
        
        # Настройка grid для растягивания
        self.grid_columnconfigure(0, weight=1)
        
        # Заголовок секции
        self._create_header()
        
        # Контейнер для событий
        self._events_container = ctk.CTkFrame(self, fg_color='transparent')
        self._events_container.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        self._events_container.grid_columnconfigure(0, weight=1)
        
        # Запуск обработчика очереди
        self._process_queue()
    
    def _create_header(self):
        """Создание заголовка панели процесса."""
        header_frame = ctk.CTkFrame(self, fg_color='transparent')
        header_frame.grid(row=0, column=0, sticky='ew', padx=10, pady=(10, 5))
        
        # Заголовок
        title = ctk.CTkLabel(
            header_frame,
            text="📊 Процесс выполнения",
            font=ctk.CTkFont(size=14, weight='bold'),
            text_color='#ffffff'
        )
        title.pack(side='left')
        
        # Индикатор активности
        self._status_indicator = ctk.CTkLabel(
            header_frame,
            text="⚫ Ожидание",
            font=ctk.CTkFont(size=11),
            text_color='#95a5a6'
        )
        self._status_indicator.pack(side='right')
        
        # Кнопка очистки
        clear_btn = ctk.CTkButton(
            header_frame,
            text="🗑️ Очистить",
            command=self.clear,
            width=80,
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color='#3a3a3a',
            hover_color='#4a4a4a'
        )
        clear_btn.pack(side='right', padx=10)
    
    def _process_queue(self):
        """Обработка очереди событий (вызывается каждые 50мс)."""
        try:
            while True:
                task = self.event_queue.get_nowait()
                action = task['action']
                
                if action == 'add_event':
                    self._do_add_event(
                        event_type=task['event_type'],
                        message=task['message'],
                        details=task.get('details', '')
                    )
                elif action == 'update_status':
                    self._do_update_status(task['status'])
                elif action == 'clear':
                    self._do_clear()
                    
        except queue.Empty:
            pass
        
        # Планируем следующий вызов через 50мс
        self.after(50, self._process_queue)
    
    def _do_add_event(self, event_type: str, message: str, details: str = ''):
        """Добавление нового события (внутренняя реализация)."""
        # Проверка лимита
        if len(self._events) >= self.max_events:
            # Удаляем самое старое событие
            old_event = self._events.pop(0)
            old_event.destroy()
        
        # Создание фрейма события
        event_frame = ctk.CTkFrame(
            self._events_container,
            fg_color='#2a2a2a',
            corner_radius=6
        )
        
        row = len(self._events)
        event_frame.grid(row=row, column=0, sticky='ew', padx=3, pady=2)
        event_frame.grid_columnconfigure(1, weight=1)
        
        # Иконка
        icon = self.EVENT_ICONS.get(event_type, '•')
        icon_label = ctk.CTkLabel(
            event_frame,
            text=icon,
            font=ctk.CTkFont(size=12),
            width=25,
            anchor='w'
        )
        icon_label.grid(row=0, column=0, padx=(5, 5), pady=5)
        
        # Основной текст
        color = self.EVENT_COLORS.get(event_type, '#ffffff')
        
        # Время события
        timestamp = datetime.now().strftime('%H:%M:%S')
        time_label = ctk.CTkLabel(
            event_frame,
            text=timestamp,
            font=ctk.CTkFont(size=9, family='Consolas'),
            text_color='#666666',
            width=50,
            anchor='w'
        )
        time_label.grid(row=0, column=1, sticky='w', pady=5)
        
        # Сообщение
        msg_label = ctk.CTkLabel(
            event_frame,
            text=message,
            font=ctk.CTkFont(size=11),
            text_color=color,
            anchor='w',
            justify='left'
        )
        msg_label.grid(row=0, column=2, sticky='w', padx=(10, 5), pady=5)
        
        # Детали (если есть)
        if details:
            details_frame = ctk.CTkFrame(event_frame, fg_color='#1a1a1a', corner_radius=4)
            details_frame.grid(row=1, column=0, columnspan=3, sticky='ew', padx=5, pady=(0, 5))
            
            details_text = ctk.CTkTextbox(
                details_frame,
                height=40,
                wrap=tk.WORD,
                font=('Consolas', 10),
                border_width=0,
                fg_color='transparent',
                text_color='#aaaaaa',
                state='disabled'
            )
            details_text.pack(fill='both', expand=True, padx=5, pady=5)
            details_text.insert('1.0', details)
            details_text.configure(state='disabled')
        
        self._events.append(event_frame)
        
        # Автоскролл вниз
        self._scroll_to_bottom()
    
    def _do_update_status(self, status: str):
        """Обновление индикатора статуса."""
        status_map = {
            'idle': ('⚫ Ожидание', '#95a5a6'),
            'running': ('🟢 Выполнение', '#2ecc71'),
            'processing': ('🟡 Обработка', '#f39c12'),
            'error': ('🔴 Ошибка', '#e74c3c'),
            'stopped': ('⚫ Остановлено', '#95a5a6'),
        }
        
        text, color = status_map.get(status, ('⚫ Неизвестно', '#95a5a6'))
        self._status_indicator.configure(text=text, text_color=color)
    
    def _do_clear(self):
        """Очистка всех событий."""
        for event in self._events:
            event.destroy()
        self._events.clear()
    
    def _scroll_to_bottom(self):
        """Прокрутка к последнему событию."""
        self._scrollbar.set(1.0, 1.0)
    
    # === Публичные методы для внешнего использования ===
    
    def add_event(
        self,
        event_type: str,
        message: str,
        details: str = '',
        immediate: bool = False
    ):
        """
        Добавление нового события (потокобезопасно).
        
        Args:
            event_type: Тип события ('action', 'tool', 'message', 'info', 'warning', 'error', 'success')
            message: Основное сообщение
            details: Дополнительные детали (отображаются в раскрывающемся блоке)
            immediate: Если True, добавляет немедленно (для вызова из главного потока)
        """
        if immediate:
            self._do_add_event(event_type, message, details)
        else:
            self.event_queue.put({
                'action': 'add_event',
                'event_type': event_type,
                'message': message,
                'details': details
            })
    
    def add_action(self, message: str, details: str = ''):
        """Добавление события действия."""
        self.add_event('action', message, details)
    
    def add_tool_use(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_output: str = ''
    ):
        """
        Добавление события использования инструмента.
        
        Args:
            tool_name: Название инструмента
            tool_input: Входные параметры инструмента
            tool_output: Результат выполнения инструмента
        """
        input_str = ', '.join(f'{k}={v}' for k, v in tool_input.items()) if tool_input else 'нет параметров'
        message = f"Инструмент: {tool_name}"
        details = f"Вход: {input_str}\n"
        if tool_output:
            details += f"Выход: {tool_output[:500]}"  # Ограничиваем длину вывода
        
        self.add_event('tool', message, details)
    
    def add_message(self, message: str, details: str = ''):
        """Добавление информационного сообщения."""
        self.add_event('message', message, details)
    
    def add_info(self, message: str):
        """Добавление информационной записи."""
        self.add_event('info', message)
    
    def add_warning(self, message: str, details: str = ''):
        """Добавление предупреждения."""
        self.add_event('warning', message, details)
    
    def add_error(self, message: str, details: str = ''):
        """Добавление ошибки."""
        self.add_event('error', message, details)
    
    def add_success(self, message: str):
        """Добавление сообщения об успехе."""
        self.add_event('success', message)
    
    def update_status(self, status: str):
        """
        Обновление статуса процесса.
        
        Args:
            status: Статус ('idle', 'running', 'processing', 'error', 'stopped')
        """
        self.event_queue.put({
            'action': 'update_status',
            'status': status
        })
    
    def clear(self):
        """Очистка всех событий (потокобезопасно)."""
        self.event_queue.put({'action': 'clear'})
    
    def set_active(self, is_active: bool):
        """
        Установка активности процесса.
        
        Args:
            is_active: True если процесс активен
        """
        self._is_active = is_active
        if is_active:
            self._stop_event.clear()
            self.update_status('running')
        else:
            self._stop_event.set()
            self.update_status('idle')
    
    def stop(self):
        """Сигнал остановки процесса."""
        self._stop_event.set()
        self.update_status('stopped')
    
    def is_active(self) -> bool:
        """Проверка активности процесса."""
        return self._is_active
    
    def should_stop(self) -> bool:
        """Проверка флага остановки."""
        return self._stop_event.is_set()
    
    def get_event_count(self) -> int:
        """Получение количества событий."""
        return len(self._events)


class ToolExecutionPanel(ctk.CTkFrame):
    """
    Панель для отображения текущего выполняемого инструмента.
    
    Показывает прогресс выполнения текущего инструмента в реальном времени.
    """
    
    def __init__(self, master: any, **kwargs):
        if 'fg_color' not in kwargs:
            kwargs['fg_color'] = '#2a2a2a'
        if 'corner_radius' not in kwargs:
            kwargs['corner_radius'] = 8
        
        super().__init__(master, **kwargs)
        
        self._current_tool = None
        self._is_running = False
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Создание виджетов панели."""
        self.grid_columnconfigure(0, weight=1)
        
        # Заголовок
        title = ctk.CTkLabel(
            self,
            text="🔧 Активный инструмент",
            font=ctk.CTkFont(size=12, weight='bold'),
            text_color='#ffffff'
        )
        title.grid(row=0, column=0, sticky='w', padx=10, pady=(10, 5))
        
        # Название инструмента
        self._tool_name_label = ctk.CTkLabel(
            self,
            text="Нет активного инструмента",
            font=ctk.CTkFont(size=11),
            text_color='#95a5a6',
            anchor='w'
        )
        self._tool_name_label.grid(row=1, column=0, sticky='ew', padx=10, pady=5)
        
        # Прогресс бар
        self._progress_bar = ctk.CTkProgressBar(
            self,
            mode='indeterminate',
            progress_color='#3498db'
        )
        self._progress_bar.grid(row=2, column=0, sticky='ew', padx=10, pady=5)
        self._progress_bar.set(0)
        
        # Параметры инструмента
        self._params_frame = ctk.CTkFrame(self, fg_color='#1a1a1a', corner_radius=4)
        self._params_frame.grid(row=3, column=0, sticky='ew', padx=10, pady=(5, 10))
        self._params_frame.grid_columnconfigure(0, weight=1)
        
        self._params_label = ctk.CTkLabel(
            self._params_frame,
            text="Параметры: -",
            font=ctk.CTkFont(size=10, family='Consolas'),
            text_color='#666666',
            anchor='w',
            justify='left'
        )
        self._params_label.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
    
    def start_tool(self, tool_name: str, params: Dict[str, Any]):
        """
        Начало выполнения инструмента.
        
        Args:
            tool_name: Название инструмента
            params: Параметры инструмента
        """
        self._current_tool = tool_name
        self._is_running = True
        
        self._tool_name_label.configure(
            text=f"Выполняется: {tool_name}",
            text_color='#3498db'
        )
        
        params_str = ', '.join(f'{k}={repr(v)}' for k, v in params.items()) if params else 'нет параметров'
        self._params_label.configure(text=f"Параметры: {params_str}")
        
        self._progress_bar.start()
    
    def stop_tool(self, result: str = ''):
        """
        Завершение выполнения инструмента.
        
        Args:
            result: Результат выполнения (опционально)
        """
        self._is_running = False
        self._current_tool = None
        
        self._tool_name_label.configure(
            text="Нет активного инструмента",
            text_color='#95a5a6'
        )
        
        self._params_label.configure(text="Параметры: -")
        self._progress_bar.stop()
        self._progress_bar.set(0)
    
    def is_running(self) -> bool:
        """Проверка, выполняется ли инструмент."""
        return self._is_running

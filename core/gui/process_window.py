"""
Окно отображения процесса выполнения задач агентом.

Требования:
- Отображение действий агента в реальном времени
- Визуализация использования инструментов
- Промежуточные сообщения о ходе выполнения
- Статусы операций (ожидание, выполнение, завершено, ошибка)
- Иерархическое представление шагов
"""

import customtkinter as ctk
import tkinter as tk
from typing import Optional, Dict, Any, List
from datetime import datetime
import threading
import queue


class ProcessStep(ctk.CTkFrame):
    """
    Виджет одного шага процесса выполнения.
    
    Атрибуты:
        step_id (str): Уникальный идентификатор шага
        status (str): Статус (pending, running, completed, error)
        title (str): Заголовок шага
        details (str): Детали выполнения
    """
    
    def __init__(
        self,
        master: any,
        step_id: str,
        title: str,
        details: str = "",
        status: str = "pending",
        **kwargs
    ):
        # Цвета по умолчанию
        if 'fg_color' not in kwargs:
            kwargs['fg_color'] = '#2b2b2b'
        if 'corner_radius' not in kwargs:
            kwargs['corner_radius'] = 8
        if 'height' not in kwargs:
            kwargs['height'] = 50
        
        super().__init__(master, **kwargs)
        
        self.step_id = step_id
        self.status = status
        self.title = title
        self.details = details
        
        # Настройка grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Индикатор статуса
        self._create_status_indicator()
        
        # Заголовок
        self._create_title_label()
        
        # Детали (опционально)
        self._create_details_label()
        
        # Время начала/окончания
        self._create_time_label()
        
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
    
    def _create_status_indicator(self):
        """Создание индикатора статуса."""
        self.status_canvas = ctk.CTkCanvas(
            self,
            width=24,
            height=24,
            bg='#2b2b2b',
            highlightthickness=0
        )
        self.status_canvas.grid(row=0, column=0, padx=(10, 10), pady=10)
        
        self._update_status_indicator()
    
    def _update_status_indicator(self):
        """Обновление индикатора в зависимости от статуса."""
        self.status_canvas.delete("all")
        
        colors = {
            "pending": "#7f8c8d",      # Серый
            "running": "#3498db",       # Синий
            "completed": "#27ae60",     # Зелёный
            "error": "#e74c3c"          # Красный
        }
        
        icons = {
            "pending": "⏳",
            "running": "⚙️",
            "completed": "✓",
            "error": "✗"
        }
        
        color = colors.get(self.status, "#7f8c8d")
        icon = icons.get(self.status, "?")
        
        # Рисуем круг
        self.status_canvas.create_oval(
            2, 2, 22, 22,
            outline=color,
            width=2
        )
        
        # Рисуем иконку/символ
        self.status_canvas.create_text(
            12, 12,
            text=icon,
            fill=color,
            font=('Arial', 12)
        )
    
    def _create_title_label(self):
        """Создание метки заголовка."""
        self.title_label = ctk.CTkLabel(
            self,
            text=self.title,
            font=ctk.CTkFont(size=13, weight='bold'),
            anchor='w'
        )
        self.title_label.grid(row=0, column=1, sticky='w', padx=(0, 10), pady=(10, 2))
    
    def _create_details_label(self):
        """Создание метки деталей."""
        self.details_label = ctk.CTkLabel(
            self,
            text=self.details,
            font=ctk.CTkFont(size=11),
            text_color='#7f8c8d',
            anchor='w'
        )
        self.details_label.grid(row=1, column=1, sticky='w', padx=(0, 10), pady=(0, 10))
    
    def _create_time_label(self):
        """Создание метки времени."""
        self.time_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=10),
            text_color='#7f8c8d',
            anchor='e'
        )
        self.time_label.grid(row=0, column=2, rowspan=2, sticky='e', padx=(10, 10), pady=10)
    
    def set_status(self, status: str, details: str = ""):
        """
        Установка статуса шага.
        
        Args:
            status: Новый статус (pending, running, completed, error)
            details: Дополнительные детали
        """
        old_status = self.status
        self.status = status
        
        # Обновляем время
        now = datetime.now()
        if status == "running" and old_status == "pending":
            self.start_time = now
        elif status in ["completed", "error"]:
            self.end_time = now
        
        # Обновляем детали
        if details:
            self.details = details
            self.details_label.configure(text=details)
        
        # Обновляем индикатор
        self._update_status_indicator()
        
        # Обновляем время
        if self.start_time:
            time_str = self.start_time.strftime("%H:%M:%S")
            if self.end_time:
                duration = (self.end_time - self.start_time).total_seconds()
                time_str += f" ({duration:.1f}s)"
            self.time_label.configure(text=time_str)
    
    def update_details(self, details: str):
        """Обновление деталей выполнения."""
        self.details = details
        self.details_label.configure(text=details)


class ToolUsagePanel(ctk.CTkFrame):
    """
    Панель отображения использования инструментов.
    
    Показывает какой инструмент вызывается, с какими параметрами,
    и результат выполнения.
    """
    
    def __init__(self, master: any, **kwargs):
        if 'fg_color' not in kwargs:
            kwargs['fg_color'] = '#1e1e1e'
        if 'corner_radius' not in kwargs:
            kwargs['corner_radius'] = 8
        
        super().__init__(master, **kwargs)
        
        # Настройка grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Заголовок
        header = ctk.CTkLabel(
            self,
            text="🛠️ Использование инструментов",
            font=ctk.CTkFont(size=13, weight='bold'),
            text_color='#3498db'
        )
        header.grid(row=0, column=0, sticky='w', padx=10, pady=(10, 5))
        
        # Область содержимого
        self.content_frame = ctk.CTkScrollableFrame(
            self,
            fg_color='transparent'
        )
        self.content_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=(0, 10))
        
        # Список вызовов инструментов
        self.tool_calls: List[Dict[str, Any]] = []
        self.call_widgets: List[ctk.CTkFrame] = []
    
    def add_tool_call(self, tool_name: str, parameters: Dict[str, Any], call_id: str = ""):
        """
        Добавление записи о вызове инструмента.
        
        Args:
            tool_name: Название инструмента
            parameters: Параметры вызова
            call_id: Уникальный идентификатор вызова
        """
        if not call_id:
            call_id = f"call_{len(self.tool_calls)}"
        
        call_record = {
            "id": call_id,
            "tool_name": tool_name,
            "parameters": parameters,
            "status": "running",
            "result": None,
            "timestamp": datetime.now()
        }
        self.tool_calls.append(call_record)
        
        # Создаём виджет
        widget = self._create_tool_call_widget(call_record)
        self.call_widgets.append(widget)
        
        # Размещаем
        widget.pack(fill='x', padx=5, pady=3)
        
        return call_id
    
    def _create_tool_call_widget(self, call_record: Dict[str, Any]) -> ctk.CTkFrame:
        """Создание виджета для отображения вызова инструмента."""
        frame = ctk.CTkFrame(self.content_frame, fg_color='#2b2b2b', corner_radius=6)
        
        # Верхняя строка: название инструмента + статус
        top_frame = ctk.CTkFrame(frame, fg_color='transparent')
        top_frame.pack(fill='x', padx=10, pady=(8, 4))
        
        # Название инструмента
        name_label = ctk.CTkLabel(
            top_frame,
            text=f"🔧 {call_record['tool_name']}",
            font=ctk.CTkFont(size=12, weight='bold'),
            text_color='#3498db',
            anchor='w'
        )
        name_label.pack(side='left')
        
        # Индикатор статуса
        status_label = ctk.CTkLabel(
            top_frame,
            text="⚙️ Выполняется...",
            font=ctk.CTkFont(size=11),
            text_color='#f39c12',
            anchor='e'
        )
        status_label.pack(side='right')
        call_record['_status_label'] = status_label
        
        # Параметры
        params_text = self._format_parameters(call_record['parameters'])
        if params_text:
            params_label = ctk.CTkLabel(
                frame,
                text=params_text,
                font=ctk.CTkFont(size=10, family='Consolas'),
                text_color='#7f8c8d',
                anchor='w',
                justify='left'
            )
            params_label.pack(fill='x', padx=10, pady=(0, 8))
        
        # Результат (скрыт по умолчанию)
        result_label = ctk.CTkLabel(
            frame,
            text="",
            font=ctk.CTkFont(size=10, family='Consolas'),
            text_color='#27ae60',
            anchor='w',
            justify='left'
        )
        result_label.pack(fill='x', padx=10, pady=(0, 8))
        call_record['_result_label'] = result_label
        
        return frame
    
    def _format_parameters(self, parameters: Dict[str, Any]) -> str:
        """Форматирование параметров для отображения."""
        if not parameters:
            return ""
        
        lines = []
        for key, value in parameters.items():
            # Ограничиваем длину значения
            value_str = str(value)
            if len(value_str) > 100:
                value_str = value_str[:97] + "..."
            lines.append(f"  {key}: {value_str}")
        
        return "Параметры:\n" + "\n".join(lines)
    
    def update_tool_call(self, call_id: str, status: str, result: str = ""):
        """
        Обновление статуса вызова инструмента.
        
        Args:
            call_id: Идентификатор вызова
            status: Новый статус (running, completed, error)
            result: Результат выполнения
        """
        # Находим запись
        call_record = None
        widget_index = -1
        for i, record in enumerate(self.tool_calls):
            if record['id'] == call_id:
                call_record = record
                widget_index = i
                break
        
        if call_record is None:
            return
        
        # Обновляем статус
        call_record['status'] = status
        
        # Обновляем виджет
        if widget_index >= 0 and widget_index < len(self.call_widgets):
            widget = self.call_widgets[widget_index]
            
            # Обновляем метку статуса
            status_label = call_record.get('_status_label')
            if status_label:
                if status == "completed":
                    status_label.configure(text="✓ Завершено", text_color='#27ae60')
                elif status == "error":
                    status_label.configure(text="✗ Ошибка", text_color='#e74c3c')
            
            # Обновляем результат
            result_label = call_record.get('_result_label')
            if result_label and result:
                # Ограничиваем длину результата
                if len(result) > 200:
                    result = result[:197] + "..."
                result_label.configure(text=f"Результат:\n{result}")
    
    def clear(self):
        """Очистка всех записей."""
        for widget in self.call_widgets:
            widget.destroy()
        self.call_widgets.clear()
        self.tool_calls.clear()


class ProcessWindow(ctk.CTkFrame):
    """
    Основное окно отображения процесса выполнения задач агентом.
    
    Компоненты:
    - Список шагов выполнения (ProcessStep)
    - Панель использования инструментов (ToolUsagePanel)
    - Логи промежуточных сообщений
    """
    
    def __init__(self, master: any, **kwargs):
        if 'fg_color' not in kwargs:
            kwargs['fg_color'] = '#2b2b2b'
        
        super().__init__(master, **kwargs)
        
        # Очередь для потокобезопасных обновлений
        self.update_queue: queue.Queue = queue.Queue()
        
        # Словарь шагов
        self.steps: Dict[str, ProcessStep] = {}
        self.step_widgets: List[ProcessStep] = []
        
        # Создание интерфейса
        self._create_ui()
        
        # Запуск обработчика очереди
        self._process_queue()
    
    def _create_ui(self):
        """Создание пользовательского интерфейса."""
        # Вертикальная прокрутка для всего содержимого
        main_scrollable = ctk.CTkScrollableFrame(
            self,
            fg_color='transparent'
        )
        main_scrollable.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Заголовок
        header = ctk.CTkLabel(
            main_scrollable,
            text="📊 Процесс выполнения",
            font=ctk.CTkFont(size=16, weight='bold'),
            text_color='#ffffff'
        )
        header.pack(fill='x', pady=(10, 15))
        
        # Секция шагов выполнения
        steps_frame = ctk.CTkFrame(main_scrollable, fg_color='#1e1e1e', corner_radius=8)
        steps_frame.pack(fill='x', pady=(0, 10), padx=5)
        
        steps_header = ctk.CTkLabel(
            steps_frame,
            text="📋 Шаги выполнения",
            font=ctk.CTkFont(size=13, weight='bold'),
            text_color='#27ae60'
        )
        steps_header.pack(fill='x', padx=10, pady=(10, 5))
        
        # Контейнер для шагов
        self.steps_container = ctk.CTkFrame(steps_frame, fg_color='transparent')
        self.steps_container.pack(fill='x', padx=10, pady=(0, 10))
        
        # Панель инструментов
        self.tools_panel = ToolUsagePanel(main_scrollable)
        self.tools_panel.pack(fill='both', expand=True, pady=(0, 10), padx=5)
        
        # Секция промежуточных сообщений
        messages_frame = ctk.CTkFrame(main_scrollable, fg_color='#1e1e1e', corner_radius=8)
        messages_frame.pack(fill='both', expand=True, padx=5, pady=(0, 10))
        
        messages_header = ctk.CTkLabel(
            messages_frame,
            text="💬 Промежуточные сообщения",
            font=ctk.CTkFont(size=13, weight='bold'),
            text_color='#9b59b6'
        )
        messages_header.pack(fill='x', padx=10, pady=(10, 5))
        
        # Текстовая область для логов
        self.messages_text = ctk.CTkTextbox(
            messages_frame,
            wrap=tk.WORD,
            font=('Consolas', 10),
            border_width=0,
            fg_color='#2b2b2b',
            text_color='#bdc3c7',
            state='disabled',
            height=10
        )
        self.messages_text.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Кнопка очистки
        clear_btn = ctk.CTkButton(
            self,
            text="🗑️ Очистить",
            command=self.clear,
            width=120,
            fg_color='#e74c3c',
            hover_color='#c0392b'
        )
        clear_btn.pack(pady=(0, 10), padx=10)
    
    def _process_queue(self):
        """Обработка очереди обновлений."""
        try:
            while True:
                task = self.update_queue.get_nowait()
                action = task['action']
                
                if action == 'add_step':
                    self._do_add_step(task['step_id'], task['title'], task.get('details', ''))
                elif action == 'update_step':
                    self._do_update_step(task['step_id'], task['status'], task.get('details', ''))
                elif action == 'add_tool_call':
                    self._do_add_tool_call(task['tool_name'], task['parameters'], task.get('call_id', ''))
                elif action == 'update_tool_call':
                    self._do_update_tool_call(task['call_id'], task['status'], task.get('result', ''))
                elif action == 'add_message':
                    self._do_add_message(task['message'])
                elif action == 'clear':
                    self._do_clear()
                    
        except queue.Empty:
            pass
        
        # Планируем следующий вызов через 50мс
        self.after(50, self._process_queue)
    
    def _do_add_step(self, step_id: str, title: str, details: str = ""):
        """Добавление шага выполнения."""
        step = ProcessStep(
            self.steps_container,
            step_id=step_id,
            title=title,
            details=details,
            status="pending"
        )
        step.pack(fill='x', pady=3)
        self.steps[step_id] = step
        self.step_widgets.append(step)
    
    def _do_update_step(self, step_id: str, status: str, details: str = ""):
        """Обновление статуса шага."""
        if step_id in self.steps:
            self.steps[step_id].set_status(status, details)
    
    def _do_add_tool_call(self, tool_name: str, parameters: Dict[str, Any], call_id: str = ""):
        """Добавление вызова инструмента."""
        return self.tools_panel.add_tool_call(tool_name, parameters, call_id)
    
    def _do_update_tool_call(self, call_id: str, status: str, result: str = ""):
        """Обновление статуса вызова инструмента."""
        self.tools_panel.update_tool_call(call_id, status, result)
    
    def _do_add_message(self, message: str):
        """Добавление промежуточного сообщения."""
        self.messages_text.configure(state='normal')
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.messages_text.insert(tk.END, f"[{timestamp}] {message}\n")
        
        # Автоскролл к концу
        self.messages_text.see(tk.END)
        
        self.messages_text.configure(state='disabled')
    
    def _do_clear(self):
        """Очистка всех данных."""
        # Очищаем шаги
        for step in self.step_widgets:
            step.destroy()
        self.step_widgets.clear()
        self.steps.clear()
        
        # Очищаем инструменты
        self.tools_panel.clear()
        
        # Очищаем сообщения
        self.messages_text.configure(state='normal')
        self.messages_text.delete('1.0', tk.END)
        self.messages_text.configure(state='disabled')
    
    # === Публичные методы ===
    
    def add_step(self, step_id: str, title: str, details: str = ""):
        """
        Добавление нового шага выполнения.
        
        Args:
            step_id: Уникальный идентификатор шага
            title: Заголовок шага
            details: Детали (опционально)
        """
        self.update_queue.put({
            'action': 'add_step',
            'step_id': step_id,
            'title': title,
            'details': details
        })
    
    def update_step(self, step_id: str, status: str, details: str = ""):
        """
        Обновление статуса шага.
        
        Args:
            step_id: Идентификатор шага
            status: Статус (pending, running, completed, error)
            details: Детали (опционально)
        """
        self.update_queue.put({
            'action': 'update_step',
            'step_id': step_id,
            'status': status,
            'details': details
        })
    
    def add_tool_call(self, tool_name: str, parameters: Dict[str, Any], call_id: str = "") -> str:
        """
        Регистрация вызова инструмента.
        
        Args:
            tool_name: Название инструмента
            parameters: Параметры вызова
            call_id: Уникальный идентификатор (генерируется если не указан)
            
        Returns:
            str: Идентификатор вызова
        """
        if not call_id:
            call_id = f"call_{len(self.tools_panel.tool_calls)}_{int(datetime.now().timestamp())}"
        
        self.update_queue.put({
            'action': 'add_tool_call',
            'tool_name': tool_name,
            'parameters': parameters,
            'call_id': call_id
        })
        
        return call_id
    
    def update_tool_call(self, call_id: str, status: str, result: str = ""):
        """
        Обновление статуса вызова инструмента.
        
        Args:
            call_id: Идентификатор вызова
            status: Статус (running, completed, error)
            result: Результат выполнения
        """
        self.update_queue.put({
            'action': 'update_tool_call',
            'call_id': call_id,
            'status': status,
            'result': result
        })
    
    def add_message(self, message: str):
        """
        Добавление промежуточного сообщения.
        
        Args:
            message: Текст сообщения
        """
        self.update_queue.put({
            'action': 'add_message',
            'message': message
        })
    
    def clear(self):
        """Очистка всех данных процесса."""
        self.update_queue.put({'action': 'clear'})
    
    def start_task(self, task_description: str):
        """
        Начало новой задачи.
        
        Args:
            task_description: Описание задачи
        """
        self.add_message(f"Начало задачи: {task_description}")
    
    def end_task(self, success: bool = True, summary: str = ""):
        """
        Завершение задачи.
        
        Args:
            success: True если задача выполнена успешно
            summary: Краткое резюме
        """
        if success:
            self.add_message(f"✓ Задача завершена успешно: {summary}")
        else:
            self.add_message(f"✗ Задача завершена с ошибкой: {summary}")


# Экспорт классов
__all__ = ['ProcessWindow', 'ProcessStep', 'ToolUsagePanel']

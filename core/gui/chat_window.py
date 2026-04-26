"""
Класс ChatWindow для управления областью чата.

Требования:
- CTkScrollableFrame с автоскроллом
- Лимит 200 сообщений
- Динамическое добавление/удаление пузырей
- Потокобезопасное обновление через queue
"""

import customtkinter as ctk
import tkinter as tk
from typing import Optional, Callable, List
from collections import deque
import threading
import queue

from .message_bubble import MessageBubble


class ChatWindow(ctk.CTkScrollableFrame):
    """
    Область чата с прокруткой и управлением сообщениями.
    
    Атрибуты:
        max_messages (int): Максимальное количество сообщений (200)
        message_queue (queue.Queue): Очередь для потокобезопасного обновления
    """
    
    def __init__(
        self,
        master: any,
        on_copy: Optional[Callable[[str], None]] = None,
        max_messages: int = 200,
        **kwargs
    ):
        # Устанавливаем цвета по умолчанию
        if 'fg_color' not in kwargs:
            kwargs['fg_color'] = '#2b2b2b'
        if 'scrollbar_button_color' not in kwargs:
            kwargs['scrollbar_button_color'] = '#555555'
        if 'scrollbar_button_hover_color' not in kwargs:
            kwargs['scrollbar_button_hover_color'] = '#777777'
        
        super().__init__(master, **kwargs)
        
        self.on_copy = on_copy
        self.max_messages = max_messages
        
        # Очередь для потокобезопасных обновлений
        self.message_queue: queue.Queue = queue.Queue()
        
        # Хранилище ссылок на пузыри сообщений
        self._bubbles: deque = deque(maxlen=max_messages)
        
        # Флаг генерации
        self._is_generating = False
        self._stop_event = threading.Event()
        
        # Текущий пузырь для стриминга
        self._current_bubble: Optional[MessageBubble] = None
        
        # Настройка grid для растягивания
        self.grid_columnconfigure(0, weight=1)
        
        # Запуск обработчика очереди
        self._process_queue()
    
    def _process_queue(self):
        """Обработка очереди сообщений (вызывается каждые 50мс)."""
        try:
            while True:
                task = self.message_queue.get_nowait()
                action = task['action']
                
                if action == 'add_message':
                    self._do_add_message(task['text'], task['is_user'])
                elif action == 'update_message':
                    self._do_update_message(task['text'], task['append'])
                elif action == 'add_error':
                    self._do_add_error(task['error'])
                elif action == 'clear':
                    self._do_clear()
                    
        except queue.Empty:
            pass
        
        # Планируем следующий вызов через 50мс
        self.after(50, self._process_queue)
    
    def _do_add_message(self, text: str, is_user: bool):
        """Добавление нового сообщения (внутренняя реализация)."""
        # Проверка лимита
        if len(self._bubbles) >= self.max_messages:
            # Удаляем самое старое сообщение
            old_bubble = self._bubbles.popleft()
            old_bubble.destroy()
        
        # Создание нового пузыря
        bubble = MessageBubble(
            self,
            text=text,
            is_user=is_user,
            on_copy=self.on_copy,
            fg_color='#2b7da0' if is_user else '#3a3a3a',
            corner_radius=12
        )
        
        # Размещение с выравниванием
        sticky = 'e' if is_user else 'w'
        bubble.grid(
            row=len(self._bubbles),
            column=0,
            sticky=sticky,
            padx=5,
            pady=5,
            ipadx=10,
            ipady=5
        )
        
        self._bubbles.append(bubble)
        
        # Автоскролл вниз
        self._scroll_to_bottom()
        
        # Сохраняем ссылку для стриминга если это ИИ
        if not is_user:
            self._current_bubble = bubble
    
    def _do_update_message(self, text: str, append: bool):
        """Обновление текущего сообщения (внутренняя реализация)."""
        if self._current_bubble:
            self._current_bubble.update_text(text, append=append)
            self._scroll_to_bottom()
    
    def _do_add_error(self, error: str):
        """Добавление сообщения об ошибке."""
        self._do_add_message(f"❌ Ошибка: {error}", is_user=False)
    
    def _do_clear(self):
        """Очистка всех сообщений."""
        for bubble in self._bubbles:
            bubble.destroy()
        self._bubbles.clear()
        self._current_bubble = None
    
    def _scroll_to_bottom(self):
        """Прокрутка к последнему сообщению."""
        self._scrollbar.set(1.0, 1.0)
    
    # === Публичные методы для внешнего использования ===
    
    def add_message(self, text: str, is_user: bool):
        """
        Добавление нового сообщения (потокобезопасно).
        
        Args:
            text: Текст сообщения
            is_user: True если сообщение от пользователя
        """
        self.message_queue.put({
            'action': 'add_message',
            'text': text,
            'is_user': is_user
        })
    
    def update_current_message(self, text: str, append: bool = True):
        """
        Обновление текущего сообщения ИИ (потокобезопасно).
        
        Args:
            text: Текст для добавления/обновления
            append: Если True, текст добавляется в конец
        """
        self.message_queue.put({
            'action': 'update_message',
            'text': text,
            'append': append
        })
    
    def add_error(self, error: str):
        """
        Добавление сообщения об ошибке (потокобезопасно).
        
        Args:
            error: Текст ошибки
        """
        self.message_queue.put({
            'action': 'add_error',
            'error': error
        })
    
    def clear(self):
        """Очистка всех сообщений (потокобезопасно)."""
        self.message_queue.put({'action': 'clear'})
    
    def set_generating(self, is_generating: bool):
        """
        Установка флага генерации.
        
        Args:
            is_generating: True если идёт генерация
        """
        self._is_generating = is_generating
        if is_generating:
            self._stop_event.clear()
        else:
            self._stop_event.set()
    
    def stop_generation(self):
        """Сигнал остановки генерации."""
        self._stop_event.set()
    
    def is_generating(self) -> bool:
        """Проверка флага генерации."""
        return self._is_generating
    
    def should_stop(self) -> bool:
        """Проверка флага остановки."""
        return self._stop_event.is_set()
    
    def get_message_count(self) -> int:
        """Получение количества сообщений."""
        return len(self._bubbles)

"""
Класс MessageBubble для отображения сообщений в чате.

Требования:
- Сообщения на всю ширину контейнера (с учётом отступов)
- Динамическая высота на основе содержимого
- Без фиксированных значений высоты в пикселях
- Поддержка форматирования кода (блоки ```)
- Выравнивание: пользователь (вправо), ИИ (влево)
"""

import customtkinter as ctk
import tkinter as tk
from typing import Optional, Callable
import re


class MessageBubble(ctk.CTkFrame):
    """
    Виджет сообщения в чате с динамической высотой и полной шириной.
    
    Атрибуты:
        is_user (bool): True если сообщение от пользователя
        text (str): Текст сообщения
        on_copy (Callable): Callback при копировании текста
    """
    
    def __init__(
        self,
        master: any,
        text: str,
        is_user: bool = False,
        error: bool = False,
        **kwargs
    ):
        # Устанавливаем цвета по умолчанию только если не переданы
        if 'fg_color' not in kwargs:
            if error:
                kwargs['fg_color'] = '#8b0000'  # Тёмно-красный для ошибок
            else:
                kwargs['fg_color'] = '#2b7da0' if is_user else '#3a3a3a'
        if 'corner_radius' not in kwargs:
            kwargs['corner_radius'] = 12
        if 'border_width' not in kwargs:
            kwargs['border_width'] = 0
        
        super().__init__(master, **kwargs)
        
        self.is_user = is_user
        self.text = text
        self._text_widget: Optional[ctk.CTkTextbox] = None
        
        # Конфигурация отступов
        self._padding_x = 10
        self._padding_y = 8
        
        # Настройка grid для растягивания на всю ширину
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Создание текстового виджета
        self._create_text_widget()
        
        # Вставка текста с обработкой кода
        self._insert_formatted_text(text)
        
        # Привязка события копирования
        self._bind_copy_event()
    
    def _create_text_widget(self):
        """Создание и настройка текстового виджета."""
        self._text_widget = ctk.CTkTextbox(
            self,
            wrap=tk.WORD,
            font=('Consolas', 12) if self.is_user else ('Arial', 12),
            border_width=0,
            fg_color='transparent',
            text_color='#ffffff',
            state='disabled' if not self.is_user else 'normal',
            cursor='arrow' if not self.is_user else 'xterm',
        )
        
        # Размещение с отступами
        self._text_widget.grid(
            row=0, 
            column=0, 
            sticky='nsew',
            padx=self._padding_x,
            pady=self._padding_y
        )
        
        # Настройка тегов для форматирования
        self._setup_tags()
    
    def _setup_tags(self):
        """Настройка тегов для подсветки кода."""
        # Получаем доступ к внутреннему tk.Text виджету внутри CTkTextbox
        internal_text = self._text_widget.textbox if hasattr(self._text_widget, 'textbox') else None
        
        if internal_text is None:
            # Fallback: пытаемся найти по имени
            for widget in self._text_widget.winfo_children():
                if isinstance(widget, tk.Text):
                    internal_text = widget
                    break
        
        if internal_text is None:
            return  # Не удалось получить доступ к текстовому виджету
        
        # Тег для блоков кода
        internal_text.tag_configure(
            'code',
            font=('Consolas', 11),
            background='#1e1e1e',
            foreground='#00ff00',
            lmargin1=10,
            lmargin2=10,
            rmargin=10,
            spacing1=5,
            spacing3=5
        )
        
        # Тег для обычного текста
        internal_text.tag_configure(
            'normal',
            font=('Arial', 12),
            foreground='#ffffff'
        )
    
    def _get_internal_text(self):
        """Получить доступ к внутреннему tk.Text виджету."""
        # В customtkinter внутренний виджет называется _textbox
        if hasattr(self._text_widget, '_textbox'):
            return self._text_widget._textbox
        
        # Fallback: ищем среди дочерних виджетов
        for widget in self._text_widget.winfo_children():
            if isinstance(widget, tk.Text):
                return widget
        
        return None
    
    def _insert_formatted_text(self, text: str):
        """
        Вставка текста с обработкой блоков кода.
        
        Блоки кода определяются по ``` и выделяются отдельным тегом.
        """
        internal_text = self._get_internal_text()
        if internal_text is None:
            return
        
        internal_text.configure(state='normal')
        internal_text.delete('1.0', tk.END)
        
        # Разделение текста на блоки кода и обычный текст
        parts = re.split(r'(```[\s\S]*?```)', text)
        
        for part in parts:
            if part.startswith('```') and part.endswith('```'):
                # Блок кода (убираем обратные кавычки)
                code_content = part[3:-3].strip()
                # Удаляем указание языка если есть
                if '\n' in code_content:
                    lang, code = code_content.split('\n', 1)
                    code_content = code
                internal_text.insert(tk.END, code_content + '\n', 'code')
            else:
                # Обычный текст
                internal_text.insert(tk.END, part, 'normal')
        
        internal_text.configure(state='disabled' if not self.is_user else 'normal')
    
    def _bind_copy_event(self):
        """Привязка события двойного клика для копирования."""
        def on_double_click(event):
            # Копирование текста в буфер обмена
            self.clipboard_clear()
            self.clipboard_append(self.text)
        
        self._text_widget.bind('<Double-Button-1>', on_double_click)
    
    def update_text(self, text: str, append: bool = False):
        """
        Обновление текста сообщения.
        
        Args:
            text: Новый текст или добавляемый фрагмент
            append: Если True, текст добавляется в конец
        """
        internal_text = self._get_internal_text()
        if internal_text is None:
            return
        
        if append:
            self.text += text
            internal_text.configure(state='normal')
            # Добавляем текст без тега для производительности (стриминг)
            internal_text.insert(tk.END, text)
            internal_text.see(tk.END)  # Автоскролл к концу
            internal_text.configure(state='disabled' if not self.is_user else 'normal')
        else:
            self.text = text
            self._insert_formatted_text(text)
    
    def append_text(self, text: str):
        """Быстрое добавление текста для стриминга."""
        self.update_text(text, append=True)
    
    def finalize_content(self):
        """Финализация сообщения (переформатирование кода после завершения стриминга)."""
        self._insert_formatted_text(self.text)
    
    def get_height(self) -> int:
        """
        Получение текущей высоты виджета.
        
        Returns:
            int: Высота в пикселях
        """
        return self.winfo_reqheight()
    
    def copy_to_clipboard(self):
        """Копирование текста в буфер обмена."""
        self.clipboard_clear()
        self.clipboard_append(self.text)

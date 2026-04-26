"""
Класс MessageBubble для отображения сообщений в чате.

Требования:
- Сообщения с адаптивной высотой (компактные для короткого текста)
- Динамическая высота на основе содержимого
- Без фиксированных значений высоты в пикселях
- Поддержка форматирования кода (блоки ```)
- Выравнивание: пользователь (вправо), ИИ (влево)
- Контекстное меню для копирования
- Кнопка копирования для блоков кода
"""

import customtkinter as ctk
import tkinter as tk
from typing import Optional, Callable
import re
import tkinter.font as tkfont


class CodeBlockFrame(ctk.CTkFrame):
    """Фрейм для блока кода с кнопкой копирования."""
    
    def __init__(self, master, code: str, language: str = "", **kwargs):
        # Устанавливаем цвета по умолчанию
        if 'fg_color' not in kwargs:
            kwargs['fg_color'] = '#1e1e1e'
        if 'corner_radius' not in kwargs:
            kwargs['corner_radius'] = 6
        
        super().__init__(master, **kwargs)
        
        self.code = code
        self.language = language
        
        # Настройка grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Хедер с языком и кнопкой копирования
        header_frame = ctk.CTkFrame(self, fg_color='#2d2d2d', height=28)
        header_frame.grid(row=0, column=0, sticky='ew', padx=0, pady=(0, 5))
        header_frame.grid_columnconfigure(0, weight=1)
        
        # Название языка
        if language:
            lang_label = ctk.CTkLabel(
                header_frame,
                text=language,
                font=ctk.CTkFont(size=10, weight='bold'),
                text_color='#888888'
            )
            lang_label.grid(row=0, column=0, padx=10, pady=5, sticky='w')
        
        # Кнопка копирования
        copy_btn = ctk.CTkButton(
            header_frame,
            text="📋 Копировать",
            command=self._copy_code,
            width=90,
            height=22,
            font=ctk.CTkFont(size=10),
            fg_color='#3a3a3a',
            hover_color='#4a4a4a'
        )
        copy_btn.grid(row=0, column=1, padx=10, pady=3, sticky='e')
        
        # Текстовый виджет для кода
        self.text_widget = ctk.CTkTextbox(
            self,
            wrap=tk.NONE,
            font=('Consolas', 11),
            border_width=0,
            fg_color='transparent',
            text_color='#00ff00',
            state='disabled',
            cursor='arrow'
        )
        self.text_widget.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)
        
        # Вставка кода
        internal_text = self._get_internal_text()
        if internal_text:
            internal_text.insert('1.0', code)
            # Автовысота на основе количества строк (минимум 2 строки для компактности)
            lines = code.count('\n') + 1
            min_lines = max(lines, 2)  # Минимум 2 строки для однострочного кода
            dynamic_height = min(max(min_lines * 18 + 10, 36), 400)
            self.text_widget.configure(height=dynamic_height // 18)
    
    def _get_internal_text(self):
        """Получить доступ к внутреннему tk.Text виджету."""
        if hasattr(self.text_widget, '_textbox'):
            return self.text_widget._textbox
        for widget in self.text_widget.winfo_children():
            if isinstance(widget, tk.Text):
                return widget
        return None
    
    def _copy_code(self):
        """Копирование кода в буфер обмена."""
        self.clipboard_clear()
        self.clipboard_append(self.code)


class MessageBubble(ctk.CTkFrame):
    """
    Виджет сообщения в чате с адаптивной высотой и динамическим размером.
    
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
        max_width: int = 800,
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
        self.max_width = max_width
        self._text_widget: Optional[ctk.CTkTextbox] = None
        self._code_blocks: list = []  # Ссылки на блоки кода
        
        # Конфигурация отступов
        self._padding_x = 12
        self._padding_y = 10
        
        # Настройка grid для растягивания
        self.grid_columnconfigure(0, weight=0 if not is_user else 1)
        self.grid_rowconfigure(0, weight=1)
        
        # Создание текстового виджета
        self._create_text_widget()
        
        # Вставка текста с обработкой кода
        self._insert_formatted_text(text)
        
        # Привязка события копирования и контекстное меню
        self._bind_copy_event()
        self._create_context_menu()
    
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
            height=1  # Минимальная высота, будет автоподбор
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
        
        Блоки кода определяются по ``` и вставляются как отдельные виджеты CodeBlockFrame.
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
                # Блок кода - извлекаем язык и код
                code_content = part[3:-3].strip()
                language = ""
                if '\n' in code_content:
                    first_line, rest = code_content.split('\n', 1)
                    # Проверяем, является ли первая строка названием языка
                    if first_line.strip() and not first_line.strip().startswith('#') and len(first_line.strip()) < 20:
                        language = first_line.strip()
                        code_content = rest
                
                # Создаём отдельный фрейм для блока кода с кнопкой копирования
                code_frame = CodeBlockFrame(self, code_content, language)
                self._code_blocks.append(code_frame)
                
                # Вставляем как окно в текстовый виджет
                internal_text.window_create(tk.END, window=code_frame)
                internal_text.insert(tk.END, '\n')
            else:
                # Обычный текст
                if part.strip():
                    internal_text.insert(tk.END, part, 'normal')
        
        internal_text.configure(state='disabled' if not self.is_user else 'normal')
        
        # Автоподбор высоты после вставки контента
        self._auto_resize_height()
    
    def _auto_resize_height(self):
        """
        Точный расчёт высоты сообщения на основе содержимого.
        
        Учитывает:
        - Высоту обычного текста (по количеству строк × высоту шрифта)
        - Высоту блоков кода (реальная высота виджетов)
        - Отступы (padding) и межблочные интервалы
        """
        internal_text = self._get_internal_text()
        if internal_text is None:
            return
        
        # Параметры для расчёта
        font_normal = tkfont.Font(family='Arial', size=12)
        font_code = tkfont.Font(family='Consolas', size=11)
        
        line_height_normal = font_normal.metrics('linespace')  # ~15-16px
        line_height_code = font_code.metrics('linespace')      # ~14-15px
        
        total_height_px = 0
        text_line_count = 0
        code_block_count = 0
        
        # Проходим по всем строкам текста (без window_names, который может не работать)
        try:
            total_lines = int(float(internal_text.index('end-1c').split('.')[0]))
            text_line_count = total_lines
        except:
            text_line_count = 1
        
        # Проверяем наличие блоков кода через winfo_children()
        code_block_count = len(self._code_blocks)
        
        # Расчёт высоты текстовой части
        if text_line_count > 0:
            total_height_px += text_line_count * line_height_normal
        
        # Добавляем высоту блоков кода (если они есть)
        for code_block in self._code_blocks:
            if hasattr(code_block, 'winfo_reqheight'):
                code_height = code_block.winfo_reqheight()
                if code_height > 0:
                    total_height_px += code_height
                else:
                    # Если высота ещё не рассчитана, оцениваем по количеству строк
                    code_lines = code_block.code.count('\n') + 1
                    total_height_px += code_lines * line_height_code + 35  # +35 на хедер и отступы
        
        # Добавляем межблочные интервалы
        if code_block_count > 0:
            total_height_px += code_block_count * 5  # spacing1+spacing3
        
        # Минимальная высота для однострочных сообщений
        min_height_px = line_height_normal + self._padding_y * 2
        max_height_px = 800  # Максимум для предотвращения гигантских пузырей
        
        # Ограничиваем диапазон
        total_height_px = max(min_height_px, min(total_height_px, max_height_px))
        
        # Конвертируем пиксели в строки для CTkTextbox
        # height параметр задаётся в строках, поэтому делим на высоту строки
        calculated_lines = max(1, int(total_height_px / line_height_normal))
        
        # Устанавливаем высоту
        self._text_widget.configure(height=calculated_lines)
    
    def _bind_copy_event(self):
        """Привязка события двойного клика для копирования."""
        def on_double_click(event):
            # Копирование текста в буфер обмена
            self.clipboard_clear()
            self.clipboard_append(self.text)
        
        self._text_widget.bind('<Double-Button-1>', on_double_click)
    
    def _create_context_menu(self):
        """Создание контекстного меню для копирования."""
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="📋 Копировать текст", command=self.copy_to_clipboard)
        
        # Привязка правой кнопки мыши
        self._text_widget.bind('<Button-3>', self._show_context_menu)
        self.bind('<Button-3>', self._show_context_menu)
    
    def _show_context_menu(self, event):
        """Показ контекстного меню."""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
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
            # Автоподбор высоты при добавлении текста
            self._auto_resize_height()
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

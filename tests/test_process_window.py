#!/usr/bin/env python3
"""
Демонстрационное приложение для окна отображения процесса.

Показывает работу ProcessWindow с имитацией выполнения задач агентом.
"""

import customtkinter as ctk
import tkinter as tk
from datetime import datetime
import threading
import time

# Импортируем компоненты окна процесса
try:
    from core.gui.process_window import ProcessWindow, ProcessStep, ToolUsagePanel
except ImportError:
    # Если импорты не работают из-за зависимостей, используем прямой импорт
    import sys
    sys.path.insert(0, '/workspace')
    from core.gui.process_window import ProcessWindow, ProcessStep, ToolUsagePanel


class DemoApp(ctk.CTk):
    """Демонстрационное приложение."""
    
    def __init__(self):
        super().__init__()
        
        self.title("DeepAgents - Окно процесса")
        self.geometry("1000x800")
        
        # Настройка темы
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Создание интерфейса
        self._create_ui()
        
        # Планируем запуск демо через 1 секунду
        self.after(1000, self.run_demo)
    
    def _create_ui(self):
        """Создание пользовательского интерфейса."""
        # Верхняя панель с кнопками управления
        control_frame = ctk.CTkFrame(self, height=60)
        control_frame.pack(fill='x', padx=10, pady=(10, 5))
        
        # Кнопка запуска демо
        self.start_btn = ctk.CTkButton(
            control_frame,
            text="▶️ Запустить демо",
            command=self.run_demo,
            width=150,
            fg_color='#27ae60',
            hover_color='#2ecc71'
        )
        self.start_btn.pack(side='left', padx=10, pady=10)
        
        # Кнопка очистки
        self.clear_btn = ctk.CTkButton(
            control_frame,
            text="🗑️ Очистить",
            command=self.clear_process,
            width=120,
            fg_color='#e74c3c',
            hover_color='#c0392b'
        )
        self.clear_btn.pack(side='left', padx=10, pady=10)
        
        # Метка статуса
        self.status_label = ctk.CTkLabel(
            control_frame,
            text="Готов к работе",
            font=ctk.CTkFont(size=12),
            text_color='#7f8c8d'
        )
        self.status_label.pack(side='right', padx=20, pady=10)
        
        # Основное окно процесса
        self.process_window = ProcessWindow(self)
        self.process_window.pack(fill='both', expand=True, padx=10, pady=(5, 10))
    
    def run_demo(self):
        """Запуск демонстрации в отдельном потоке."""
        self.start_btn.configure(state='disabled')
        self.status_label.configure(text="Выполнение демо...", text_color='#3498db')
        
        demo_thread = threading.Thread(target=self._demo_sequence, daemon=True)
        demo_thread.start()
    
    def _demo_sequence(self):
        """Последовательность демонстрационных шагов."""
        # Начало задачи
        self.process_window.start_task("Анализ файлов проекта и создание отчёта")
        
        # Шаг 1: Анализ структуры проекта
        step1_id = "step_1"
        self.process_window.add_step(step1_id, "Анализ структуры проекта")
        time.sleep(0.5)
        
        self.process_window.update_step(step1_id, "running")
        call1 = self.process_window.add_tool_call(
            "list_directory",
            {"path": "/workspace", "recursive": False}
        )
        time.sleep(1)
        
        self.process_window.update_tool_call(
            call1, 
            "completed", 
            "Найдено файлов: 15, директорий: 5"
        )
        self.process_window.update_step(
            step1_id, 
            "completed", 
            "Обнаружено 5 директорий: core, tests, __pycache__, .git, workspace"
        )
        
        # Шаг 2: Чтение конфигурации
        step2_id = "step_2"
        self.process_window.add_step(step2_id, "Чтение конфигурационных файлов")
        time.sleep(0.5)
        
        self.process_window.update_step(step2_id, "running")
        call2 = self.process_window.add_tool_call(
            "read_file",
            {"path": "/workspace/requirements.txt"}
        )
        time.sleep(1.5)
        
        self.process_window.update_tool_call(
            call2,
            "completed",
            "Прочитано 18 строк, найдено зависимостей: 15"
        )
        self.process_window.update_step(
            step2_id,
            "completed",
            "Конфигурация загружена: langchain, customtkinter, pytest..."
        )
        
        # Шаг 3: Веб-поиск (с ошибкой)
        step3_id = "step_3"
        self.process_window.add_step(step3_id, "Поиск дополнительной информации")
        time.sleep(0.5)
        
        self.process_window.update_step(step3_id, "running")
        call3 = self.process_window.add_tool_call(
            "web_search",
            {"query": "langchain agents best practices 2024"}
        )
        time.sleep(1)
        
        self.process_window.update_tool_call(
            call3,
            "error",
            "Ошибка сети: таймаут соединения"
        )
        self.process_window.update_step(
            step3_id,
            "error",
            "Не удалось выполнить поиск: ошибка сети"
        )
        
        # Шаг 4: Математические вычисления
        step4_id = "step_4"
        self.process_window.add_step(step4_id, "Статистический анализ")
        time.sleep(0.5)
        
        self.process_window.update_step(step4_id, "running")
        call4 = self.process_window.add_tool_call(
            "calculate",
            {"expression": "sum([15, 5, 18, 3]) / 4"}
        )
        time.sleep(0.8)
        
        self.process_window.update_tool_call(
            call4,
            "completed",
            "Результат: 10.25"
        )
        self.process_window.update_step(
            step4_id,
            "completed",
            "Среднее значение вычислено: 10.25"
        )
        
        # Шаг 5: Создание отчёта
        step5_id = "step_5"
        self.process_window.add_step(step5_id, "Генерация итогового отчёта")
        time.sleep(0.5)
        
        self.process_window.update_step(step5_id, "running")
        self.process_window.add_message("Формирование структуры отчёта...")
        time.sleep(0.5)
        
        self.process_window.add_message("Добавление раздела 'Структура проекта'...")
        time.sleep(0.5)
        
        self.process_window.add_message("Добавление раздела 'Зависимости'...")
        time.sleep(0.5)
        
        call5 = self.process_window.add_tool_call(
            "write_file",
            {"path": "/workspace/report.md", "content": "# Отчёт...\n\n## Структура..."}
        )
        time.sleep(1)
        
        self.process_window.update_tool_call(
            call5,
            "completed",
            "Файл создан: report.md (256 байт)"
        )
        self.process_window.update_step(
            step5_id,
            "completed",
            "Отчёт сохранён в /workspace/report.md"
        )
        
        # Завершение задачи
        self.process_window.end_task(
            success=True,
            summary="Отчёт создан успешно"
        )
        
        # Возвращаем кнопку в активное состояние
        self.after(0, lambda: self.start_btn.configure(state='normal'))
        self.after(0, lambda: self.status_label.configure(
            text="Демо завершено", 
            text_color='#27ae60'
        ))
    
    def clear_process(self):
        """Очистка окна процесса."""
        self.process_window.clear()
        self.status_label.configure(text="Очищено", text_color='#7f8c8d')


def main():
    """Точка входа приложения."""
    app = DemoApp()
    app.mainloop()


if __name__ == "__main__":
    main()

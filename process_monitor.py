#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Демонстрационное окно отображения процесса выполнения задач агентом.
Включает: шаги процесса, использование инструментов, промежуточные сообщения.
"""

import sys
import time
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QScrollArea, QFrame, 
                             QProgressBar, QPushButton, QGroupBox, QTextEdit)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QColor, QPalette

class ProcessStep(QFrame):
    """Виджет одного шага процесса"""
    def __init__(self, title, description="", parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border-radius: 8px;
                padding: 10px;
                margin: 5px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Заголовок
        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.title_label.setStyleSheet("color: #ffffff;")
        layout.addWidget(self.title_label)
        
        # Описание
        self.desc_label = QLabel(description)
        self.desc_label.setFont(QFont("Arial", 10))
        self.desc_label.setStyleSheet("color: #aaaaaa;")
        self.desc_label.setWordWrap(True)
        layout.addWidget(self.desc_label)
        
        # Индикатор статуса
        self.status_label = QLabel("Ожидание")
        self.status_label.setFont(QFont("Arial", 9))
        self.status_label.setStyleSheet("color: #ffaa00;")
        layout.addWidget(self.status_label)
        
        # Прогресс бар
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Неопределённый прогресс
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: #444444;
                border-radius: 3px;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #ffaa00;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress)
        
        self.set_status("waiting")
    
    def set_status(self, status):
        """Установить статус шага"""
        if status == "waiting":
            self.status_label.setText("⏳ Ожидание")
            self.status_label.setStyleSheet("color: #ffaa00;")
            self.progress.setStyleSheet("""
                QProgressBar { background-color: #444444; border-radius: 3px; height: 8px; }
                QProgressBar::chunk { background-color: #ffaa00; border-radius: 3px; }
            """)
        elif status == "running":
            self.status_label.setText("🔄 Выполняется...")
            self.status_label.setStyleSheet("color: #00aaff;")
            self.progress.setStyleSheet("""
                QProgressBar { background-color: #444444; border-radius: 3px; height: 8px; }
                QProgressBar::chunk { background-color: #00aaff; border-radius: 3px; }
            """)
        elif status == "completed":
            self.status_label.setText("✅ Завершено")
            self.status_label.setStyleSheet("color: #00ff88;")
            self.progress.setRange(0, 100)
            self.progress.setValue(100)
            self.progress.setStyleSheet("""
                QProgressBar { background-color: #444444; border-radius: 3px; height: 8px; }
                QProgressBar::chunk { background-color: #00ff88; border-radius: 3px; }
            """)
        elif status == "error":
            self.status_label.setText("❌ Ошибка")
            self.status_label.setStyleSheet("color: #ff4444;")
            self.progress.setStyleSheet("""
                QProgressBar { background-color: #444444; border-radius: 3px; height: 8px; }
                QProgressBar::chunk { background-color: #ff4444; border-radius: 3px; }
            """)

class ToolUsagePanel(QGroupBox):
    """Панель отображения использования инструментов"""
    def __init__(self, parent=None):
        super().__init__("🛠 Использование инструментов", parent)
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #ffffff;
                border: 2px solid #444444;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        self.tool_log = QTextEdit()
        self.tool_log.setReadOnly(True)
        self.tool_log.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff88;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                border: 1px solid #333333;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.tool_log)
    
    def add_tool_call(self, tool_name, params, result=""):
        """Добавить запись о вызове инструмента"""
        timestamp = time.strftime("%H:%M:%S")
        entry = f"[{timestamp}] 📞 Вызов: {tool_name}\n"
        entry += f"   Параметры: {params}\n"
        if result:
            entry += f"   Результат: {result}\n"
        entry += "-" * 50 + "\n"
        
        self.tool_log.append(entry)
        self.tool_log.verticalScrollBar().setValue(
            self.tool_log.verticalScrollBar().maximum()
        )

class ProcessWindow(QMainWindow):
    """Основное окно отображения процесса"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🤖 Монитор процесса выполнения агента")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
            }
        """)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        header = QLabel("📊 Процесс выполнения задачи")
        header.setFont(QFont("Arial", 18, QFont.Bold))
        header.setStyleSheet("color: #ffffff; padding: 10px;")
        main_layout.addWidget(header)
        
        # Секция шагов процесса
        steps_group = QGroupBox("📋 Шаги процесса")
        steps_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #ffffff;
                border: 2px solid #444444;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        steps_layout = QVBoxLayout(steps_group)
        
        # Скролл для шагов
        self.steps_scroll = QScrollArea()
        self.steps_scroll.setWidgetResizable(True)
        self.steps_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.steps_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        self.steps_container = QWidget()
        self.steps_layout = QVBoxLayout(self.steps_container)
        self.steps_layout.setSpacing(10)
        self.steps_scroll.setWidget(self.steps_container)
        steps_layout.addWidget(self.steps_scroll)
        
        main_layout.addWidget(steps_group, stretch=1)
        
        # Панель инструментов
        self.tool_panel = ToolUsagePanel()
        main_layout.addWidget(self.tool_panel, stretch=1)
        
        # Логи промежуточных сообщений
        messages_group = QGroupBox("💬 Промежуточные сообщения")
        messages_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #ffffff;
                border: 2px solid #444444;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        messages_layout = QVBoxLayout(messages_group)
        
        self.messages_log = QTextEdit()
        self.messages_log.setReadOnly(True)
        self.messages_log.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #aaaaff;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                border: 1px solid #333333;
                border-radius: 4px;
            }
        """)
        messages_layout.addWidget(self.messages_log)
        main_layout.addWidget(messages_group, stretch=1)
        
        # Кнопки управления
        btn_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("🚀 Запустить процесс")
        self.start_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #00aaff;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #0088cc;
            }
            QPushButton:pressed {
                background-color: #006699;
            }
        """)
        self.start_btn.clicked.connect(self.start_process)
        btn_layout.addWidget(self.start_btn)
        
        self.clear_btn = QPushButton("🗑 Очистить")
        self.clear_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #444444;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_logs)
        btn_layout.addWidget(self.clear_btn)
        
        main_layout.addLayout(btn_layout)
        
        # Инициализация шагов
        self.steps = []
        self.init_steps()
    
    def init_steps(self):
        """Инициализировать шаги процесса"""
        step_titles = [
            ("Анализ запроса", "Обработка входных данных и определение намерений"),
            ("Поиск информации", "Поиск релевантных данных в базе знаний"),
            ("Генерация ответа", "Формирование ответа на основе найденной информации"),
            ("Проверка качества", "Валидация ответа на соответствие требованиям"),
            ("Финализация", "Подготовка окончательного результата")
        ]
        
        for title, desc in step_titles:
            step = ProcessStep(title, desc)
            self.steps.append(step)
            self.steps_layout.addWidget(step)
    
    def add_message(self, message):
        """Добавить промежуточное сообщение"""
        timestamp = time.strftime("%H:%M:%S")
        self.messages_log.append(f"[{timestamp}] {message}")
        self.messages_log.verticalScrollBar().setValue(
            self.messages_log.verticalScrollBar().maximum()
        )
    
    def clear_logs(self):
        """Очистить все логи"""
        self.tool_log.clear()
        self.messages_log.clear()
        for step in self.steps:
            step.set_status("waiting")
    
    def start_process(self):
        """Запустить демонстрационный процесс"""
        self.clear_logs()
        self.start_btn.setEnabled(False)
        self.add_message("🚀 Запуск процесса выполнения задачи...")
        
        # Запускаем в отдельном потоке
        thread = threading.Thread(target=self.run_demo_process)
        thread.daemon = True
        thread.start()
    
    def run_demo_process(self):
        """Демонстрационный процесс выполнения"""
        # Шаг 1: Анализ запроса
        self.update_step_status(0, "running")
        self.add_message("🔍 Начало анализа запроса пользователя...")
        time.sleep(1.5)
        self.tool_panel.add_tool_call("NLP_Analyzer", {"text": "пользовательский запрос"}, "намерение: поиск информации")
        self.add_message("✅ Анализ завершён: определено намерение пользователя")
        self.update_step_status(0, "completed")
        
        # Шаг 2: Поиск информации
        self.update_step_status(1, "running")
        self.add_message("🔎 Поиск релевантной информации в базе знаний...")
        time.sleep(2)
        self.tool_panel.add_tool_call("KnowledgeSearch", {"query": "ключевые слова", "limit": 5}, "найдено 3 документа")
        self.add_message("📚 Найдено 3 релевантных документа")
        self.update_step_status(1, "completed")
        
        # Шаг 3: Генерация ответа
        self.update_step_status(2, "running")
        self.add_message("✍️ Генерация ответа на основе найденной информации...")
        time.sleep(2.5)
        self.tool_panel.add_tool_call("ResponseGenerator", {"context": "документы", "style": "формальный"}, "черновик готов")
        self.add_message("📝 Черновик ответа сгенерирован")
        self.update_step_status(2, "completed")
        
        # Шаг 4: Проверка качества
        self.update_step_status(3, "running")
        self.add_message("🔍 Проверка качества сгенерированного ответа...")
        time.sleep(1.5)
        self.tool_panel.add_tool_call("QualityChecker", {"response": "черновик", "criteria": ["точность", "полнота"]}, "оценка: 95%")
        self.add_message("✅ Проверка пройдена: качество ответа 95%")
        self.update_step_status(3, "completed")
        
        # Шаг 5: Финализация
        self.update_step_status(4, "running")
        self.add_message("📦 Финализация и подготовка результата...")
        time.sleep(1)
        self.tool_panel.add_tool_call("Finalizer", {"response": "проверенный черновик"}, "готов к выдаче")
        self.add_message("🎉 Процесс завершён успешно!")
        self.update_step_status(4, "completed")
        
        self.add_message("✅ Все шаги выполнены успешно")
        self.start_btn.setEnabled(True)
    
    def update_step_status(self, step_index, status):
        """Обновить статус шага (потокобезопасно)"""
        def update():
            if 0 <= step_index < len(self.steps):
                self.steps[step_index].set_status(status)
        
        # Используем QTimer для потокобезопасного обновления UI
        QTimer.singleShot(0, update)

def main():
    app = QApplication(sys.argv)
    
    # Устанавливаем тёмную тему
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#121212"))
    palette.setColor(QPalette.WindowText, QColor("#ffffff"))
    palette.setColor(QPalette.Base, QColor("#1e1e1e"))
    palette.setColor(QPalette.AlternateBase, QColor("#2b2b2b"))
    palette.setColor(QPalette.ToolTipBase, QColor("#ffffff"))
    palette.setColor(QPalette.ToolTipText, QColor("#ffffff"))
    palette.setColor(QPalette.Text, QColor("#ffffff"))
    palette.setColor(QPalette.Button, QColor("#2b2b2b"))
    palette.setColor(QPalette.ButtonText, QColor("#ffffff"))
    palette.setColor(QPalette.BrightText, QColor("#00aaff"))
    palette.setColor(QPalette.Link, QColor("#00aaff"))
    palette.setColor(QPalette.Highlight, QColor("#00aaff"))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)
    
    window = ProcessWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

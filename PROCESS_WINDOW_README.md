# Окно отображения процесса (Process Window)

## Обзор

Модуль `process_window.py` предоставляет компоненты для визуализации работы агента в реальном времени в GUI DeepAgents.

## Компоненты

### 1. ProcessWindow

Основной класс для отображения лога событий выполнения агента.

**Функции:**
- Отображение действий агента с временными метками
- Визуализация использования инструментов
- Показ промежуточных сообщений и статуса
- Прокручиваемый лог событий (максимум 500 событий)
- Цветовая индикация типов событий

**Типы событий:**
- `action` (⚡ Синий) - Действия агента
- `tool` (🔧 Фиолетовый) - Использование инструментов
- `message` (💬 Зеленый) - Сообщения
- `info` (ℹ️ Серый) - Информация
- `warning` (⚠️ Оранжевый) - Предупреждения
- `error` (❌ Красный) - Ошибки
- `success` (✅ Темно-зеленый) - Успешное выполнение

**Пример использования:**
```python
from core.gui import ProcessWindow

# Создание
process_window = ProcessWindow(parent, max_events=500)

# Добавление событий
process_window.add_action("Анализ запроса", details="Обработка...")
process_window.add_tool_use(
    tool_name="read_file",
    tool_input={"path": "/file.txt"},
    tool_output="Content..."
)
process_window.add_message("Запрос обработан")
process_window.add_error("Ошибка подключения")
process_window.add_success("Задача выполнена")

# Управление статусом
process_window.set_active(True)  # Запуск
process_window.set_active(False)  # Остановка
process_window.clear()  # Очистка
```

### 2. ToolExecutionPanel

Панель для отображения текущего выполняемого инструмента.

**Функции:**
- Показ названия активного инструмента
- Индикатор прогресса (неопределённый режим)
- Отображение параметров инструмента

**Пример использования:**
```python
from core.gui import ToolExecutionPanel

# Создание
tool_panel = ToolExecutionPanel(parent)

# Начало выполнения
tool_panel.start_tool("read_file", {"path": "/file.txt"})

# Завершение
tool_panel.stop_tool(result="Success")
```

## Интеграция в DeepAgentsGUI

В основном файле `deepagents_gui.py`:

1. **Импорт компонентов:**
```python
from core.gui import ChatWindow, MessageBubble, ProcessWindow, ToolExecutionPanel
```

2. **Создание в `_create_main_area()`:**
```python
# Правая панель для процесса
process_container = ctk.CTkFrame(main_frame, fg_color="#1e1e1e", width=350)
self.process_window = ProcessWindow(process_container, max_events=500)
self.tool_panel = ToolExecutionPanel(process_container)
```

3. **Использование в `_process_message()`:**
```python
# Активация при начале обработки
self.process_window.set_active(True)
self.process_window.add_action("Начало обработки запроса")

# Отслеживание вызовов инструментов
for tc in msg.tool_calls:
    self.process_window.add_action(f"Вызов инструмента: {tc['name']}")
    self.tool_panel.start_tool(tc['name'], tc['args'])

# Завершение
self.process_window.set_active(False)
```

## Потокобезопасность

Все методы обновления UI используют очередь событий (`event_queue`) и вызываются через `after()` для безопасной работы из фоновых потоков.

## Структура файлов

```
/workspace/core/gui/
├── __init__.py           # Экспорт компонентов
├── chat_window.py        # Окно чата
├── message_bubble.py     # Пузыри сообщений
└── process_window.py     # Новый модуль процесса
```

## Тестирование

Запуск тестового приложения:
```bash
python test_process_window.py
```

## Требования

- customtkinter >= 5.0
- Python >= 3.8

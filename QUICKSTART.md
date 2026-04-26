# 🚀 Быстрый старт для Deep Agents GUI

## Для пользователей LM Studio (БЕСПЛАТНО)

### Шаг 1: Установка LM Studio
1. Скачайте LM Studio: https://lmstudio.ai/
2. Установите и запустите программу
3. В разделе "Discover" загрузите модель (рекомендуется Llama 3 или Mistral)
4. Перейдите в раздел "Local Server"
5. Нажмите "Start Server" (порт по умолчанию: 1234)

### Шаг 2: Установка Deep Agents GUI
```bash
# Запустите установку зависимостей
1_install.bat

# Дождитесь завершения установки
```

### Шаг 3: Настройка (НЕ ТРЕБУЕТСЯ для LM Studio!)
По умолчанию проект уже настроен для работы с LM Studio на порту 1234.
Если вы изменили порт, отредактируйте файл `.env`:
```
BASE_URL=http://localhost:ВАШ_ПОРТ/v1
```

### Шаг 4: Проверка системы
```bash
# Запустите тесты
2_run_tests.bat

# Все 40 тестов должны пройти успешно
```

### Шаг 5: Запуск приложения
```bash
# Запустите GUI
4_launch_gui.bat
```

---

## Для пользователей OpenAI API (ПЛАТНО)

### Шаг 1: Получение API ключа
1. Зарегистрируйтесь на https://platform.openai.com/
2. Создайте API ключ: https://platform.openai.com/api-keys
3. Скопируйте ключ (начинается с `sk-`)

### Шаг 2: Установка и настройка
```bash
# Установка
1_install.bat

# Настройка
3_setup_env.bat
# Откройте .env файл и вставьте ваш ключ:
# OPENAI_API_KEY=sk-ваш-ключ-здесь
```

### Шаг 3: Запуск
```bash
# Проверка
2_run_tests.bat

# Запуск GUI
4_launch_gui.bat
```

---

## Для пользователей Ollama

### Шаг 1: Установка Ollama
1. Скачайте Ollama: https://ollama.ai/
2. Установите модель: `ollama pull llama3`
3. Запустите сервер: `ollama serve`

### Шаг 2: Настройка
Отредактируйте `.env`:
```
BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama3
```

### Шаг 3: Запуск
```bash
1_install.bat
2_run_tests.bat
4_launch_gui.bat
```

---

## Структура проекта

```
Deep_Agents_GUI/
├── deepagents/              # Основной пакет
│   ├── tools.py             # Инструменты с валидацией
│   ├── graph.py             # LangGraph StateGraph
│   ├── gui_components.py    # UI компоненты
│   └── gui_integration.py   # Контроллер
├── tests/                   # Тесты (40 тестов)
├── 1_install.bat           # Установка
├── 2_run_tests.bat         # Тесты
├── 3_setup_env.bat         # Настройка
├── 4_launch_gui.bat        # Запуск GUI
├── 5_quick_test.bat        # Быстрый тест
├── 6_cleanup.bat           # Очистка
├── START_HERE.bat          # Главное меню
├── .env.example            # Шаблон конфигурации
└── requirements.txt        # Зависимости
```

---

## Решение проблем

### Ошибка: "ModuleNotFoundError: No module named 'deepagents'"
**Решение:** Запустите `1_install.bat` заново или выполните:
```bash
pip install -e .
```

### Ошибка: "Connection refused" при работе с LM Studio
**Решение:** 
1. Убедитесь, что LM Studio запущен
2. Проверьте, что сервер активен (кнопка "Start Server")
3. Проверьте порт в `.env` (должен совпадать с портом в LM Studio)

### Ошибка: "40 tests failed"
**Решение:** 
1. Удалите папку `venv`
2. Запустите `1_install.bat` заново
3. Убедитесь, что все зависимости установлены

### Ошибка LangSmith (403 Forbidden)
**Решение:** Это нормально без API ключа. LangSmith отключен по умолчанию.
Для включения добавьте в `.env`:
```
LANGSMITH_API_KEY=ваш-ключ
LANGSMITH_TRACING=true
```

---

## Горячие клавиши в GUI

- **Ctrl+N**: Новый диалог
- **Ctrl+S**: Сохранить конфигурацию
- **Ctrl+O**: Загрузить конфигурацию
- **F5**: Обновить состояние
- **Esc**: Закрыть диалог подтверждения

---

## Дополнительные ресурсы

- Документация LangGraph: https://langchain-ai.github.io/langgraph/
- LM Studio Docs: https://lmstudio.ai/docs
- Сообщество: https://github.com/Denstis/Deep_Agents_GUI

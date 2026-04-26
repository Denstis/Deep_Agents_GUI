#!/bin/bash
# Deep Agents GUI - Launch Application Script for macOS/Linux

echo "============================================================"
echo "  Deep Agents GUI: Запуск приложения"
echo "============================================================"
echo ""

# Проверка наличия venv
if [ ! -f "venv/bin/activate" ]; then
    echo "[ОШИБКА] Виртуальное окружение не найдено!"
    echo "Сначала запустите 'bash 1_install.sh'."
    exit 1
fi

# Активация окружения
source venv/bin/activate

# Проверка наличия .env
if [ -f ".env" ]; then
    echo "[OK] Файл .env найден, загрузка переменных окружения..."
    set -a
    source .env
    set +a
else
    echo "[ПРЕДУПРЕЖДЕНИЕ] Файл .env не найден!"
    echo "Убедитесь, что переменные окружения установлены вручную."
    echo "Или запустите 'bash 3_setup_env.sh' для настройки."
    echo ""
    sleep 3
fi

# Проверка ключа OpenAI
if [ -z "$OPENAI_API_KEY" ]; then
    echo "[ОШИБКА] OPENAI_API_KEY не установлен!"
    echo ""
    echo "Запустите 'bash 3_setup_env.sh' для настройки API ключей."
    exit 1
fi

echo "[OK] OPENAI_API_KEY установлен."
if [ -z "$LANGSMITH_API_KEY" ]; then
    echo "[INFO] LANGSMITH_API_KEY не установлен (трассировка отключена)."
else
    echo "[OK] LANGSMITH_API_KEY установлен (трассировка включена)."
fi

echo ""
echo "------------------------------------------------------------"
echo "[INFO] Запуск Deep Agents GUI..."
echo "------------------------------------------------------------"
echo ""

# Запуск основного приложения
python deepagents_gui.py
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "[OK] Приложение завершено нормально."
else
    echo "[ОШИБКА] Приложение завершилось с кодом $EXIT_CODE."
    echo ""
    echo "Возможные причины:"
    echo "- Неверный API ключ OpenAI"
    echo "- Ошибки в коде GUI"
    echo "- Проблемы с совместимостью библиотек"
    echo ""
    echo "Проверьте логи выше для деталей."
fi

echo ""

#!/bin/bash
# Deep Agents GUI - Quick Test Script for macOS/Linux

echo "============================================================"
echo "  Deep Agents GUI: Быстрый демонстрационный тест"
echo "============================================================"
echo ""
echo "Этот скрипт запускает быстрый тест без GUI для проверки:"
echo "- Работы инструментов (Tools Layer)"
echo "- Работы графа агента (Agent Layer)"
echo "- Генерации ответов моделью"
echo ""

# Проверка наличия venv
if [ ! -f "venv/bin/activate" ]; then
    echo "[ОШИБКА] Виртуальное окружение не найдено!"
    echo "Сначала запустите 'bash 1_install.sh'."
    exit 1
fi

# Активация окружения
source venv/bin/activate

# Проверка .env
if [ ! -f ".env" ]; then
    echo "[ПРЕДУПРЕЖДЕНИЕ] Файл .env не найден."
    echo "Тест может завершиться ошибкой без API ключа."
    echo ""
fi

echo "------------------------------------------------------------"
echo "[INFO] Запуск демонстрационного теста..."
echo "------------------------------------------------------------"
echo ""

python -c "import sys; sys.path.insert(0, '.'); from tests.test_gui_integration import run_quick_demo; run_quick_demo()"
EXIT_CODE=$?

echo ""
echo "------------------------------------------------------------"
if [ $EXIT_CODE -eq 0 ]; then
    echo "[OK] Демонстрационный тест завершён успешно!"
    echo ""
    echo "Система готова к работе. Запустите 'bash 4_launch_gui.sh'."
else
    echo "[FAIL] Демонстрационный тест завершился с ошибкой."
    echo ""
    echo "Проверьте:"
    echo "- Установлен ли OPENAI_API_KEY в файле .env"
    echo "- Корректность ключа API"
    echo "- Наличие интернет-соединения"
fi
echo "------------------------------------------------------------"

echo ""

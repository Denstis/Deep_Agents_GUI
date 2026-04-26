#!/bin/bash
# Deep Agents GUI - Installation Script for macOS/Linux

set -e

echo "============================================================"
echo "  Deep Agents GUI: Установка зависимостей (macOS/Linux)"
echo "============================================================"
echo ""

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
    echo "[ОШИБКА] Python3 не найден в системе!"
    echo "Пожалуйста, установите Python 3.10+ через:"
    echo "  macOS: brew install python@3.11"
    echo "  Ubuntu: sudo apt-get install python3 python3-venv python3-pip"
    exit 1
fi

echo "[OK] Python найден:"
python3 --version
echo ""

# Создание виртуального окружения
if [ ! -d "venv" ]; then
    echo "[INFO] Создание виртуального окружения (venv)..."
    python3 -m venv venv
    echo "[OK] Виртуальное окружение создано."
else
    echo "[INFO] Виртуальное окружение уже существует."
fi
echo ""

# Активация и обновление pip
echo "[INFO] Активация окружения и обновление pip..."
source venv/bin/activate
pip install --upgrade pip --quiet

# Установка зависимостей
echo ""
echo "[INFO] Установка необходимых библиотек..."
echo "Это может занять несколько минут..."
echo ""

pip install -r requirements.txt || {
    echo ""
    echo "[ПРЕДУПРЕЖДЕНИЕ] Ошибка установки из requirements.txt"
    echo "Попытка установки базового набора пакетов вручную..."
    pip install langchain langchain-openai langgraph langsmith pydantic pytest customtkinter networkx matplotlib
}

echo ""
echo "============================================================"
echo "  Установка завершена успешно!"
echo "============================================================"
echo ""
echo "Следующие шаги:"
echo "1. Запустите 'bash 2_run_tests.sh' для проверки системы."
echo "2. Настройте переменные окружения (см. .env.example)."
echo "3. Запустите 'bash 4_launch_gui.sh' для работы с интерфейсом."
echo ""

#!/bin/bash
# Deep Agents GUI - Cleanup Script for macOS/Linux

echo "============================================================"
echo "  Deep Agents GUI: Очистка временных файлов"
echo "============================================================"
echo ""

read -p "Вы уверены, что хотите удалить временные файлы? (y/n): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "[INFO] Операция отменена пользователем."
    exit 0
fi

echo ""
echo "[INFO] Удаление временных файлов..."

# Удаление кэша Python
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null && echo "[OK] Удалены __pycache__"
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null && echo "[OK] Удалены .pytest_cache"

# Удаление логов
rm -f *.log && echo "[OK] Удалены файлы *.log"

# Удаление чекпоинтов SQLite
rm -f *.db && echo "[OK] Удалены файлы *.db"
rm -rf checkpoints && echo "[OK] Удалена папка checkpoints"

# Удаление тестовых файлов
rm -rf test_output && echo "[OK] Удалена папка test_output"
rm -rf workspace_files && echo "[OK] Удалена папка workspace_files"

echo ""
echo "------------------------------------------------------------"
read -p "Хотите удалить виртуальное окружение (venv)? Это освободит ~200-500 МБ. (y/n): " DELETE_VENV
if [[ "$DELETE_VENV" =~ ^[Yy]$ ]]; then
    if [ -d "venv" ]; then
        rm -rf venv
        echo "[OK] Виртуальное окружение удалено."
    else
        echo "[INFO] Виртуальное окружение не найдено."
    fi
fi

echo ""
echo "------------------------------------------------------------"
read -p "Хотите удалить файл .env с API ключами? [ПРЕДУПРЕЖДЕНИЕ: это необратимо!] (y/n): " DELETE_ENV
if [[ "$DELETE_ENV" =~ ^[Yy]$ ]]; then
    if [ -f ".env" ]; then
        rm -f .env
        echo "[OK] Файл .env удалён."
    else
        echo "[INFO] Файл .env не найден."
    fi
fi

echo ""
echo "============================================================"
echo "  Очистка завершена!"
echo "============================================================"
echo ""
echo "Для повторного запуска:"
echo "- Если удалили venv: запустите 'bash 1_install.sh'"
echo "- Если удалили .env: запустите 'bash 3_setup_env.sh'"
echo ""

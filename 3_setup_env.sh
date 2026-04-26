#!/bin/bash
# Deep Agents GUI - Setup Environment Script for macOS/Linux

echo "============================================================"
echo "  Deep Agents GUI: Настройка переменных окружения"
echo "============================================================"
echo ""

# Проверка наличия .env.example
if [ -f ".env.example" ]; then
    echo "[INFO] Файл .env.example найден."
    if [ ! -f ".env" ]; then
        echo "[ВОПРОС] Создать файл .env на основе примера? (y/n)"
        read -r CREATE
        if [[ "$CREATE" =~ ^[Yy]$ ]]; then
            cp .env.example .env
            echo "[OK] Файл .env создан."
            echo ""
            echo "[ВАЖНО] Откройте файл .env и заполните следующие поля:"
            echo "  - OPENAI_API_KEY (или другой провайдер)"
            echo "  - LANGSMITH_API_KEY (опционально, для трассировки)"
            echo ""
            echo "Нажмите Enter, чтобы открыть .env в редакторе..."
            read -r
            ${EDITOR:-nano} .env
        else
            echo "[INFO] Пропущено создание .env."
        fi
    else
        echo "[INFO] Файл .env уже существует."
        echo ""
        echo "[ВОПРОС] Открыть .env для редактирования? (y/n)"
        read -r EDIT
        if [[ "$EDIT" =~ ^[Yy]$ ]]; then
            ${EDITOR:-nano} .env
        fi
    fi
else
    echo "[ПРЕДУПРЕЖДЕНИЕ] Файл .env.example не найден."
    echo "Создание базового файла .env..."
    
    cat > .env << 'ENVEOF'
# API ключи для Deep Agents GUI

# OpenAI API Key (обязательно)
# Получите на https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-key-here

# LangSmith API Key (опционально, для трассировки)
# Получите на https://smith.langchain.com
LANGSMITH_API_KEY=your-langsmith-key-here
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=deep-agents-gui

# Рабочая директория для файловых операций
WORKING_DIR=./workspace_files
ENVEOF
    
    echo "[OK] Файл .env создан с базовыми настройками."
    echo ""
    echo "[ВАЖНО] Заполните файл .env вашими API ключами!"
    echo "Нажмите Enter, чтобы открыть .env в редакторе..."
    read -r
    ${EDITOR:-nano} .env
fi

echo ""
echo "============================================================"
echo "  Настройка завершена!"
echo "============================================================"
echo ""
echo "Проверьте, что в файле .env указаны:"
echo "  [V] OPENAI_API_KEY - ваш ключ OpenAI"
echo "  [ ] LANGSMITH_API_KEY - если нужна трассировка (опционально)"
echo ""
echo "После этого запустите 'bash 4_launch_gui.sh'"
echo ""

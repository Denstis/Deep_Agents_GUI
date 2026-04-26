@echo off
chcp 65001 >nul
title Deep Agents GUI - Настройка окружения

echo ============================================================
echo   Deep Agents GUI: Настройка переменных окружения
echo ============================================================
echo.

:: Проверка наличия .env.example
if exist ".env.example" (
    echo [INFO] Файл .env.example найден.
    if not exist ".env" (
        echo [ВОПРОС] Создать файл .env на основе примера?
        set /p CREATE="Введите Y для создания или нажмите Enter для пропуска: "
        if /i "%CREATE%"=="Y" (
            copy .env.example .env >nul
            echo [OK] Файл .env создан.
            echo.
            echo [ВАЖНО] Откройте файл .env и заполните следующие поля:
            echo   - OPENAI_API_KEY (или другой провайдер)
            echo   - LANGSMITH_API_KEY (опционально, для трассировки)
            echo.
            echo Нажмите любую клавишу, чтобы открыть .env в блокноте...
            pause >nul
            notepad .env
        ) else (
            echo [INFO] Пропущено создание .env.
        )
    ) else (
        echo [INFO] Файл .env уже существует.
        echo.
        echo [ВОПРОС] Открыть .env для редактирования?
        set /p EDIT="Введите Y для редактирования или нажмите Enter для пропуска: "
        if /i "%EDIT%"=="Y" (
            notepad .env
        )
    )
) else (
    echo [ПРЕДУПРЕЖДЕНИЕ] Файл .env.example не найден.
    echo Создание базового файла .env...
    
    (
        echo # API ключи для Deep Agents GUI
        echo.
        echo # OpenAI API Key (обязательно)
        echo # Получите на https://platform.openai.com/api-keys
        echo OPENAI_API_KEY=sk-your-key-here
        echo.
        echo # LangSmith API Key (опционально, для трассировки)
        echo # Получите на https://smith.langchain.com
        echo LANGSMITH_API_KEY=your-langsmith-key-here
        echo LANGSMITH_TRACING=true
        echo LANGSMITH_PROJECT=deep-agents-gui
        echo.
        echo # Рабочая директория для файловых операций
        echo WORKING_DIR=./workspace_files
    ) > .env
    
    echo [OK] Файл .env создан с базовыми настройками.
    echo.
    echo [ВАЖНО] Заполните файл .env вашими API ключами!
    echo Нажмите любую клавишу, чтобы открыть .env в блокноте...
    pause >nul
    notepad .env
)

echo.
echo ============================================================
echo   Настройка завершена!
echo ============================================================
echo.
echo Проверьте, что в файле .env указаны:
echo   [V] OPENAI_API_KEY - ваш ключ OpenAI
echo   [ ] LANGSMITH_API_KEY - если нужна трассировка (опционально)
echo.
echo После этого запустите '4_launch_gui.bat'
echo.
pause

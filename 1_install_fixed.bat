@echo off
chcp 65001 >nul
title Deep Agents GUI - Диагностика и установка

echo ============================================================
echo   Deep Agents GUI: Полная диагностика системы
echo ============================================================
echo.

:: Проверка Python
echo [1/6] Проверка Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ОШИБКА] Python не найден!
    echo Установите Python 3.10+ с https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% найден
echo.

:: Проверка текущей директории
echo [2/6] Проверка директории...
if not exist "deepagents" (
    echo [ОШИБКА] Папка 'deepagents' не найдена!
    echo Запустите этот скрипт из корневой папки проекта Deep_Agents_GUI
    echo Текущая директория: %CD%
    pause
    exit /b 1
)
if not exist "tests" (
    echo [ОШИБКА] Папка 'tests' не найдена!
    echo Запустите этот скрипт из корневой папки проекта
    pause
    exit /b 1
)
echo [OK] Директория проекта верна: %CD%
echo.

:: Создание/проверка venv
echo [3/6] Проверка виртуального окружения...
if not exist "venv" (
    echo [INFO] Создание нового venv...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ОШИБКА] Не удалось создать venv
        pause
        exit /b 1
    )
    echo [OK] Venv создан
) else (
    echo [OK] Venv уже существует
)
echo.

:: Активация venv
echo [4/6] Активация виртуального окружения...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ОШИБКА] Не удалось активировать venv
    pause
    exit /b 1
)
echo [OK] Venv активирован
echo.

:: Обновление pip
echo [5/6] Обновление pip...
python -m pip install --upgrade pip >nul 2>&1
echo [OK] Pip обновлён
echo.

:: Установка зависимостей
echo [6/6] Установка зависимостей...
echo Это может занять 2-5 минут, пожалуйста подождите...
echo.

pip install -r requirements.txt > install_log.txt 2>&1
if %errorlevel% neq 0 (
    echo [ВНИМАНИЕ] Ошибки при установке из requirements.txt
    echo Попытка установки основных пакетов...
    pip install langchain langchain-core langchain-openai langgraph langsmith pydantic python-dotenv pytest pytest-asyncio customtkinter networkx matplotlib httpx duckduckgo-search sympy Pillow > install_log2.txt 2>&1
)

:: Проверка ключевых модулей
echo.
echo [ПРОВЕРКА] Тестирование импорта модулей...
python -c "from deepagents.tools import SafeBaseTool; from deepagents.gui_integration import DeepAgentsGUIController; print('[OK] Все модули доступны!')" 2>nul
if %errorlevel% neq 0 (
    echo.
    echo [ОШИБКА] Модули deepagents не найдены!
    echo Возможные причины:
    echo   1. Вы запустили скрипт не из корневой папки проекта
    echo   2. Папка deepagents повреждена
    echo   3. Проблемы с PYTHONPATH
    echo.
    echo Текущая директория: %CD%
    echo Содержимое папки:
    dir /b deepagents 2>nul
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Установка завершена успешно!
echo ============================================================
echo.
echo Следующие шаги:
echo   1. Запустите '2_run_tests.bat' для проверки системы
echo   2. Отредактируйте .env файл (если нужно)
echo   3. Запустите '4_launch_gui.bat' для запуска GUI
echo.
echo Лог установки: install_log.txt
pause

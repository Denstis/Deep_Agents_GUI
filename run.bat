@echo off
REM DeepAgents GUI v2.0 - Launcher
chcp 65001 >nul
echo ============================================
echo   DeepAgents GUI v2.0
echo ============================================
echo.

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Ошибка: Python не найден
    pause
    exit /b 1
)

echo [1/3] Python найден
echo.

REM Создание venv если нет
if not exist "venv" (
    echo [2/3] Создание виртуального окружения...
    python -m venv venv
) else (
    echo [2/3] Виртуальное окружение готово
)
echo.

REM Активация и запуск
echo [3/3] Запуск DeepAgents GUI...
call venv\Scripts\activate.bat
pip install -q customtkinter
python app.py

if errorlevel 1 (
    echo.
    echo Ошибка при запуске
    pause
)

deactivate >nul 2>&1

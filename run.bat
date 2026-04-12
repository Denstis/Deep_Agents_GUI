@echo off
REM DeepAgents GUI Launcher
REM Запуск графического интерфейса DeepAgents

echo Запуск DeepAgents GUI...

REM Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Ошибка: Python не найден. Установите Python 3.8+
    pause
    exit /b 1
)

REM Проверка и установка зависимостей при необходимости
if not exist "requirements.txt" (
    echo Ошибка: requirements.txt не найден
    pause
    exit /b 1
)

REM Установка зависимостей (опционально, если нужно раскомментировать)
REM pip install -r requirements.txt

REM Запуск приложения
python deepagents_gui.py

if errorlevel 1 (
    echo Ошибка при запуске приложения
    pause
)

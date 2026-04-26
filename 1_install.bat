@echo off
chcp 65001 >nul
title Deep Agents GUI - Installation

echo ============================================================
echo   Deep Agents GUI: Установка зависимостей
echo ============================================================
echo.

:: Проверка наличия Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ОШИБКА] Python не найден в системе!
    echo Пожалуйста, установите Python 3.10+ и добавьте его в PATH.
    pause
    exit /b 1
)

echo [OK] Python найден!
for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo %PYTHON_VERSION%
echo.

:: Создание виртуального окружения
if not exist "venv" (
    echo [INFO] Создание виртуального окружения (venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ОШИБКА] Не удалось создать venv.
        pause
        exit /b 1
    )
    echo [OK] Виртуальное окружение создано.
) else (
    echo [INFO] Виртуальное окружение уже существует.
)
echo.

:: Активация и обновление pip
echo [INFO] Активация окружения и обновление pip...
call venv\Scripts\activate.bat

echo [INFO] Обновление pip...
python -m pip install --upgrade pip 2>&1 | findstr /V /C:"Collecting" /C:"Downloading" /C:"Installing" /C:"Successfully"

:: Установка зависимостей
echo.
echo [INFO] Установка необходимых библиотек...
echo Это может занять несколько минут, пожалуйста подождите...
echo.

echo [INFO] Установка из requirements.txt...
pip install -r requirements.txt 2>&1 | findstr /V /C:"Collecting" /C:"Downloading" /C:"Installing" /C:"Successfully" /C:"Requirement already"
if %errorlevel% neq 0 (
    echo.
    echo [ПРЕДУПРЕЖДЕНИЕ] Файл requirements.txt не найден или содержит ошибки.
    echo Попытка установки базового набора пакетов вручную...
    pip install langchain langchain-openai langgraph langsmith pydantic pytest customtkinter python-dotenv networkx matplotlib httpx duckduckgo-search sympy
)

echo.
echo [ПРОВЕРКА] Проверка установленных пакетов...
python -c "import langchain; import langgraph; import pydantic; print('[OK] Все пакеты установлены успешно!')" 2>nul
if %errorlevel% neq 0 (
    echo [ВНИМАНИЕ] Некоторые пакеты могут быть установлены некорректно.
)

echo.
echo ============================================================
echo   Установка завершена успешно!
echo ============================================================
echo.
echo Следующие шаги:
echo 1. Запустите '2_run_tests.bat' для проверки системы.
echo 2. Настройте переменные окружения (.env) для API ключей.
echo 3. Запустите '4_launch_gui.bat' для работы с интерфейсом.
echo.
pause

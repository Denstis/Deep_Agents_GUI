@echo off
REM DeepAgents GUI Launcher
REM Автоматическое создание окружения, клонирование deepagents, установка зависимостей и запуск

chcp 65001 >nul
echo ============================================
echo   DeepAgents GUI - Установка и запуск
echo ============================================
echo.

REM Проверка наличия Git
git --version >nul 2>&1
if errorlevel 1 (
    echo Ошибка: Git не найден. Установите Git.
    pause
    exit /b 1
)

echo [1/5] Git найден...
echo.

REM Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Ошибка: Python не найден. Установите Python 3.8+
    pause
    exit /b 1
)

echo [2/5] Python найден!
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo %PYTHON_VERSION%
echo.

REM Создание виртуального окружения если оно отсутствует
if not exist "venv" (
    echo [3/5] Создание виртуального окружения...
    python -m venv venv
    if errorlevel 1 (
        echo Ошибка при создании виртуального окружения
        pause
        exit /b 1
    )
    echo Виртуальное окружение создано успешно.
) else (
    echo [3/5] Виртуальное окружение уже существует...
)
echo.

REM Активация виртуального окружения
echo [4/5] Активация виртуального окружения и установка зависимостей...
call venv\Scripts\activate.bat

REM Проверка наличия requirements.txt
if not exist "requirements.txt" (
    echo Ошибка: requirements.txt не найден
    pause
    exit /b 1
)

REM Установка зависимостей
echo Установка зависимостей из requirements.txt...
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo Ошибка при установке зависимостей
    pause
    exit /b 1
)

REM Проверка наличия папки deepagents и её содержимого
if exist "deepagents\.git" (
    echo Папка deepagents уже содержит репозиторий.
) else (
    if exist "deepagents" (
        echo Удаление существующей пустой или неполной папки deepagents...
        rmdir /s /q deepagents
    )
    echo Клонирование репозитория deepagents...
    git clone https://github.com/langchain-ai/deepagents.git deepagents
    if errorlevel 1 (
        echo Ошибка при клонировании репозитория
        pause
        exit /b 1
    )
    echo Репозиторий deepagents успешно склонирован.
    
    REM Установка deepagents в режиме разработки
    echo Установка deepagents в режиме разработки...
    cd deepagents
    pip install -e .
    cd ..
)

echo.
echo [5/5] Запуск DeepAgents GUI...
echo ============================================
echo.

REM Запуск приложения
python deepagents_gui.py

if errorlevel 1 (
    echo.
    echo Ошибка при запуске приложения
    pause
)

REM Деактивация виртуального окружения
deactivate >nul 2>&1

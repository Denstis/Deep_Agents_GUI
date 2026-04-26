@echo off
chcp 65001 >nul
title Deep Agents GUI - Быстрый тест (Demo)

echo ============================================================
echo   Deep Agents GUI: Быстрый демонстрационный тест
echo ============================================================
echo.
echo Этот скрипт запускает быстрый тест без GUI для проверки:
echo - Работы инструментов (Tools Layer)
echo - Работы графа агента (Agent Layer)
echo - Генерации ответов моделью
echo.

:: Проверка наличия venv
if not exist "venv\Scripts\activate.bat" (
    echo [ОШИБКА] Виртуальное окружение не найдено!
    echo Сначала запустите '1_install.bat'.
    pause
    exit /b 1
)

:: Активация окружения
call venv\Scripts\activate.bat

:: Проверка .env
if not exist ".env" (
    echo [ПРЕДУПРЕЖДЕНИЕ] Файл .env не найден.
    echo Тест может завершиться ошибкой без API ключа.
    echo.
)

echo ------------------------------------------------------------
echo [INFO] Запуск демонстрационного теста...
echo ------------------------------------------------------------
echo.

python -c "import sys; sys.path.insert(0, '.'); from tests.test_gui_integration import run_quick_demo; run_quick_demo()"

set EXIT_CODE=%errorlevel%

echo.
echo ------------------------------------------------------------
if %EXIT_CODE% equ 0 (
    echo [OK] Демонстрационный тест завершён успешно!
    echo.
    echo Система готова к работе. Запустите '4_launch_gui.bat'.
) else (
    echo [FAIL] Демонстрационный тест завершился с ошибкой.
    echo.
    echo Проверьте:
    echo - Установлен ли OPENAI_API_KEY в файле .env
    echo - Корректность ключа API
    echo - Наличие интернет-соединения
)
echo ------------------------------------------------------------

echo.
pause

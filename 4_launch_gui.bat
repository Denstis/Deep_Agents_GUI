@echo off
chcp 65001 >nul
title Deep Agents GUI - Запуск приложения

echo ============================================================
echo   Deep Agents GUI: Запуск приложения
echo ============================================================
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

:: Загрузка переменных из .env если файл существует
if exist ".env" (
    echo [OK] Файл .env найден, загрузка переменных окружения...
    for /f "tokens=1,* delims==" %%a in ('findstr /r /c:"^[^#].*=" .env') do (
        set "%%a=%%b"
    )
) else (
    echo [INFO] Файл .env не найден, используются переменные системы.
)

:: Проверка ключа OpenAI или LM Studio
if "%OPENAI_API_KEY%"=="" if "%LM_STUDIO_API_BASE%"=="" (
    echo [ОШИБКА] Ни OPENAI_API_KEY, ни LM_STUDIO_API_BASE не установлены!
    echo.
    echo Запустите '3_setup_env.bat' для настройки API ключей.
    echo Или настройте LM Studio в интерфейсе приложения.
    pause
    exit /b 1
)

if not "%OPENAI_API_KEY%"=="" (
    echo [OK] OPENAI_API_KEY установлен.
)
if not "%LM_STUDIO_API_BASE%"=="" (
    echo [OK] LM_STUDIO_API_BASE установлен: %LM_STUDIO_API_BASE%
)
if "%OPENAI_API_KEY%"=="" if not "%LM_STUDIO_API_BASE%"=="" (
    echo [INFO] Режим LM Studio активирован.
)

if "%LANGSMITH_API_KEY%"=="" (
    echo [INFO] LANGSMITH_API_KEY не установлен (трассировка отключена).
) else (
    echo [OK] LANGSMITH_API_KEY установлен (трассировка включена).
)

echo.
echo ------------------------------------------------------------
echo [INFO] Запуск Deep Agents GUI...
echo ------------------------------------------------------------
echo.

:: Запуск основного приложения
python deepagents_gui.py

:: Обработка ошибок запуска
set EXIT_CODE=%errorlevel%

echo.
if %EXIT_CODE% equ 0 (
    echo [OK] Приложение завершено нормально.
) else (
    echo [ОШИБКА] Приложение завершилось с кодом %EXIT_CODE%.
    echo.
    echo Возможные причины:
    echo - Неверный API ключ OpenAI
    echo - Ошибки в коде GUI
    echo - Проблемы с совместимостью библиотек
    echo.
    echo Проверьте логи выше для деталей.
)

echo.
pause

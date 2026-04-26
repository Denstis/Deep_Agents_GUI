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

:: Проверка наличия .env
if exist ".env" (
    echo [OK] Файл .env найден, загрузка переменных окружения...
    for /f "delims=" %%a in (.env) do (
        echo %%a | findstr /r /c:"^[^#].*=" >nul && (
            for /f "tokens=1,* delims==" %%b in ("%%a") do (
                set "%%b=%%c"
            )
        )
    )
) else (
    echo [ПРЕДУПРЕЖДЕНИЕ] Файл .env не найден!
    echo Убедитесь, что переменные окружения установлены вручную.
    echo Или запустите '3_setup_env.bat' для настройки.
    echo.
    timeout /t 3 /nobreak >nul
)

:: Проверка ключа OpenAI
if "%OPENAI_API_KEY%"=="" (
    if "%OPENAI_API_KEY%"=="" (
        echo [ОШИБКА] OPENAI_API_KEY не установлен!
        echo.
        echo Запустите '3_setup_env.bat' для настройки API ключей.
        pause
        exit /b 1
    )
)

echo [OK] OPENAI_API_KEY установлен.
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

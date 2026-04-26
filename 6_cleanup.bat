@echo off
chcp 65001 >nul
title Deep Agents GUI - Очистка

echo ============================================================
echo   Deep Agents GUI: Очистка временных файлов
echo ============================================================
echo.

set /p CONFIRM="Вы уверены, что хотите удалить временные файлы? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo [INFO] Операция отменена пользователем.
    pause
    exit /b 0
)

echo.
echo [INFO] Удаление временных файлов...

:: Удаление кэша Python
if exist "__pycache__" (
    rmdir /s /q __pycache__
    echo [OK] Удалён __pycache__
)

if exist "deepagents\__pycache__" (
    rmdir /s /q deepagents\__pycache__
    echo [OK] Удалён deepagents\__pycache__
)

if exist "tests\__pycache__" (
    rmdir /s /q tests\__pycache__
    echo [OK] Удалён tests\__pycache__
)

:: Удаление файлов pytest
if exist ".pytest_cache" (
    rmdir /s /q .pytest_cache
    echo [OK] Удалён .pytest_cache
)

:: Удаление логов
if exist "*.log" (
    del /q *.log
    echo [OK] Удалены файлы *.log
)

:: Удаление чекпоинтов SQLite (если есть)
if exist "*.db" (
    del /q *.db
    echo [OK] Удалены файлы *.db
)

if exist "checkpoints" (
    rmdir /s /q checkpoints
    echo [OK] Удалена папка checkpoints
)

:: Удаление тестовых файлов
if exist "test_output" (
    rmdir /s /q test_output
    echo [OK] Удалена папка test_output
)

if exist "workspace_files" (
    rmdir /s /q workspace_files
    echo [OK] Удалена папка workspace_files
)

echo.
echo ------------------------------------------------------------
echo [ВОПРОС] Хотите удалить виртуальное окружение (venv)?
echo Это освободит ~200-500 МБ, но потребует повторной установки.
set /p DELETE_VENV="Удалить venv? (Y/N): "
if /i "%DELETE_VENV%"=="Y" (
    if exist "venv" (
        rmdir /s /q venv
        echo [OK] Виртуальное окружение удалено.
    ) else (
        echo [INFO] Виртуальное окружение не найдено.
    )
)

echo.
echo ------------------------------------------------------------
echo [ВОПРОС] Хотите удалить файл .env с API ключами?
echo [ПРЕДУПРЕЖДЕНИЕ] Это удалит ваши ключи безвозвратно!
set /p DELETE_ENV="Удалить .env? (Y/N): "
if /i "%DELETE_ENV%"=="Y" (
    if exist ".env" (
        del /q .env
        echo [OK] Файл .env удалён.
    ) else (
        echo [INFO] Файл .env не найден.
    )
)

echo.
echo ============================================================
echo   Очистка завершена!
echo ============================================================
echo.
echo Для повторного запуска:
echo - Если удалили venv: запустите '1_install.bat'
echo - Если удалили .env: запустите '3_setup_env.bat'
echo.
pause

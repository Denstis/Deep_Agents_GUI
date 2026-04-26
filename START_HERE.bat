@echo off
chcp 65001 >nul
title Deep Agents GUI - Главное меню

:MENU
cls
echo ============================================================
echo        Deep Agents GUI - Главное меню запуска
echo ============================================================
echo.
echo Выберите действие:
echo.
echo   [1] Установка зависимостей (первый запуск)
echo   [2] Запуск всех тестов (проверка системы)
echo   [3] Настройка переменных окружения (.env)
echo   [4] Запуск приложения (GUI)
echo   [5] Быстрый демонстрационный тест
echo   [6] Очистка временных файлов
echo   [7] Открыть документацию
echo   [0] Выход
echo.
echo ============================================================
echo.

set /p CHOICE="Введите номер действия (0-7): "

if "%CHOICE%"=="1" goto INSTALL
if "%CHOICE%"=="2" goto TESTS
if "%CHOICE%"=="3" goto SETUP
if "%CHOICE%"=="4" goto LAUNCH
if "%CHOICE%"=="5" goto QUICKTEST
if "%CHOICE%"=="6" goto CLEANUP
if "%CHOICE%"=="7" goto DOCS
if "%CHOICE%"=="0" goto EXIT

echo [ОШИБКА] Неверный выбор. Попробуйте снова.
timeout /t 2 /nobreak >nul
goto MENU

:INSTALL
cls
call 1_install.bat
goto MENU

:TESTS
cls
call 2_run_tests.bat
goto MENU

:SETUP
cls
call 3_setup_env.bat
goto MENU

:LAUNCH
cls
call 4_launch_gui.bat
goto MENU

:QUICKTEST
cls
call 5_quick_test.bat
goto MENU

:CLEANUP
cls
call 6_cleanup.bat
goto MENU

:DOCS
cls
echo ============================================================
echo   Документация Deep Agents GUI
echo ============================================================
echo.

if exist "README.md" (
    echo [INFO] Открытие README.md...
    notepad README.md
) else if exist "INTEGRATION_GUIDE.md" (
    echo [INFO] Файл README.md не найден. Открытие INTEGRATION_GUIDE.md...
    notepad INTEGRATION_GUIDE.md
) else if exist "FINAL_SUMMARY.md" (
    echo [INFO] Файлы README.md и INTEGRATION_GUIDE.md не найдены.
    echo Открытие FINAL_SUMMARY.md...
    notepad FINAL_SUMMARY.md
) else (
    echo [ПРЕДУПРЕЖДЕНИЕ] Файлы документации не найдены!
    echo.
    echo Основная информация содержится в этом файле (START_HERE.bat).
    echo.
    echo Краткое руководство:
    echo 1. Запустите пункт 1 для установки зависимостей
    echo 2. Запустите пункт 3 для настройки API ключей
    echo 3. Запустите пункт 2 для проверки системы
    echo 4. Запустите пункт 4 для работы с GUI
)

goto MENU

:EXIT
cls
echo.
echo Спасибо за использование Deep Agents GUI!
echo.
timeout /t 2 /nobreak >nul
exit /b 0

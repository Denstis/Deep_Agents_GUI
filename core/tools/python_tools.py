"""
Инструменты для работы с Python: установка зависимостей, выполнение скриптов, отладка.
"""

import subprocess
import sys
import os
import tempfile
import json
from typing import Optional, Dict, Any
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class PipInstallInput(BaseModel):
    """Входные данные для установки пакетов."""
    packages: str = Field(..., description="Список пакетов для установки (например, 'requests pandas' или 'numpy==1.24.0')")
    upgrade: bool = Field(default=False, description="Обновить пакеты до последних версий")
    user: bool = Field(default=True, description="Установить в пользовательскую директорию (без прав администратора)")
    quiet: bool = Field(default=False, description="Тихий режим вывода")


class PipInstallTool(BaseTool):
    """Инструмент для установки Python пакетов через pip."""
    name: str = "pip_install"
    description: str = """
    Устанавливает Python пакеты через pip.
    Используйте для установки библиотек, необходимых для выполнения скрипта.
    Поддерживает установку нескольких пакетов одновременно.
    Автоматически использует --user флаг для установки без прав администратора.
    
    Входные данные: строка с именами пакетов (можно с версиями).
    Пример: "requests pandas numpy==1.24.0"
    """
    args_schema: type[BaseModel] = PipInstallInput

    def _run(
        self,
        packages: str,
        upgrade: bool = False,
        user: bool = True,
        quiet: bool = False
    ) -> str:
        """Выполняет установку пакетов."""
        cmd = [sys.executable, "-m", "pip", "install"]
        
        if upgrade:
            cmd.append("--upgrade")
        if user:
            cmd.append("--user")
        if quiet:
            cmd.append("--quiet")
        
        # Разбиваем строку пакетов на список
        package_list = packages.strip().split()
        cmd.extend(package_list)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 минут на установку
                encoding='utf-8',
                errors='replace'
            )
            
            output = []
            if result.stdout:
                output.append("STDOUT:\n" + result.stdout)
            if result.stderr:
                output.append("STDERR:\n" + result.stderr)
            
            if result.returncode == 0:
                return f"Успешно установлено: {packages}\n\n" + "\n".join(output)
            else:
                return f"Ошибка при установке пакетов: {packages}\nКод возврата: {result.returncode}\n\n" + "\n".join(output)
                
        except subprocess.TimeoutExpired:
            return f"Превышено время ожидания при установке пакетов: {packages}"
        except Exception as e:
            return f"Исключение при установке пакетов: {str(e)}"

    async def _arun(self, **kwargs: Any) -> str:
        """Асинхронная версия (не реализована, используется синхронная)."""
        return self._run(**kwargs)


class RunPythonScriptInput(BaseModel):
    """Входные данные для выполнения Python скрипта."""
    code: str = Field(..., description="Код Python для выполнения")
    working_directory: Optional[str] = Field(default=None, description="Рабочая директория для выполнения скрипта")
    timeout: int = Field(default=60, description="Таймаут выполнения в секундах")
    arguments: Optional[str] = Field(default=None, description="Аргументы командной строки для скрипта")


class RunPythonScriptTool(BaseTool):
    """Инструмент для выполнения Python кода."""
    name: str = "run_python_script"
    description: str = """
    Выполняет предоставленный код Python как скрипт.
    Полезно для тестирования кода, выполнения вычислений, обработки данных.
    Код выполняется в изолированном временном файле.
    
    Возвращает: вывод скрипта (stdout), ошибки (stderr) и код возврата.
    """
    args_schema: type[BaseModel] = RunPythonScriptInput

    def _run(
        self,
        code: str,
        working_directory: Optional[str] = None,
        timeout: int = 60,
        arguments: Optional[str] = None
    ) -> str:
        """Выполняет Python код."""
        # Создаем временный файл для скрипта
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(code)
            script_path = f.name
        
        try:
            cmd = [sys.executable, script_path]
            
            # Добавляем аргументы если есть
            if arguments:
                cmd.extend(arguments.split())
            
            # Определяем рабочую директорию
            cwd = working_directory if working_directory else os.getcwd()
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
                encoding='utf-8',
                errors='replace',
                env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
            )
            
            output_parts = []
            
            if result.stdout:
                output_parts.append(f"=== ВЫВОД (STDOUT) ===\n{result.stdout}")
            
            if result.stderr:
                output_parts.append(f"=== ОШИБКИ (STDERR) ===\n{result.stderr}")
            
            output_parts.append(f"=== КОД ВОЗВРАТА: {result.returncode} ===")
            
            return "\n\n".join(output_parts)
            
        except subprocess.TimeoutExpired:
            return f"Превышено время выполнения скрипта ({timeout} сек). Скрипт был остановлен."
        except FileNotFoundError as e:
            return f"Ошибка: файл или директория не найдены - {str(e)}"
        except Exception as e:
            return f"Исключение при выполнении скрипта: {type(e).__name__}: {str(e)}"
        finally:
            # Удаляем временный файл
            if os.path.exists(script_path):
                try:
                    os.unlink(script_path)
                except:
                    pass

    async def _arun(self, **kwargs: Any) -> str:
        """Асинхронная версия."""
        return self._run(**kwargs)


class CheckPythonSyntaxInput(BaseModel):
    """Входные данные для проверки синтаксиса."""
    code: str = Field(..., description="Код Python для проверки синтаксиса")


class CheckPythonSyntaxTool(BaseTool):
    """Инструмент для проверки синтаксиса Python кода."""
    name: str = "check_python_syntax"
    description: str = """
    Проверяет синтаксическую корректность кода Python без его выполнения.
    Полезно для отладки перед запуском скрипта.
    Возвращает информацию об ошибках синтаксиса если они есть.
    """
    args_schema: type[BaseModel] = CheckPythonSyntaxInput

    def _run(self, code: str) -> str:
        """Проверяет синтаксис кода."""
        try:
            compile(code, '<string>', 'exec')
            return "✓ Синтаксис корректен. Ошибок не обнаружено."
        except SyntaxError as e:
            error_msg = (
                f"✗ Обнаружена синтаксическая ошибка:\n"
                f"  Тип ошибки: {type(e).__name__}\n"
                f"  Сообщение: {e.msg}\n"
                f"  Строка: {e.lineno}\n"
                f"  Позиция: {e.offset}\n"
                f"  Текст строки: {e.text}"
            )
            return error_msg
        except Exception as e:
            return f"Неожиданная ошибка при проверке: {type(e).__name__}: {str(e)}"

    async def _arun(self, **kwargs: Any) -> str:
        """Асинхронная версия."""
        return self._run(**kwargs)


class FormatPythonCodeInput(BaseModel):
    """Входные данные для форматирования кода."""
    code: str = Field(..., description="Код Python для форматирования")


class FormatPythonCodeTool(BaseTool):
    """Инструмент для форматирования Python кода."""
    name: str = "format_python_code"
    description: str = """
    Форматирует код Python согласно PEP 8.
    Использует встроенный модуль ast для парсинга и генерации отформатированного кода.
    Если код содержит синтаксические ошибки, вернет сообщение об ошибке.
    """
    args_schema: type[BaseModel] = FormatPythonCodeInput

    def _run(self, code: str) -> str:
        """Форматирует код Python."""
        try:
            # Пробуем распарсить код
            tree = compile(code, '<string>', 'exec', flags=ast.PyCF_ONLY_AST)
            
            # Для простого форматирования используем unparse (Python 3.9+)
            import ast
            try:
                formatted = ast.unparse(ast.parse(code))
                return f"=== ОРИГИНАЛЬНЫЙ КОД ===\n{code}\n\n=== ОТФОРМАТИРОВАННЫЙ КОД ===\n{formatted}"
            except AttributeError:
                # Если ast.unparse недоступен (Python < 3.9)
                return "Форматирование недоступно в этой версии Python. Используйте внешние инструменты (black, autopep8)."
                
        except SyntaxError as e:
            return f"Невозможно отформатировать код из-за синтаксической ошибки: {e}"
        except Exception as e:
            return f"Ошибка при форматировании: {type(e).__name__}: {str(e)}"

    async def _arun(self, **kwargs: Any) -> str:
        """Асинхронная версия."""
        return self._run(**kwargs)


# Импорт ast в начале файла для format_python_code
import ast


def get_python_tools() -> list:
    """Возвращает список всех инструментов для работы с Python."""
    return [
        PipInstallTool(),
        RunPythonScriptTool(),
        CheckPythonSyntaxTool(),
        FormatPythonCodeTool(),
    ]


if __name__ == "__main__":
    # Тестирование инструментов
    print("Тестирование инструментов Python...\n")
    
    # Тест 1: Проверка синтаксиса
    print("1. Проверка синтаксиса:")
    syntax_tool = CheckPythonSyntaxTool()
    result = syntax_tool.invoke({"code": "print('Hello')\nx = 5"})
    print(result)
    print()
    
    # Тест 2: Ошибка синтаксиса
    print("2. Проверка с ошибкой синтаксиса:")
    result = syntax_tool.invoke({"code": "print('Hello'\nx = 5"})  #Missing )
    print(result)
    print()
    
    # Тест 3: Выполнение скрипта
    print("3. Выполнение скрипта:")
    run_tool = RunPythonScriptTool()
    code = """
import sys
print(f"Python version: {sys.version}")
for i in range(3):
    print(f"Count: {i}")
"""
    result = run_tool.invoke({"code": code, "timeout": 10})
    print(result)
    print()
    
    # Тест 4: Установка пакета (тестовый режим - не устанавливаем реально)
    print("4. Инструмент pip_install создан:")
    pip_tool = PipInstallTool()
    print(f"   Name: {pip_tool.name}")
    print(f"   Description: {pip_tool.description[:100]}...")
    print()
    
    print("Все тесты завершены!")

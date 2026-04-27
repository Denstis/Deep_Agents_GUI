"""
Real Tool Implementations - LangChain Compatible Tools
Production-ready tools with actual functionality, not simulations.
"""
import os
import sys
import subprocess
import json
import re
import requests
from typing import Any, Dict, List, Optional, Type
from pathlib import Path
import asyncio
import threading

from langchain_core.tools import BaseTool, Tool
from pydantic import BaseModel, Field


# ============== File System Tools ==============

class FileSystemReadInput(BaseModel):
    path: str = Field(description="File path to read")
    max_lines: int = Field(default=100, description="Maximum lines to read")

class FileSystemReadTool(BaseTool):
    name = "file_read"
    description = "Read contents of a file from the filesystem"
    args_schema: Type[BaseModel] = FileSystemReadInput
    
    def _run(self, path: str, max_lines: int = 100) -> str:
        try:
            file_path = Path(path).expanduser().resolve()
            
            # Security check - prevent accessing files outside workspace
            workspace = Path(os.getcwd())
            try:
                file_path.relative_to(workspace)
            except ValueError:
                # Allow home directory access for config files
                if not str(file_path).startswith(os.path.expanduser("~")):
                    return f"Error: Access denied. Path must be within workspace or home directory."
            
            if not file_path.exists():
                return f"Error: File not found: {path}"
            
            if not file_path.is_file():
                return f"Error: Not a file: {path}"
            
            # Read file
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
                
            content = ''.join(lines[:max_lines])
            truncated = len(lines) > max_lines
            
            result = f"File: {path}\n{'='*50}\n{content}"
            if truncated:
                result += f"\n... (truncated, showing {max_lines} of {len(lines)} lines)"
            
            return result
            
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    async def _arun(self, path: str, max_lines: int = 100) -> str:
        return self._run(path, max_lines)


class FileSystemWriteInput(BaseModel):
    path: str = Field(description="File path to write")
    content: str = Field(description="Content to write to file")
    append: bool = Field(default=False, description="Append to file instead of overwriting")

class FileSystemWriteTool(BaseTool):
    name = "file_write"
    description = "Write content to a file on the filesystem"
    args_schema: Type[BaseModel] = FileSystemWriteInput
    
    def _run(self, path: str, content: str, append: bool = False) -> str:
        try:
            file_path = Path(path).expanduser().resolve()
            
            # Security check
            workspace = Path(os.getcwd())
            try:
                file_path.relative_to(workspace)
            except ValueError:
                if not str(file_path).startswith(os.path.expanduser("~")):
                    return f"Error: Access denied. Cannot write outside workspace."
            
            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            mode = 'a' if append else 'w'
            with open(file_path, mode, encoding='utf-8') as f:
                f.write(content)
            
            return f"Successfully wrote {len(content)} characters to {path}"
            
        except Exception as e:
            return f"Error writing file: {str(e)}"
    
    async def _arun(self, path: str, content: str, append: bool = False) -> str:
        return self._run(path, content, append)


class FileSystemListInput(BaseModel):
    path: str = Field(default=".", description="Directory path to list")
    recursive: bool = Field(default=False, description="List recursively")

class FileSystemListTool(BaseTool):
    name = "file_list"
    description = "List files and directories in a given path"
    args_schema: Type[BaseModel] = FileSystemListInput
    
    def _run(self, path: str = ".", recursive: bool = False) -> str:
        try:
            dir_path = Path(path).expanduser().resolve()
            
            if not dir_path.exists():
                return f"Error: Directory not found: {path}"
            
            if not dir_path.is_dir():
                return f"Error: Not a directory: {path}"
            
            result = f"Directory: {path}\n{'='*50}\n"
            
            if recursive:
                items = []
                for root, dirs, files in os.walk(dir_path):
                    level = root.replace(str(dir_path), '').count(os.sep)
                    indent = '  ' * level
                    items.append(f"{indent}[DIR] {os.path.basename(root)}/")
                    sub_indent = '  ' * (level + 1)
                    for file in files[:50]:  # Limit files
                        items.append(f"{sub_indent}{file}")
                result += '\n'.join(items[:200])  # Limit total output
            else:
                items = sorted(dir_path.iterdir(), key=lambda x: (x.is_file(), x.name))
                for item in items[:50]:  # Limit to 50 items
                    icon = "[FILE]" if item.is_file() else "[DIR] "
                    result += f"{icon} {item.name}\n"
            
            return result
            
        except Exception as e:
            return f"Error listing directory: {str(e)}"
    
    async def _arun(self, path: str = ".", recursive: bool = False) -> str:
        return self._run(path, recursive)


# ============== Console/Shell Tools ==============

class ConsoleExecuteInput(BaseModel):
    command: str = Field(description="Shell command to execute")
    timeout: int = Field(default=30, description="Execution timeout in seconds")
    shell: bool = Field(default=True, description="Run in shell")

class ConsoleExecuteTool(BaseTool):
    name = "console_execute"
    description = "Execute a shell/command line command and return output"
    args_schema: Type[BaseModel] = ConsoleExecuteInput
    
    def _run(self, command: str, timeout: int = 30, shell: bool = True) -> str:
        # Security: Block dangerous commands
        dangerous_patterns = ['rm -rf /', 'format', 'del /s', 'sudo rm', ':(){:|:&};:']
        for pattern in dangerous_patterns:
            if pattern in command.lower():
                return f"Error: Dangerous command blocked: {pattern}"
        
        try:
            process = subprocess.Popen(
                command,
                shell=shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.getcwd()
            )
            
            try:
                stdout, stderr = process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                return f"Error: Command timed out after {timeout} seconds"
            
            result = ""
            if stdout:
                result += f"STDOUT:\n{stdout}\n"
            if stderr:
                result += f"STDERR:\n{stderr}\n"
            result += f"Exit code: {process.returncode}"
            
            return result.strip() or "Command executed successfully (no output)"
            
        except Exception as e:
            return f"Error executing command: {str(e)}"
    
    async def _arun(self, command: str, timeout: int = 30, shell: bool = True) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._run, command, timeout, shell)


# ============== Web Tools ==============

class WebSearchInput(BaseModel):
    query: str = Field(description="Search query")
    num_results: int = Field(default=5, description="Number of results to return")

class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web using DuckDuckGo"
    args_schema: Type[BaseModel] = WebSearchInput
    
    def _run(self, query: str, num_results: int = 5) -> str:
        try:
            # Use DuckDuckGo search API
            from duckduckgo_search import DDGS
            
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=num_results))
            
            if not results:
                return "No results found"
            
            formatted = []
            for i, r in enumerate(results, 1):
                formatted.append(f"{i}. {r.get('title', 'N/A')}\n   {r.get('body', 'N/A')}\n   URL: {r.get('href', 'N/A')}\n")
            
            return f"Search results for '{query}':\n{'='*50}\n" + '\n'.join(formatted)
            
        except ImportError:
            return "Error: duckduckgo-search not installed. Run: pip install duckduckgo-search"
        except Exception as e:
            return f"Error searching web: {str(e)}"
    
    async def _arun(self, query: str, num_results: int = 5) -> str:
        return self._run(query, num_results)


class WebFetchInput(BaseModel):
    url: str = Field(description="URL to fetch")
    timeout: int = Field(default=10, description="Request timeout")

class WebFetchTool(BaseTool):
    name = "web_fetch"
    description = "Fetch content from a URL"
    args_schema: Type[BaseModel] = WebFetchInput
    
    def _run(self, url: str, timeout: int = 10) -> str:
        try:
            # Validate URL
            if not url.startswith(('http://', 'https://')):
                return "Error: Invalid URL. Must start with http:// or https://"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (DeepAgents Bot)'
            }
            
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            # Return first 5000 chars to avoid overwhelming
            content = response.text[:5000]
            truncated = len(response.text) > 5000
            
            result = f"URL: {url}\nStatus: {response.status_code}\n{'='*50}\n{content}"
            if truncated:
                result += "\n... (content truncated)"
            
            return result
            
        except requests.exceptions.RequestException as e:
            return f"Error fetching URL: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def _arun(self, url: str, timeout: int = 10) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._run, url, timeout)


# ============== Python Code Execution ==============

class PythonExecuteInput(BaseModel):
    code: str = Field(description="Python code to execute")
    timeout: int = Field(default=30, description="Execution timeout")

class PythonExecuteTool(BaseTool):
    name = "python_execute"
    description = "Execute Python code safely and return output"
    args_schema: Type[BaseModel] = PythonExecuteInput
    
    def _run(self, code: str, timeout: int = 30) -> str:
        # Security checks
        dangerous_imports = ['os.system', 'subprocess', 'eval(', 'exec(', '__import__']
        for pattern in dangerous_imports:
            if pattern in code:
                return f"Error: Potentially dangerous code detected: {pattern}"
        
        try:
            # Capture stdout
            import io
            from contextlib import redirect_stdout, redirect_stderr
            
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            # Create safe namespace
            namespace = {
                '__builtins__': {
                    'print': print,
                    'len': len,
                    'range': range,
                    'str': str,
                    'int': int,
                    'float': float,
                    'list': list,
                    'dict': dict,
                    'set': set,
                    'tuple': tuple,
                    'bool': bool,
                    'sum': sum,
                    'min': min,
                    'max': max,
                    'abs': abs,
                    'round': round,
                    'enumerate': enumerate,
                    'zip': zip,
                    'map': map,
                    'filter': filter,
                    'sorted': sorted,
                    'reversed': reversed,
                }
            }
            
            # Execute code
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(code, namespace)
            
            result = ""
            stdout_output = stdout_capture.getvalue()
            stderr_output = stderr_capture.getvalue()
            
            if stdout_output:
                result += f"Output:\n{stdout_output}\n"
            if stderr_output:
                result += f"Errors:\n{stderr_output}\n"
            
            # Get final variable state (excluding builtins)
            variables = {k: v for k, v in namespace.items() 
                        if not k.startswith('__') and k != '_'}
            if variables:
                result += f"\nFinal variables:\n{json.dumps(variables, default=str, indent=2)}"
            
            return result.strip() or "Code executed successfully (no output)"
            
        except Exception as e:
            return f"Error executing code: {str(e)}"
    
    async def _arun(self, code: str, timeout: int = 30) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._run, code, timeout)


# ============== Math & Calculation Tools ==============

class MathEvaluateInput(BaseModel):
    expression: str = Field(description="Mathematical expression to evaluate")

class MathEvaluateTool(BaseTool):
    name = "math_evaluate"
    description = "Evaluate mathematical expressions safely"
    args_schema: Type[BaseModel] = MathEvaluateInput
    
    def _run(self, expression: str) -> str:
        # Only allow safe characters
        allowed_chars = set('0123456789+-*/().^ ')
        if not all(c in allowed_chars for c in expression):
            return "Error: Invalid characters in expression. Only numbers and +-*/.()^ allowed."
        
        try:
            # Replace ^ with ** for exponentiation
            expr = expression.replace('^', '**')
            
            # Safe evaluation
            result = eval(expr, {"__builtins__": {}}, {})
            return f"{expression} = {result}"
            
        except Exception as e:
            return f"Error evaluating expression: {str(e)}"
    
    async def _arun(self, expression: str) -> str:
        return self._run(expression)


# ============== Utility Tools ==============

class GetCurrentTimeTool(BaseTool):
    name = "get_current_time"
    description = "Get the current date and time"
    
    def _run(self) -> str:
        from datetime import datetime
        now = datetime.now()
        return f"Current date/time: {now.strftime('%Y-%m-%d %H:%M:%S')}"
    
    async def _arun(self) -> str:
        return self._run()


class GetSystemInfoTool(BaseTool):
    name = "get_system_info"
    description = "Get system information (OS, Python version, etc.)"
    
    def _run(self) -> str:
        import platform
        info = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "cwd": os.getcwd()
        }
        return json.dumps(info, indent=2)
    
    async def _arun(self) -> str:
        return self._run()


# ============== Tool Factory ==============

def get_all_tools() -> List[BaseTool]:
    """Factory function to get all available tools"""
    return [
        # File System
        FileSystemReadTool(),
        FileSystemWriteTool(),
        FileSystemListTool(),
        
        # Console
        ConsoleExecuteTool(),
        
        # Web
        WebSearchTool(),
        WebFetchTool(),
        
        # Code Execution
        PythonExecuteTool(),
        
        # Math
        MathEvaluateTool(),
        
        # Utilities
        GetCurrentTimeTool(),
        GetSystemInfoTool()
    ]


def get_tool_by_name(name: str) -> Optional[BaseTool]:
    """Get a specific tool by name"""
    tools = get_all_tools()
    for tool in tools:
        if tool.name == name:
            return tool
    return None


def get_tool_categories() -> Dict[str, List[str]]:
    """Get tools organized by category"""
    return {
        "filesystem": ["file_read", "file_write", "file_list"],
        "console": ["console_execute"],
        "web": ["web_search", "web_fetch"],
        "code": ["python_execute"],
        "math": ["math_evaluate"],
        "utility": ["get_current_time", "get_system_info"]
    }

#!/usr/bin/env python3
"""
DeepAgents GUI - A full-featured customtkinter GUI for DeepAgents using LM Studio server.

This application provides a complete graphical interface for interacting with DeepAgents
using only LM Studio server and local models. No external API keys required.

Features:
- Chat interface with streaming responses
- Tool execution visualization
- Sub-agent management
- File system operations
- Configurable LM Studio connection
- Thread/conversation management
- Real-time status updates
- Todo list tracking
- Memory management
- Web search capabilities
- Calculator and math tools
- Debug logging
"""

import asyncio
import json
import os
import sys
import threading
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional
from functools import wraps

import customtkinter as ctk
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool, tool
import httpx

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deepagents_gui.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Try to import additional tools
try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
    logger.info("DuckDuckGo search available")
except ImportError:
    DDGS_AVAILABLE = False
    logger.warning("DuckDuckGo search not available - install with: pip install duckduckgo-search")

try:
    from sympy import symbols, Eq, solve, sympify
    SYMPY_AVAILABLE = True
    logger.info("SymPy math solver available")
except ImportError:
    SYMPY_AVAILABLE = False
    logger.warning("SymPy not available - install with: pip install sympy")

try:
    from PIL import Image
    PIL_AVAILABLE = True
    logger.info("Pillow image processing available")
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("Pillow not available - install with: pip install Pillow")

# Configure customtkinter appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# Try to import deepagents if available
try:
    from deepagents import create_deep_agent
    DEEPAGENTS_AVAILABLE = True
    logger.info("DeepAgents package loaded successfully")
except ImportError:
    DEEPAGENTS_AVAILABLE = False
    logger.warning("DeepAgents package not installed. Using basic LangGraph agent.")


class LMStudioClient:
    """Client for interacting with LM Studio server."""
    
    def __init__(self, base_url: str = "http://localhost:1234"):
        self.base_url = base_url.rstrip("/")
        self.api_key = "lm-studio"  # LM Studio doesn't require a real API key
        logger.debug(f"LMStudioClient initialized with base_url: {self.base_url}")
        
    def get_chat_model(self, model_name: Optional[str] = None, temperature: float = 0.7):
        """Get a ChatOpenAI instance configured for LM Studio."""
        logger.info(f"Getting chat model: {model_name or 'local-model'}, temperature: {temperature}")
        return ChatOpenAI(
            base_url=f"{self.base_url}/v1",
            api_key=self.api_key,
            model=model_name or "local-model",
            temperature=temperature,
            streaming=True,
        )
    
    async def check_connection(self) -> bool:
        """Check if LM Studio server is reachable."""
        try:
            logger.debug(f"Checking connection to {self.base_url}/v1/models")
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/v1/models", timeout=5.0)
                connected = response.status_code == 200
                logger.info(f"Connection check result: {connected} (status: {response.status_code})")
                return connected
        except Exception as e:
            logger.error(f"Connection check failed: {str(e)}")
            return False
    
    async def get_available_models(self) -> list[str]:
        """Get list of available models from LM Studio."""
        try:
            logger.debug("Fetching available models from LM Studio")
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/v1/models", timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    models = [model["id"] for model in data.get("data", [])]
                    logger.info(f"Found {len(models)} models: {models}")
                    return models
        except Exception as e:
            logger.error(f"Failed to get models: {str(e)}")
        return []
    
    async def get_model_info(self, model_id: str) -> dict:
        """Get detailed information about a specific model including max_tokens."""
        try:
            logger.debug(f"Fetching info for model: {model_id}")
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/v1/models/{model_id}", timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Model info retrieved: {model_id}")
                    return data
        except Exception as e:
            logger.error(f"Failed to get model info: {str(e)}")
        return {}


class SimpleFilesystemTools:
    """Simple filesystem tools for the agent."""
    
    @staticmethod
    @tool
    def read_file(file_path: str) -> str:
        """Read contents of a file.
        
        Args:
            file_path: Path to the file to read.
            
        Returns:
            Contents of the file or error message.
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return f"Error: File '{file_path}' does not exist."
            if not path.is_file():
                return f"Error: '{file_path}' is not a file."
            return path.read_text(encoding="utf-8")
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    @staticmethod
    @tool
    def write_file(file_path: str, content: str) -> str:
        """Write content to a file.
        
        Args:
            file_path: Path to the file to write.
            content: Content to write to the file.
            
        Returns:
            Success message or error.
        """
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return f"Successfully wrote {len(content)} characters to '{file_path}'."
        except Exception as e:
            return f"Error writing file: {str(e)}"
    
    @staticmethod
    @tool
    def list_directory(dir_path: str = ".") -> str:
        """List contents of a directory.
        
        Args:
            dir_path: Path to the directory to list.
            
        Returns:
            List of files and directories or error message.
        """
        try:
            path = Path(dir_path)
            if not path.exists():
                return f"Error: Directory '{dir_path}' does not exist."
            if not path.is_dir():
                return f"Error: '{dir_path}' is not a directory."
            
            items = []
            for item in sorted(path.iterdir()):
                prefix = "[DIR] " if item.is_dir() else "[FILE] "
                items.append(f"{prefix}{item.name}")
            
            return "\n".join(items) if items else "Directory is empty."
        except Exception as e:
            return f"Error listing directory: {str(e)}"
    
    @staticmethod
    @tool
    def execute_command(command: str, full_access: bool = False, allowed_commands: list = None) -> str:
        """Execute a shell command with configurable security.
        
        Args:
            command: Shell command to execute.
            full_access: If True, allow any command (dangerous!).
            allowed_commands: List of allowed command prefixes (used when full_access=False).
            
        Returns:
            Command output or error message.
        """
        import subprocess
        
        if allowed_commands is None:
            allowed_commands = ["ls", "dir", "cat", "head", "tail", "pwd", "echo", "find", "grep"]
        
        try:
            # Security check
            if not full_access:
                cmd_lower = command.lower().strip()
                # Extract base command (first word)
                base_cmd = cmd_lower.split()[0] if cmd_lower else ""
                
                # Check against allowed commands
                if not any(base_cmd == prefix or cmd_lower.startswith(prefix + " ") for prefix in allowed_commands):
                    return f"Error: Command '{command}' is not allowed.\nAllowed commands: {', '.join(allowed_commands)}\nEnable full access in Settings > Security to run any command."
            
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = result.stdout if result.stdout else result.stderr
            logger.debug(f"Command executed: {command}, output length: {len(output)}")
            return output.strip() or "Command executed successfully (no output)."
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {command}")
            return "Error: Command timed out."
        except Exception as e:
            logger.error(f"Command execution failed: {str(e)}")
            return f"Error executing command: {str(e)}"


def get_execute_command_tool(full_access: bool = False, allowed_commands: list = None):
    """Create a configured execute_command tool with security settings.
    
    This function creates a partial application of SimpleFilesystemTools.execute_command
    with the specified security settings.
    
    Args:
        full_access: If True, allow any command (dangerous!).
        allowed_commands: List of allowed command prefixes.
        
    Returns:
        A configured tool function for executing commands.
    """
    from functools import partial
    
    if allowed_commands is None:
        allowed_commands = ["ls", "dir", "cat", "head", "tail", "pwd", "echo", "find", "grep"]
    
    # Get the underlying function from the staticmethod descriptor
    base_func = SimpleFilesystemTools.__dict__['execute_command']
    if isinstance(base_func, staticmethod):
        base_func = base_func.__func__
    
    # Create partial application with security settings
    execute_cmd = partial(base_func, full_access=full_access, allowed_commands=allowed_commands)
    
    # Copy metadata from the original tool
    if hasattr(SimpleFilesystemTools.execute_command, 'name'):
        execute_cmd.name = SimpleFilesystemTools.execute_command.name
    if hasattr(SimpleFilesystemTools.execute_command, 'description'):
        execute_cmd.description = SimpleFilesystemTools.execute_command.description
    if hasattr(SimpleFilesystemTools.execute_command, 'args_schema'):
        execute_cmd.args_schema = SimpleFilesystemTools.execute_command.args_schema
    
    return execute_cmd


class WebSearchTools:
    """Web search tools using DuckDuckGo."""
    
    @staticmethod
    @tool
    def web_search(query: str, num_results: int = 5) -> str:
        """Search the web for current information.
        
        Args:
            query: Search query string.
            num_results: Number of results to return (default: 5).
            
        Returns:
            Search results with titles and snippets.
        """
        if not DDGS_AVAILABLE:
            logger.warning("Web search requested but DuckDuckGo not available")
            return "Error: Web search is not available. Please install duckduckgo-search package."
        
        try:
            logger.info(f"Performing web search: '{query}' (num_results={num_results})")
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=num_results))
                if not results:
                    return f"No results found for '{query}'"
                
                formatted = []
                for i, r in enumerate(results[:num_results], 1):
                    title = r.get('title', 'No title')
                    body = r.get('body', 'No description')
                    url = r.get('href', 'No URL')
                    formatted.append(f"{i}. {title}\n   {body}\n   URL: {url}")
                
                result_text = "\n\n".join(formatted)
                logger.info(f"Web search returned {len(results)} results")
                return f"Search results for '{query}':\n\n{result_text}"
        except Exception as e:
            logger.error(f"Web search failed: {str(e)}")
            return f"Error performing web search: {str(e)}"
    
    @staticmethod
    @tool
    def news_search(topic: str, num_results: int = 3) -> str:
        """Search for recent news on a topic.
        
        Args:
            topic: News topic to search for.
            num_results: Number of results to return (default: 3).
            
        Returns:
            Recent news articles about the topic.
        """
        if not DDGS_AVAILABLE:
            return "Error: News search is not available. Please install duckduckgo-search package."
        
        try:
            logger.info(f"Performing news search: '{topic}'")
            with DDGS() as ddgs:
                results = list(ddgs.news(topic, max_results=num_results))
                if not results:
                    return f"No news found for '{topic}'"
                
                formatted = []
                for i, r in enumerate(results[:num_results], 1):
                    title = r.get('title', 'No title')
                    source = r.get('source', 'Unknown source')
                    date = r.get('date', 'Unknown date')
                    url = r.get('url', 'No URL')
                    formatted.append(f"{i}. {title}\n   Source: {source} | Date: {date}\n   URL: {url}")
                
                result_text = "\n\n".join(formatted)
                logger.info(f"News search returned {len(results)} results")
                return f"Recent news about '{topic}':\n\n{result_text}"
        except Exception as e:
            logger.error(f"News search failed: {str(e)}")
            return f"Error performing news search: {str(e)}"


class MathTools:
    """Mathematical computation tools using SymPy."""
    
    @staticmethod
    @tool
    def calculate(expression: str) -> str:
        """Evaluate a mathematical expression safely.
        
        Args:
            expression: Mathematical expression to evaluate (e.g., "2 + 2", "sqrt(16)", "sin(pi/2)").
            
        Returns:
            Result of the calculation.
        """
        if not SYMPY_AVAILABLE:
            logger.warning("Calculation requested but SymPy not available")
            return "Error: Calculator is not available. Please install sympy package."
        
        try:
            logger.info(f"Calculating expression: '{expression}'")
            # Safely evaluate the expression using sympify
            result = sympify(expression, evaluate=True)
            result_str = str(result)
            logger.info(f"Calculation result: {result_str}")
            return f"Result of '{expression}': {result_str}"
        except Exception as e:
            logger.error(f"Calculation failed: {str(e)}")
            return f"Error calculating '{expression}': {str(e)}"
    
    @staticmethod
    @tool
    def solve_equation(equation: str, variable: str = "x") -> str:
        """Solve an algebraic equation.
        
        Args:
            equation: Equation to solve (e.g., "x**2 - 4 = 0" or "2*x + 3 = 7").
            variable: Variable to solve for (default: "x").
            
        Returns:
            Solution(s) to the equation.
        """
        if not SYMPY_AVAILABLE:
            return "Error: Equation solver is not available. Please install sympy package."
        
        try:
            logger.info(f"Solving equation: '{equation}' for variable '{variable}'")
            x = symbols(variable)
            
            # Parse the equation - handle both "expr = 0" and "expr1 = expr2" formats
            if "=" in equation:
                left, right = equation.split("=", 1)
                eq = Eq(sympify(left.strip()), sympify(right.strip()))
            else:
                eq = Eq(sympify(equation), 0)
            
            solutions = solve(eq, x)
            if not solutions:
                return f"No solutions found for: {equation}"
            
            solution_str = ", ".join(str(s) for s in solutions)
            logger.info(f"Equation solutions: {solution_str}")
            return f"Solutions for '{equation}': {solution_str}"
        except Exception as e:
            logger.error(f"Equation solving failed: {str(e)}")
            return f"Error solving '{equation}': {str(e)}"


class ImageTools:
    """Image processing tools using Pillow."""
    
    @staticmethod
    @tool
    def get_image_info(image_path: str) -> str:
        """Get information about an image file.
        
        Args:
            image_path: Path to the image file.
            
        Returns:
            Image metadata including format, size, mode, etc.
        """
        if not PIL_AVAILABLE:
            logger.warning("Image info requested but Pillow not available")
            return "Error: Image processing is not available. Please install Pillow package."
        
        try:
            logger.info(f"Getting image info: '{image_path}'")
            path = Path(image_path)
            if not path.exists():
                return f"Error: Image file '{image_path}' does not exist."
            
            with Image.open(path) as img:
                info = {
                    "format": img.format,
                    "mode": img.mode,
                    "size": img.size,
                    "width": img.width,
                    "height": img.height
                }
                result = f"Image info for '{image_path}':\n"
                result += "\n".join(f"  {k}: {v}" for k, v in info.items())
                logger.info(f"Image info retrieved: {info}")
                return result
        except Exception as e:
            logger.error(f"Image info failed: {str(e)}")
            return f"Error getting image info: {str(e)}"


# Note: Filesystem tools are now available via deepagents.tools module
# Import them with: from deepagents.tools import create_filesystem_tools


class MessageBubble(ctk.CTkFrame):
    """A message bubble widget for chat display with collapsible content."""
    
    def __init__(
        self,
        master,
        message: str,
        role: str = "user",
        timestamp: Optional[str] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        
        self.role = role
        self.is_expanded = False
        self.full_message = message
        self.collapsed_lines = 15  # Количество видимых строк в свернутом режиме
        self.configure(corner_radius=10, fg_color="transparent")
        logger.debug(f"MessageBubble created: role={role}, message_len={len(message)}")
        
        # Timestamp
        if timestamp is None:
            timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Role label
        role_color = "#3498db" if role == "user" else "#2ecc71"
        role_text = "You" if role == "user" else "Assistant"
        
        self.role_label = ctk.CTkLabel(
            self,
            text=f"{role_text} • {timestamp}",
            text_color=role_color,
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        self.role_label.pack(fill="x", padx=5, pady=(5, 0))
        
        # Message content frame
        self.message_frame = ctk.CTkFrame(
            self,
            corner_radius=10,
            fg_color="#2b2b2b" if role == "assistant" else "#3a3a3a"
        )
        self.message_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Text widget with scrollbar for long messages
        self.message_text = ctk.CTkTextbox(
            self.message_frame,
            wrap="word",
            font=ctk.CTkFont(size=13),
            height=10,
            activate_scrollbars=True
        )
        self.message_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.message_text.insert("0.0", message)
        self.message_text.configure(state="disabled")  # Make read-only
        
        # Button frame for expand/collapse and copy
        self.btn_frame = ctk.CTkFrame(self.message_frame, fg_color="transparent")
        self.btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Expand/Collapse button for assistant messages
        if role == "assistant" and len(message) > 500:
            self.toggle_btn = ctk.CTkButton(
                self.btn_frame,
                text="📋 Показать полностью",
                command=self._toggle_expand,
                width=150,
                height=25,
                font=ctk.CTkFont(size=11),
                fg_color="#3a3a3a",
                hover_color="#4a4a4a"
            )
            self.toggle_btn.pack(side="left", padx=(0, 5))
        
        # Copy button
        self.copy_btn = ctk.CTkButton(
            self.btn_frame,
            text="📋 Копировать",
            command=self._copy_to_clipboard,
            width=120,
            height=25,
            font=ctk.CTkFont(size=11),
            fg_color="#3a3a3a",
            hover_color="#4a4a4a"
        )
        self.copy_btn.pack(side="right")
    
    def _copy_to_clipboard(self):
        """Copy message content to clipboard."""
        self.clipboard_clear()
        self.clipboard_append(self.full_message)
        # Show temporary feedback
        original_text = self.copy_btn.cget("text")
        self.copy_btn.configure(text="✓ Скопировано!")
        self.after(1500, lambda: self.copy_btn.configure(text=original_text))
    
    def _toggle_expand(self):
        """Toggle between expanded and collapsed state."""
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            self.message_text.configure(height=30)  # More lines when expanded
            self.toggle_btn.configure(text="📄 Свернуть")
        else:
            self.message_text.configure(height=10)  # Fewer lines when collapsed
            self.toggle_btn.configure(text="📋 Показать полностью")
    
    def update_message(self, new_content: str):
        """Update the message content (for streaming)."""
        self.full_message = new_content
        self.message_text.configure(state="normal")
        self.message_text.delete("0.0", "end")
        self.message_text.insert("0.0", new_content)
        self.message_text.configure(state="disabled")


class SettingsDialog(ctk.CTkToplevel):
    """Расширенные настройки с управлением инструментами и безопасностью."""
    
    def __init__(self, parent, current_settings: dict, save_callback: Callable):
        super().__init__(parent)
        
        self.title("Настройки DeepAgents")
        self.geometry("900x700")
        self.resizable(True, True)
        self.minsize(700, 500)
        
        self.save_callback = save_callback
        self.current_settings = current_settings.copy()
        
        # Инициализация настроек инструментов
        if "tools_settings" not in self.current_settings:
            self.current_settings["tools_settings"] = {
                "filesystem_enabled": True,
                "websearch_enabled": DDGS_AVAILABLE,
                "math_enabled": SYMPY_AVAILABLE,
                "image_enabled": PIL_AVAILABLE,
                "command_full_access": False,  # По умолчанию ограниченный доступ
                "allowed_commands": ["ls", "dir", "cat", "head", "tail", "pwd", "echo", "find", "grep"],
            }
        
        # Modal behavior
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        """Create settings widgets with tabs."""
        # Создаем систему вкладок
        self.tabview = ctk.CTkTabview(self, width=850, height=600)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Вкладка 1: LM Studio
        self.lmstudio_tab = self.tabview.add("LM Studio")
        self._create_lmstudio_widgets(self.lmstudio_tab)
        
        # Вкладка 2: Инструменты
        self.tools_tab = self.tabview.add("Инструменты")
        self._create_tools_widgets(self.tools_tab)
        
        # Вкладка 3: Безопасность
        self.security_tab = self.tabview.add("Безопасность")
        self._create_security_widgets(self.security_tab)
        
        # Кнопки внизу
        self._create_buttons()
    
    def _create_lmstudio_widgets(self, parent):
        """Виджеты настроек LM Studio."""
        main_frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title = ctk.CTkLabel(
            main_frame,
            text="Настройки LM Studio",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=(0, 20))
        
        # LM Studio URL
        url_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        url_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            url_frame,
            text="LM Studio Server URL:",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w")
        
        self.url_entry = ctk.CTkEntry(
            url_frame,
            width=400,
            placeholder_text="http://localhost:1234"
        )
        self.url_entry.pack(fill="x", pady=5)
        if self.current_settings.get("lmstudio_url", ""):
            self.url_entry.insert(0, self.current_settings.get("lmstudio_url", "http://localhost:1234"))
        
        # Model name
        model_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        model_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            model_frame,
            text="Model Name (опционально):",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w")
        
        self.model_entry = ctk.CTkEntry(
            model_frame,
            width=400,
            placeholder_text="Оставить пустым для значения по умолчанию"
        )
        self.model_entry.pack(fill="x", pady=5)
        if self.current_settings.get("model_name", ""):
            self.model_entry.insert(0, self.current_settings.get("model_name", ""))
        
        # Temperature
        temp_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        temp_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            temp_frame,
            text="Temperature (креативность):",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w")
        
        self.temp_slider = ctk.CTkSlider(
            temp_frame,
            from_=0.0,
            to=2.0,
            number_of_steps=20,
            command=lambda v: self.temp_value.configure(text=f"{v:.2f}")
        )
        self.temp_slider.pack(fill="x", pady=5)
        self.temp_slider.set(self.current_settings.get("temperature", 0.7))
        
        self.temp_value = ctk.CTkLabel(
            temp_frame,
            text=f"{self.current_settings.get('temperature', 0.7):.2f}",
            font=ctk.CTkFont(size=12)
        )
        self.temp_value.pack(anchor="e")
        
        # Max tokens
        tokens_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        tokens_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            tokens_frame,
            text="Max Tokens (лимит ответа):",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w")
        
        self.max_tokens_entry = ctk.CTkEntry(
            tokens_frame,
            width=150,
            placeholder_text="4096"
        )
        self.max_tokens_entry.pack(anchor="w", pady=5)
        if self.current_settings.get("max_tokens"):
            self.max_tokens_entry.insert(0, str(self.current_settings["max_tokens"]))
        
        # Timeout
        timeout_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        timeout_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            timeout_frame,
            text="Timeout (секунды на запрос):",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w")
        
        self.timeout_entry = ctk.CTkEntry(
            timeout_frame,
            width=150,
            placeholder_text="120"
        )
        self.timeout_entry.pack(anchor="w", pady=5)
        if self.current_settings.get("timeout_seconds"):
            self.timeout_entry.insert(0, str(self.current_settings["timeout_seconds"]))
        
        # Retry attempts
        retry_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        retry_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            retry_frame,
            text="Попытки повтора при ошибке:",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w")
        
        self.retry_entry = ctk.CTkEntry(
            retry_frame,
            width=150,
            placeholder_text="3"
        )
        self.retry_entry.pack(anchor="w", pady=5)
        if self.current_settings.get("retry_attempts"):
            self.retry_entry.insert(0, str(self.current_settings["retry_attempts"]))
        
        # Working directory
        workdir_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        workdir_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            workdir_frame,
            text="Рабочая директория:",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w")
        
        workdir_entry_frame = ctk.CTkFrame(workdir_frame, fg_color="transparent")
        workdir_entry_frame.pack(fill="x", pady=5)
        
        self.workdir_entry = ctk.CTkEntry(
            workdir_entry_frame,
            width=320,
            placeholder_text=str(Path.cwd())
        )
        self.workdir_entry.pack(side="left", fill="x", expand=True)
        if self.current_settings.get("working_dir", ""):
            self.workdir_entry.insert(0, self.current_settings.get("working_dir", str(Path.cwd())))
        
        browse_btn = ctk.CTkButton(
            workdir_entry_frame,
            text="Обзор...",
            command=self._browse_workdir,
            width=80
        )
        browse_btn.pack(side="right", padx=(10, 0))
    
    def _create_tools_widgets(self, parent):
        """Виджеты управления инструментами."""
        main_frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        title = ctk.CTkLabel(
            main_frame,
            text="Управление инструментами",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=(0, 20))
        
        desc = ctk.CTkLabel(
            main_frame,
            text="Включайте/выключайте инструменты для контроля возможностей агента",
            font=ctk.CTkFont(size=12),
            text_color="#7f8c8d"
        )
        desc.pack(pady=(0, 20))
        
        tools = self.current_settings.get("tools_settings", {})
        
        # Файловая система
        self._create_tool_toggle(
            main_frame,
            "📁 Файловая система",
            "Чтение/запись файлов, просмотр директорий",
            "filesystem_enabled",
            tools.get("filesystem_enabled", True)
        )
        
        # Веб-поиск
        self._create_tool_toggle(
            main_frame,
            "🌐 Веб-поиск",
            "Поиск информации в интернете через DuckDuckGo",
            "websearch_enabled",
            tools.get("websearch_enabled", DDGS_AVAILABLE),
            disabled=not DDGS_AVAILABLE,
            disabled_text="Требуется пакет duckduckgo-search"
        )
        
        # Математика
        self._create_tool_toggle(
            main_frame,
            "🧮 Математика",
            "Вычисления и решение уравнений через SymPy",
            "math_enabled",
            tools.get("math_enabled", SYMPY_AVAILABLE),
            disabled=not SYMPY_AVAILABLE,
            disabled_text="Требуется пакет sympy"
        )
        
        # Изображения
        self._create_tool_toggle(
            main_frame,
            "🖼️ Обработка изображений",
            "Получение информации об изображениях",
            "image_enabled",
            tools.get("image_enabled", PIL_AVAILABLE),
            disabled=not PIL_AVAILABLE,
            disabled_text="Требуется пакет Pillow"
        )
        
        # Командная строка
        self._create_tool_toggle(
            main_frame,
            "💻 Командная строка",
            "Выполнение системных команд",
            "command_line_enabled",
            tools.get("command_line_enabled", True)
        )
    
    def _create_tool_toggle(self, parent, title, description, setting_key, enabled, disabled=False, disabled_text=""):
        """Создание переключателя инструмента."""
        frame = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        frame.pack(fill="x", pady=5, padx=5)
        
        # Название и описание
        info_frame = ctk.CTkFrame(frame, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=15, pady=10)
        
        ctk.CTkLabel(
            info_frame,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#3498db" if enabled else "#7f8c8d"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            info_frame,
            text=description,
            font=ctk.CTkFont(size=11),
            text_color="#7f8c8d"
        ).pack(anchor="w")
        
        if disabled and disabled_text:
            ctk.CTkLabel(
                info_frame,
                text=f"⚠ {disabled_text}",
                font=ctk.CTkFont(size=10),
                text_color="#e74c3c"
            ).pack(anchor="w", pady=(5, 0))
        
        # Переключатель
        switch_var = ctk.BooleanVar(value=enabled and not disabled)
        setattr(self, f"_{setting_key}_var", switch_var)
        
        switch = ctk.CTkSwitch(
            frame,
            variable=switch_var,
            text="Вкл" if enabled else "Выкл",
            command=lambda s=switch, t=title: s.configure(text="Вкл" if s.get() else "Выкл"),
            state="disabled" if disabled else "normal"
        )
        switch.pack(side="right", padx=15, pady=10)
    
    def _create_security_widgets(self, parent):
        """Виджеты настроек безопасности."""
        main_frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        title = ctk.CTkLabel(
            main_frame,
            text="Настройки безопасности",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=(0, 20))
        
        warning = ctk.CTkLabel(
            main_frame,
            text="⚠ ВНИМАНИЕ: Полные права могут быть опасны!\nУбедитесь, что доверяете используемой модели.",
            font=ctk.CTkFont(size=12),
            text_color="#e74c3c",
            justify="left"
        )
        warning.pack(pady=(0, 20), anchor="w")
        
        tools = self.current_settings.get("tools_settings", {})
        
        # Полный доступ к командной строке
        security_frame = ctk.CTkFrame(main_frame, fg_color="#2b2b2b")
        security_frame.pack(fill="x", pady=10, padx=5)
        
        ctk.CTkLabel(
            security_frame,
            text="💻 Полный доступ к командной строке",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#e74c3c"
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        ctk.CTkLabel(
            security_frame,
            text="Разрешить выполнение ЛЮБЫХ команд (включая rm, del, format и т.д.)",
            font=ctk.CTkFont(size=11),
            text_color="#7f8c8d"
        ).pack(anchor="w", padx=15, pady=(0, 10))
        
        self.full_access_var = ctk.BooleanVar(value=tools.get("command_full_access", False))
        self.full_access_switch = ctk.CTkSwitch(
            security_frame,
            variable=self.full_access_var,
            text="Полный доступ" if self.full_access_var.get() else "Ограниченный доступ",
            command=self._toggle_full_access
        )
        self.full_access_switch.pack(side="right", padx=15, pady=10)
        
        # Список разрешённых команд (для ограниченного режима)
        self.allowed_commands_frame = ctk.CTkFrame(main_frame, fg_color="#2b2b2b")
        self.allowed_commands_frame.pack(fill="both", expand=True, pady=10, padx=5)
        
        ctk.CTkLabel(
            self.allowed_commands_frame,
            text="Разрешённые команды (ограниченный режим):",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        ctk.CTkLabel(
            self.allowed_commands_frame,
            text="Введите команды через запятую (например: ls, dir, cat, pwd)",
            font=ctk.CTkFont(size=10),
            text_color="#7f8c8d"
        ).pack(anchor="w", padx=15, pady=(0, 5))
        
        allowed_commands = tools.get("allowed_commands", ["ls", "dir", "cat", "head", "tail", "pwd", "echo", "find", "grep"])
        self.allowed_commands_entry = ctk.CTkTextbox(
            self.allowed_commands_frame,
            height=100,
            font=ctk.CTkFont(size=12),
            wrap="word"
        )
        self.allowed_commands_entry.pack(fill="both", expand=True, padx=15, pady=5)
        self.allowed_commands_entry.insert("0.0", ", ".join(allowed_commands))
        
        # Обновить состояние UI
        self._update_security_ui()
    
    def _toggle_full_access(self):
        """Переключение полного доступа."""
        is_full = self.full_access_var.get()
        self.full_access_switch.configure(
            text="Полный доступ ⚠" if is_full else "Ограниченный доступ"
        )
        self._update_security_ui()
    
    def _update_security_ui(self):
        """Обновление состояния UI безопасности."""
        is_full = self.full_access_var.get()
        
        # Блокируем список команд при полном доступе
        if is_full:
            self.allowed_commands_entry.configure(state="disabled", fg_color="#1a1a1a")
        else:
            self.allowed_commands_entry.configure(state="normal", fg_color="#2b2b2b")
    
    def _create_buttons(self):
        """Кнопки сохранения/отмены."""
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Отмена",
            command=self.destroy,
            width=100
        )
        cancel_btn.pack(side="left", padx=10)
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="Сохранить",
            command=self._save_settings,
            width=100,
            fg_color="#27ae60"
        )
        save_btn.pack(side="right", padx=10)
    
    def _save_settings(self):
        """Save settings and close dialog."""
        self.current_settings["lmstudio_url"] = self.url_entry.get() or "http://localhost:1234"
        self.current_settings["model_name"] = self.model_entry.get() or None
        self.current_settings["temperature"] = self.temp_slider.get()
        self.current_settings["working_dir"] = self.workdir_entry.get() or str(Path.cwd())
        
        # Сохранение расширенных настроек модели
        max_tokens_str = self.max_tokens_entry.get().strip()
        if max_tokens_str:
            try:
                self.current_settings["max_tokens"] = int(max_tokens_str)
            except ValueError:
                self.current_settings["max_tokens"] = 4096
        
        timeout_str = self.timeout_entry.get().strip()
        if timeout_str:
            try:
                self.current_settings["timeout_seconds"] = int(timeout_str)
            except ValueError:
                self.current_settings["timeout_seconds"] = 120
        
        retry_str = self.retry_entry.get().strip()
        if retry_str:
            try:
                self.current_settings["retry_attempts"] = int(retry_str)
            except ValueError:
                self.current_settings["retry_attempts"] = 3
        
        # Сохранение настроек инструментов
        tools_settings = {
            "filesystem_enabled": getattr(self, "_filesystem_enabled_var", ctk.BooleanVar(value=True)).get(),
            "websearch_enabled": getattr(self, "_websearch_enabled_var", ctk.BooleanVar(value=False)).get(),
            "math_enabled": getattr(self, "_math_enabled_var", ctk.BooleanVar(value=False)).get(),
            "image_enabled": getattr(self, "_image_enabled_var", ctk.BooleanVar(value=False)).get(),
            "command_line_enabled": getattr(self, "_command_line_enabled_var", ctk.BooleanVar(value=True)).get(),
            "command_full_access": self.full_access_var.get(),
            "allowed_commands": [
                cmd.strip() 
                for cmd in self.allowed_commands_entry.get("0.0", "end-1c").split(",") 
                if cmd.strip()
            ],
        }
        self.current_settings["tools_settings"] = tools_settings
        
        logger.info(f"Settings saved: tools={tools_settings}")
        self.save_callback(self.current_settings)
        self.destroy()
    
    def _browse_workdir(self):
        """Open file dialog to select working directory."""
        import tkinter.filedialog as fd
        dirname = fd.askdirectory(initialdir=self.current_settings.get("working_dir", str(Path.cwd())))
        if dirname:
            self.workdir_entry.delete(0, 'end')
            self.workdir_entry.insert(0, dirname)
    
    def _browse_project(self):
        """Open file dialog to select project folder."""
        import tkinter.filedialog as fd
        initial_dir = self.current_settings.get("project_folder", "") or self.current_settings.get("working_dir", str(Path.cwd()))
        dirname = fd.askdirectory(initialdir=initial_dir)
        if dirname:
            self.project_entry.delete(0, 'end')
            self.project_entry.insert(0, dirname)


class DeepAgentsGUI(ctk.CTk):
    """Main DeepAgents GUI Application."""
    
    def __init__(self):
        super().__init__()
        
        self.title("DeepAgents GUI - LM Studio")
        self.geometry("1200x800")
        self.minsize(900, 600)
        
        # Settings
        self.settings = {
            "lmstudio_url": "http://localhost:1234",
            "model_name": None,
            "temperature": 0.7,
            "max_tokens": 4096,  # Default value, will be updated from LM Studio
            "timeout_seconds": 120,
            "retry_attempts": 3,
            "working_dir": str(Path.cwd()),
        }
        
        # Reference to settings dialog (for updating fields)
        self._settings_dialog = None
        
        # State
        self.lmstudio_client = LMStudioClient(self.settings["lmstudio_url"])
        self.conversation_history: list = []
        self.is_processing = False
        self.current_tool_calls: list = []
        self.current_tool_names: list = []  # Store available tool names for display
        self.tasks: list = []  # List of tasks/conversations
        
        # Setup UI
        self._setup_ui()
        
        # Check connection on startup
        self.after(1000, self._check_lmstudio_connection)
    
    def _setup_ui(self):
        """Setup the user interface."""
        # Configure grid weights
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        self._create_header()
        
        # Main content area
        self._create_main_area()
        
        # Status bar
        self._create_status_bar()
    
    def _create_header(self):
        """Create header with controls."""
        header = ctk.CTkFrame(self, height=60, fg_color="#2b2b2b")
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        # Configure grid columns for header elements
        header.grid_columnconfigure(0, weight=1)  # Title section (expandable)
        header.grid_columnconfigure(1, weight=0)  # Connection indicator
        header.grid_columnconfigure(2, weight=0)  # Connect button
        header.grid_columnconfigure(3, weight=0)  # Model dropdown
        header.grid_columnconfigure(4, weight=0)  # New Task button
        header.grid_columnconfigure(5, weight=0)  # Settings button
        header.grid_columnconfigure(6, weight=0)  # Clear button
        
        # Logo/Title
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        ctk.CTkLabel(
            title_frame,
            text="🤖 DeepAgents GUI",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#3498db"
        ).pack(side="left")
        
        ctk.CTkLabel(
            title_frame,
            text="  |  Powered by LM Studio",
            font=ctk.CTkFont(size=14),
            text_color="#7f8c8d"
        ).pack(side="left")
        
        # Connection status
        self.connection_indicator = ctk.CTkLabel(
            header,
            text="●",
            font=ctk.CTkFont(size=24),
            text_color="#e74c3c"  # Red (disconnected)
        )
        self.connection_indicator.grid(row=0, column=1, sticky="e", padx=10)
        
        self.connection_label = ctk.CTkLabel(
            header,
            text="Disconnected",
            font=ctk.CTkFont(size=12),
            text_color="#e74c3c"
        )
        self.connection_label.grid(row=0, column=1, sticky="e", padx=(10, 5))
        
        # Connect/Refresh button
        self.connect_btn = ctk.CTkButton(
            header,
            text="🔄 Connect",
            command=self._check_lmstudio_connection,
            width=90,
            height=30
        )
        self.connect_btn.grid(row=0, column=2, padx=5, pady=10)
        
        # Model selection dropdown
        self.model_var = ctk.StringVar(value="Select model...")
        self.model_dropdown = ctk.CTkOptionMenu(
            header,
            variable=self.model_var,
            values=[],
            command=self._on_model_selected,
            width=150,
            height=30
        )
        self.model_dropdown.grid(row=0, column=3, padx=10, pady=10)
        
        # New Task button
        new_task_btn = ctk.CTkButton(
            header,
            text="📄 New Task",
            command=self._new_task,
            width=80,
            height=30
        )
        new_task_btn.grid(row=0, column=4, padx=10, pady=10)
        
        # Settings button
        settings_btn = ctk.CTkButton(
            header,
            text="⚙ Settings",
            command=self._open_settings,
            width=80,
            height=30
        )
        settings_btn.grid(row=0, column=5, padx=10, pady=10)
        
        # Clear chat button
        clear_btn = ctk.CTkButton(
            header,
            text="🗑 Clear Chat",
            command=self._clear_chat,
            width=80,
            height=30,
            fg_color="#e74c3c"
        )
        clear_btn.grid(row=0, column=6, padx=10, pady=10)
    
    def _create_main_area(self):
        """Create main content area with chat and tools."""
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Chat area
        chat_container = ctk.CTkFrame(main_frame, fg_color="#1e1e1e")
        chat_container.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        chat_container.grid_columnconfigure(0, weight=1)
        chat_container.grid_rowconfigure(0, weight=1)
        
        # Scrollable chat frame
        self.chat_canvas = ctk.CTkScrollableFrame(
            chat_container,
            fg_color="transparent"
        )
        self.chat_canvas.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.chat_canvas.grid_columnconfigure(0, weight=1)
        
        # Welcome message
        self._add_welcome_message()
        
        # Input area
        input_frame = ctk.CTkFrame(main_frame, height=100, fg_color="#2b2b2b")
        input_frame.grid(row=1, column=0, sticky="ew", padx=0, pady=(10, 0))
        input_frame.grid_columnconfigure(0, weight=1)
        
        # Text input
        self.input_text = ctk.CTkTextbox(
            input_frame,
            height=60,
            font=ctk.CTkFont(size=13),
            wrap="word"
        )
        self.input_text.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.input_text.bind("<Return>", lambda e: self._on_enter_pressed(e))
        self.input_text.bind("<Shift-Return>", lambda e: None)  # Allow new line
        
        # Send button
        self.send_btn = ctk.CTkButton(
            input_frame,
            text="➤ Send",
            command=self._send_message,
            height=40,
            width=100,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.send_btn.grid(row=0, column=1, padx=10, pady=10)
        
        # Bind Enter key
        self.input_text.bind("<Control-Return>", lambda e: self._send_message())
    
    def _create_status_bar(self):
        """Create status bar at bottom."""
        status_bar = ctk.CTkFrame(self, height=30, fg_color="#2b2b2b")
        status_bar.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        status_bar.grid_columnconfigure(1, weight=1)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            status_bar,
            text="Ready",
            font=ctk.CTkFont(size=11),
            text_color="#7f8c8d"
        )
        self.status_label.grid(row=0, column=0, padx=10, pady=5)
        
        # Token count / info
        self.info_label = ctk.CTkLabel(
            status_bar,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#7f8c8d"
        )
        self.info_label.grid(row=0, column=1, padx=10, pady=5, sticky="e")
    
    def _add_welcome_message(self):
        """Add welcome message to chat."""
        tools_available = []
        tools_available.append("File operations")  # Always available
        tools_available.append("Command execution")  # Always available
        if DDGS_AVAILABLE:
            tools_available.extend(["Web search", "News search"])
        if SYMPY_AVAILABLE:
            tools_available.extend(["Calculator", "Equation solver"])
        if PIL_AVAILABLE:
            tools_available.append("Image info")
        
        welcome_text = (
            f"Welcome to DeepAgents GUI! 🎉\n\n"
            f"I'm connected to LM Studio and ready to help you with various tasks.\n\n"
            f"Available tools:\n"
        )
        
        for tool in tools_available:
            welcome_text += f"• {tool}\n"
        
        welcome_text += "\nConfigure tools in Settings > Tools tab\nTo get started, simply type your message below!"
        
        logger.info(f"Displaying welcome message, tools available: {tools_available}")
        
        bubble = MessageBubble(
            self.chat_canvas,
            message=welcome_text,
            role="assistant",
            fg_color="transparent"
        )
        bubble.grid(row=len(self.conversation_history), column=0, sticky="ew", pady=5)
    
    def _add_message_bubble(self, message: str, role: str = "user") -> MessageBubble:
        """Add a message bubble to the chat."""
        row = len(self.conversation_history)
        
        logger.debug(f"Adding {role} message bubble at row {row}, message length: {len(message)}")
        
        bubble = MessageBubble(
            self.chat_canvas,
            message=message,
            role=role,
            fg_color="transparent"
        )
        bubble.grid(row=row, column=0, sticky="ew", pady=5)
        
        # Auto-scroll to bottom
        self.chat_canvas._scrollbar.set(1.0, 1.0)
        
        return bubble
    
    def _update_status(self, status: str):
        """Update status bar text."""
        logger.debug(f"Status update: {status}")
        self.status_label.configure(text=status)
    
    def _check_lmstudio_connection(self):
        """Check LM Studio connection asynchronously."""
        logger.info("Checking LM Studio connection...")
        async def check():
            connected = await self.lmstudio_client.check_connection()
            if connected:
                logger.info("LM Studio connection successful")
                self.connection_indicator.configure(text="●", text_color="#2ecc71")
                self.connection_label.configure(text="Connected", text_color="#2ecc71")
                self._update_status("Connected to LM Studio")
                
                # Get available models
                logger.debug("Fetching available models...")
                models = await self.lmstudio_client.get_available_models()
                if models:
                    logger.info(f"Found {len(models)} models from LM Studio")
                    self.info_label.configure(text=f"Available models: {len(models)}")
                    # Populate model dropdown
                    self.model_dropdown.configure(values=models)
                    if self.settings.get("model_name") and self.settings["model_name"] in models:
                        self.model_var.set(self.settings["model_name"])
                    else:
                        self.model_var.set(models[0] if models else "Select model...")
                    # Update connect button text
                    self.connect_btn.configure(text="🔄 Refresh")
                    
                    # Fetch and apply model parameters (max_tokens) for the selected model
                    selected_model = self.model_var.get()
                    if selected_model and selected_model in models:
                        await self._fetch_and_apply_model_params(selected_model)
            else:
                logger.warning("LM Studio connection failed")
                self.connection_indicator.configure(text="●", text_color="#e74c3c")
                self.connection_label.configure(text="Disconnected", text_color="#e74c3c")
                self._update_status("Cannot connect to LM Studio - Please start the server")
                self.model_dropdown.configure(values=[])
                self.model_var.set("No connection")
                # Update connect button text
                self.connect_btn.configure(text="🔄 Connect")
        
        # Run async function in a new thread with its own event loop
        def run_async_check():
            try:
                logger.debug("Starting async connection check in thread")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(check())
                loop.close()
            except Exception as e:
                logger.error(f"Connection check thread error: {str(e)}")
                self.after(0, lambda: self._update_status(f"Connection error: {str(e)}"))
        
        thread = threading.Thread(target=run_async_check, daemon=True)
        thread.start()
    
    async def _fetch_and_apply_model_params(self, model_id: str):
        """Fetch model parameters from LM Studio and apply to settings fields."""
        logger.info(f"Fetching parameters for model: {model_id}")
        try:
            model_info = await self.lmstudio_client.get_model_info(model_id)
            if model_info:
                # Extract max_tokens from model info
                # LM Studio returns different structures, check common paths
                max_tokens = None
                
                # Try different possible paths for max_tokens
                if 'max_tokens' in model_info:
                    max_tokens = model_info['max_tokens']
                elif 'context_length' in model_info:
                    max_tokens = model_info['context_length']
                elif 'meta' in model_info and 'max_tokens' in model_info['meta']:
                    max_tokens = model_info['meta']['max_tokens']
                elif 'capabilities' in model_info and 'max_tokens' in model_info['capabilities']:
                    max_tokens = model_info['capabilities']['max_tokens']
                
                if max_tokens:
                    logger.info(f"Model {model_id} max_tokens: {max_tokens}")
                    # Update the max_tokens field in settings dialog if open
                    # Store in main settings for later use
                    self.settings["max_tokens"] = max_tokens
                    
                    # If settings dialog is open, update the field
                    if hasattr(self, '_settings_dialog') and self._settings_dialog:
                        try:
                            self._settings_dialog.max_tokens_entry.delete(0, 'end')
                            self._settings_dialog.max_tokens_entry.insert(0, str(max_tokens))
                            self.after(0, lambda: self._update_status(f"Max tokens для {model_id}: {max_tokens}"))
                        except Exception as e:
                            logger.error(f"Failed to update settings dialog: {e}")
                    else:
                        self.after(0, lambda: self._update_status(f"Max tokens для {model_id}: {max_tokens}"))
                else:
                    logger.warning(f"Could not find max_tokens in model info for {model_id}")
        except Exception as e:
            logger.error(f"Error fetching model parameters: {e}")
    
    def _on_model_selected(self, selected_model: str):
        """Handle model selection from dropdown."""
        if selected_model and selected_model not in ("Select model...", "No connection"):
            self.settings["model_name"] = selected_model
            self._update_status(f"Model selected: {selected_model}")
            # Update connect button to show Refresh since we have a model selected
            if hasattr(self, 'connect_btn'):
                self.connect_btn.configure(text="🔄 Refresh")
            
            # Fetch and apply model parameters for the newly selected model
            async def fetch_params():
                await self._fetch_and_apply_model_params(selected_model)
            
            # Run in a new thread with its own event loop
            def run_fetch():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(fetch_params())
                    loop.close()
                except Exception as e:
                    logger.error(f"Error fetching model params: {e}")
            
            thread = threading.Thread(target=run_fetch, daemon=True)
            thread.start()
    
    def _open_settings(self):
        """Open settings dialog."""
        self._settings_dialog = SettingsDialog(self, self.settings, self._save_settings)
    
    def _save_settings(self, new_settings: dict):
        """Save settings and reconnect."""
        self.settings = new_settings
        self.lmstudio_client = LMStudioClient(self.settings["lmstudio_url"])
        
        # Log tool settings
        tools_settings = self.settings.get("tools_settings", {})
        logger.info(f"Settings updated: tools={tools_settings}")
        
        self._settings_dialog = None  # Clear reference when dialog is closed
        self._check_lmstudio_connection()
        self._update_status("Настройки сохранены")
    
    def _new_task(self):
        """Create a new task/conversation."""
        if self.is_processing:
            self._update_status("Cannot create new task while processing...")
            return
        
        # Save current conversation to tasks list (optional - could be expanded)
        if self.conversation_history:
            self.tasks.append({
                "history": self.conversation_history.copy(),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "name": f"Task {len(self.tasks) + 1}"
            })
        
        # Clear current conversation
        self._clear_chat()
        self._update_status("New task created")
    
    def _clear_chat(self):
        """Clear chat history."""
        self.conversation_history.clear()
        
        # Clear UI
        for widget in self.chat_canvas.winfo_children():
            widget.destroy()
        
        self._add_welcome_message()
        self._update_status("Chat cleared")
    
    def _on_enter_pressed(self, event):
        """Handle Enter key press."""
        if event.state & 0x1:  # Shift key
            return  # Allow new line
        self._send_message()
        return "break"  # Prevent default newline
    
    def _send_message(self):
        """Send message to agent."""
        if self.is_processing:
            return
        
        message = self.input_text.get("1.0", "end-1c").strip()
        if not message:
            return
        
        # Add user message to UI
        self._add_message_bubble(message, role="user")
        self.conversation_history.append(HumanMessage(content=message))
        
        # Clear input
        self.input_text.delete("1.0", "end")
        
        # Process message
        self.is_processing = True
        self.send_btn.configure(state="disabled")
        self._update_status("Processing...")
        
        # Run in thread to avoid blocking UI
        thread = threading.Thread(target=self._process_message, args=(message,))
        thread.daemon = True
        thread.start()
    
    def _get_configured_tools(self):
        """Get tools based on current settings."""
        tools_settings = self.settings.get("tools_settings", {})
        tools = []
        
        # Get security settings
        full_access = tools_settings.get("command_full_access", False)
        allowed_commands = tools_settings.get("allowed_commands", ["ls", "dir", "cat", "head", "tail", "pwd", "echo", "find", "grep"])
        
        # Файловая система
        if tools_settings.get("filesystem_enabled", True):
            tools.extend([
                SimpleFilesystemTools.read_file,
                SimpleFilesystemTools.write_file,
                SimpleFilesystemTools.list_directory,
            ])
            logger.debug("Added filesystem tools")
        
        # Командная строка (всегда добавляем, но с проверкой прав внутри)
        if tools_settings.get("command_line_enabled", True):
            # Используем вспомогательную функцию для создания инструмента с настройками безопасности
            execute_cmd = get_execute_command_tool(
                full_access=full_access,
                allowed_commands=allowed_commands
            )
            tools.append(execute_cmd)
            logger.debug(f"Added command tool (full_access={full_access})")
        
        # Веб-поиск
        if tools_settings.get("websearch_enabled", DDGS_AVAILABLE) and DDGS_AVAILABLE:
            tools.extend([
                WebSearchTools.web_search,
                WebSearchTools.news_search,
            ])
            logger.debug("Added web search tools")
        
        # Математика
        if tools_settings.get("math_enabled", SYMPY_AVAILABLE) and SYMPY_AVAILABLE:
            tools.extend([
                MathTools.calculate,
                MathTools.solve_equation,
            ])
            logger.debug("Added math tools")
        
        # Изображения
        if tools_settings.get("image_enabled", PIL_AVAILABLE) and PIL_AVAILABLE:
            tools.append(ImageTools.get_image_info)
            logger.debug("Added image tools")
        
        logger.info(f"Total tools configured: {len(tools)}")
        return tools
    
    def _process_message(self, message: str):
        """Process message in background thread."""
        try:
            logger.info(f"Processing message: {message[:50]}...")
            
            # Get model - use selected model from dropdown if available
            model_name = self.settings.get("model_name")
            # If no model selected in settings but we have a selection from dropdown, use that
            if not model_name and hasattr(self, 'model_var'):
                selected = self.model_var.get()
                if selected and selected not in ("Select model...", "No connection"):
                    model_name = selected
            
            logger.info(f"Using model: {model_name or 'local-model'}")
            model = self.lmstudio_client.get_chat_model(
                model_name,
                self.settings["temperature"]
            )
            
            # Get tools based on current settings
            tools = self._get_configured_tools()
            
            logger.info(f"Total tools available: {len(tools)}")
            tool_names = [t.name for t in tools]
            logger.debug(f"Tool names: {tool_names}")
            
            # Store tool names for display during agent execution
            self.current_tool_names = tool_names
            
            # Create agent - use deepagents if available, otherwise basic LangGraph
            if DEEPAGENTS_AVAILABLE:
                # Use full DeepAgents with all features
                logger.info("Creating DeepAgent with all tools")
                agent = create_deep_agent(
                    model=model,
                    tools=tools,
                    system_prompt=(
                        "You are a helpful AI assistant with access to multiple tools including:\n"
                        "- Filesystem operations (read/write files, list directories)\n"
                        "- Web search for current information\n"
                        "- Mathematical calculations and equation solving\n"
                        "- Image information retrieval\n"
                        "- Safe shell command execution\n"
                        "Always be helpful and thorough in completing tasks. Use tools when appropriate."
                    )
                )
            else:
                # Fallback to basic LangGraph ReAct agent
                logger.info("Creating LangGraph ReAct agent (deepagents not available)")
                from langgraph.prebuilt import create_react_agent
                agent = create_react_agent(model, tools)
            
            # Run agent with tool call tracking
            config = {"recursion_limit": 100}
            logger.info("Invoking agent...")
            
            # Track tool usage for display
            self.after(0, lambda: self._update_status(f"Processing... Tools: {', '.join(self.current_tool_names[:3])}..."))
            
            response = agent.invoke(
                {"messages": self.conversation_history},
                config=config
            )
            logger.info("Agent invocation complete")
            
            # Get assistant response
            assistant_message = response["messages"][-1]
            assistant_content = assistant_message.content if hasattr(assistant_message, 'content') else str(assistant_message)
            logger.info(f"Response length: {len(assistant_content)} characters")
            
            # Add to history
            self.conversation_history.append(AIMessage(content=assistant_content))
            
            # Update UI in main thread
            self.after(0, lambda: self._display_assistant_response(assistant_content))
            
        except Exception as e:
            logger.error(f"Message processing failed: {str(e)}", exc_info=True)
            error_msg = f"Error: {str(e)}\n\nPlease ensure LM Studio is running and a model is loaded."
            self.after(0, lambda: self._display_assistant_response(error_msg))
        
        finally:
            self.is_processing = False
            self.after(0, lambda: self.send_btn.configure(state="normal"))
            self.after(0, lambda: self._update_status("Ready"))
    
    def _display_assistant_response(self, content: str):
        """Display assistant response in chat."""
        bubble = self._add_message_bubble(content, role="assistant")
        
        # Store reference for potential updates
        self.current_bubble = bubble


def main():
    """Main entry point."""
    app = DeepAgentsGUI()
    app.mainloop()


if __name__ == "__main__":
    main()

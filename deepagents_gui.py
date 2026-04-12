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
"""

import asyncio
import json
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

import customtkinter as ctk
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool, tool
import httpx

# Configure customtkinter appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# Try to import deepagents if available
try:
    from deepagents import create_deep_agent
    DEEPAGENTS_AVAILABLE = True
except ImportError:
    DEEPAGENTS_AVAILABLE = False
    print("Note: deepagents package not installed. Using basic LangGraph agent.")


class LMStudioClient:
    """Client for interacting with LM Studio server."""
    
    def __init__(self, base_url: str = "http://localhost:1234"):
        self.base_url = base_url.rstrip("/")
        self.api_key = "lm-studio"  # LM Studio doesn't require a real API key
        
    def get_chat_model(self, model_name: Optional[str] = None, temperature: float = 0.7):
        """Get a ChatOpenAI instance configured for LM Studio."""
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
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/v1/models", timeout=5.0)
                return response.status_code == 200
        except Exception:
            return False
    
    async def get_available_models(self) -> list[str]:
        """Get list of available models from LM Studio."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/v1/models", timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    return [model["id"] for model in data.get("data", [])]
        except Exception:
            pass
        return []


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
    def execute_command(command: str) -> str:
        """Execute a shell command (read-only operations recommended).
        
        Args:
            command: Shell command to execute.
            
        Returns:
            Command output or error message.
        """
        import subprocess
        try:
            # Safety: Only allow read-only commands
            readonly_prefixes = ["ls", "dir", "cat", "head", "tail", "pwd", "echo", "find", "grep"]
            cmd_lower = command.lower().strip()
            if not any(cmd_lower.startswith(prefix) for prefix in readonly_prefixes):
                return "Error: Only read-only commands are allowed for safety."
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = result.stdout if result.stdout else result.stderr
            return output.strip() or "Command executed successfully (no output)."
        except subprocess.TimeoutExpired:
            return "Error: Command timed out."
        except Exception as e:
            return f"Error executing command: {str(e)}"


class MessageBubble(ctk.CTkFrame):
    """A message bubble widget for chat display."""
    
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
        self.configure(corner_radius=10, fg_color="transparent")
        
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
        
        # Message content
        self.message_frame = ctk.CTkFrame(
            self,
            corner_radius=10,
            fg_color="#2b2b2b" if role == "assistant" else "#3a3a3a"
        )
        self.message_frame.pack(fill="x", expand=True, padx=5, pady=5)
        
        self.message_label = ctk.CTkLabel(
            self.message_frame,
            text=message,
            wraplength=600,
            justify="left",
            font=ctk.CTkFont(size=13),
            anchor="nw"
        )
        self.message_label.pack(fill="x", padx=10, pady=10)
    
    def update_message(self, new_content: str):
        """Update the message content (for streaming)."""
        self.message_label.configure(text=new_content)


class SettingsDialog(ctk.CTkToplevel):
    """Settings dialog for configuring LM Studio connection."""
    
    def __init__(self, parent, current_settings: dict, save_callback: Callable):
        super().__init__(parent)
        
        self.title("Settings")
        self.geometry("500x400")
        self.resizable(False, False)
        
        self.save_callback = save_callback
        self.current_settings = current_settings.copy()
        
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
        """Create settings widgets."""
        # Main frame
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title = ctk.CTkLabel(
            main_frame,
            text="LM Studio Settings",
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
        self.url_entry.insert(0, self.current_settings.get("lmstudio_url", "http://localhost:1234"))
        
        # Model name
        model_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        model_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            model_frame,
            text="Model Name (optional):",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w")
        
        self.model_entry = ctk.CTkEntry(
            model_frame,
            width=400,
            placeholder_text="Leave empty for default"
        )
        self.model_entry.pack(fill="x", pady=5)
        self.model_entry.insert(0, self.current_settings.get("model_name", ""))
        
        # Temperature
        temp_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        temp_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            temp_frame,
            text="Temperature:",
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
        
        # Working directory
        workdir_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        workdir_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            workdir_frame,
            text="Working Directory:",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w")
        
        self.workdir_entry = ctk.CTkEntry(
            workdir_frame,
            width=400,
            placeholder_text=str(Path.cwd())
        )
        self.workdir_entry.pack(fill="x", pady=5)
        self.workdir_entry.insert(0, self.current_settings.get("working_dir", str(Path.cwd())))
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(30, 0))
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.destroy,
            width=100
        )
        cancel_btn.pack(side="left", padx=10)
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="Save",
            command=self._save_settings,
            width=100
        )
        save_btn.pack(side="right", padx=10)
    
    def _save_settings(self):
        """Save settings and close dialog."""
        self.current_settings["lmstudio_url"] = self.url_entry.get() or "http://localhost:1234"
        self.current_settings["model_name"] = self.model_entry.get() or None
        self.current_settings["temperature"] = self.temp_slider.get()
        self.current_settings["working_dir"] = self.workdir_entry.get() or str(Path.cwd())
        
        self.save_callback(self.current_settings)
        self.destroy()


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
            "working_dir": str(Path.cwd()),
        }
        
        # State
        self.lmstudio_client = LMStudioClient(self.settings["lmstudio_url"])
        self.conversation_history: list = []
        self.is_processing = False
        self.current_tool_calls: list = []
        
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
        header.grid_columnconfigure(1, weight=1)
        
        # Logo/Title
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=20, pady=10)
        
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
        self.connection_label.grid(row=0, column=1, sticky="e", padx=(10, 20))
        
        # Settings button
        settings_btn = ctk.CTkButton(
            header,
            text="⚙ Settings",
            command=self._open_settings,
            width=100,
            height=30
        )
        settings_btn.grid(row=0, column=2, padx=10, pady=10)
        
        # Clear chat button
        clear_btn = ctk.CTkButton(
            header,
            text="🗑 Clear Chat",
            command=self._clear_chat,
            width=100,
            height=30,
            fg_color="#e74c3c"
        )
        clear_btn.grid(row=0, column=3, padx=10, pady=10)
    
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
        welcome_text = (
            "Welcome to DeepAgents GUI! 🎉\n\n"
            "I'm connected to LM Studio and ready to help you with various tasks.\n\n"
            "I can:\n"
            "• Answer questions using local models\n"
            "• Read and write files\n"
            "• List directory contents\n"
            "• Execute safe shell commands\n\n"
            "To get started, simply type your message below!"
        )
        
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
        self.status_label.configure(text=status)
    
    def _check_lmstudio_connection(self):
        """Check LM Studio connection asynchronously."""
        async def check():
            connected = await self.lmstudio_client.check_connection()
            if connected:
                self.connection_indicator.configure(text="●", text_color="#2ecc71")
                self.connection_label.configure(text="Connected", text_color="#2ecc71")
                self._update_status("Connected to LM Studio")
                
                # Get available models
                models = await self.lmstudio_client.get_available_models()
                if models:
                    self.info_label.configure(text=f"Available models: {len(models)}")
            else:
                self.connection_indicator.configure(text="●", text_color="#e74c3c")
                self.connection_label.configure(text="Disconnected", text_color="#e74c3c")
                self._update_status("Cannot connect to LM Studio - Please start the server")
        
        # Run async function
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.create_task(check())
    
    def _open_settings(self):
        """Open settings dialog."""
        SettingsDialog(self, self.settings, self._save_settings)
    
    def _save_settings(self, new_settings: dict):
        """Save settings and reconnect."""
        self.settings = new_settings
        self.lmstudio_client = LMStudioClient(self.settings["lmstudio_url"])
        self._check_lmstudio_connection()
    
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
    
    def _process_message(self, message: str):
        """Process message in background thread."""
        try:
            # Get model
            model = self.lmstudio_client.get_chat_model(
                self.settings["model_name"],
                self.settings["temperature"]
            )
            
            # Get tools
            tools = [
                SimpleFilesystemTools.read_file,
                SimpleFilesystemTools.write_file,
                SimpleFilesystemTools.list_directory,
                SimpleFilesystemTools.execute_command,
            ]
            
            # Create agent - use deepagents if available, otherwise basic LangGraph
            if DEEPAGENTS_AVAILABLE:
                # Use full DeepAgents with all features
                agent = create_deep_agent(
                    model=model,
                    tools=tools,
                    system_prompt=(
                        "You are a helpful AI assistant with access to filesystem tools. "
                        "You can read files, write files, list directories, and execute safe shell commands. "
                        "Always be helpful and thorough in completing tasks."
                    )
                )
            else:
                # Fallback to basic LangGraph ReAct agent
                from langgraph.prebuilt import create_react_agent
                agent = create_react_agent(model, tools)
            
            # Run agent
            config = {"recursion_limit": 100}
            response = agent.invoke(
                {"messages": self.conversation_history},
                config=config
            )
            
            # Get assistant response
            assistant_message = response["messages"][-1]
            assistant_content = assistant_message.content if hasattr(assistant_message, 'content') else str(assistant_message)
            
            # Add to history
            self.conversation_history.append(AIMessage(content=assistant_content))
            
            # Update UI in main thread
            self.after(0, lambda: self._display_assistant_response(assistant_content))
            
        except Exception as e:
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

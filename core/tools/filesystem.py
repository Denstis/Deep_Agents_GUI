"""
Filesystem Tools - File operations and command execution for DeepAgents
"""

import logging
import subprocess
from pathlib import Path
from typing import List, Optional
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


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
    def execute_command(
        command: str, 
        full_access: bool = False, 
        allowed_commands: Optional[List[str]] = None
    ) -> str:
        """Execute a shell command with configurable security.
        
        Args:
            command: Shell command to execute.
            full_access: If True, allow any command (dangerous!).
            allowed_commands: List of allowed command prefixes (used when full_access=False).
            
        Returns:
            Command output or error message.
        """
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


def get_execute_command_tool(
    full_access: bool = False, 
    allowed_commands: Optional[List[str]] = None
):
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
    
    # Get the underlying function from the tool descriptor
    base_func = SimpleFilesystemTools.execute_command.func
    
    # Create a wrapper function instead of partial to maintain introspection capability
    def execute_cmd_wrapper(command: str) -> str:
        return base_func(command=command, full_access=full_access, allowed_commands=allowed_commands)
    
    # Copy metadata from the original tool (required for LangChain tool system)
    execute_cmd_wrapper.__name__ = 'execute_command'
    execute_cmd_wrapper.__doc__ = SimpleFilesystemTools.execute_command.__doc__
    
    return execute_cmd_wrapper

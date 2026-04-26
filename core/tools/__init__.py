"""
Tools Package - Filesystem, Web Search, Math, and Console Command Tools for DeepAgents
"""

from core.tools.filesystem import SimpleFilesystemTools, get_execute_command_tool
from core.tools.websearch import WebSearchTools
from core.tools.math import MathTools
from core.tools.console_command import ConsoleCommandTool, get_console_command_tool, create_console_tools

__all__ = [
    "SimpleFilesystemTools",
    "get_execute_command_tool",
    "WebSearchTools",
    "MathTools",
    "ConsoleCommandTool",
    "get_console_command_tool",
    "create_console_tools",
]


# Legacy compatibility layer for existing tests
# These classes wrap the new modular tools for backward compatibility
class ReadFileTool:
    """Wrapper for backward compatibility."""
    risk_level = "safe"
    name = "read_file"
    
    def invoke(self, args):
        return SimpleFilesystemTools.read_file.func(args.get("file_path", ""))


class WriteFileTool:
    """Wrapper for backward compatibility."""
    risk_level = "review"
    name = "write_file"
    
    def invoke(self, args):
        return SimpleFilesystemTools.write_file.func(
            args.get("file_path", ""), 
            args.get("content", "")
        )


class ListDirectoryTool:
    """Wrapper for backward compatibility."""
    risk_level = "safe"
    name = "list_directory"
    
    def invoke(self, args):
        return SimpleFilesystemTools.list_directory.func(args.get("dir_path", "."))


class ExecuteCommandTool:
    """Wrapper for backward compatibility."""
    risk_level = "review"
    name = "execute_command"
    
    def __init__(self):
        self._func = get_execute_command_tool()
    
    def invoke(self, args):
        return self._func(args.get("command", ""))


# Pydantic models for schema validation (stubs for now)
class ReadFileArgs:
    def __init__(self, file_path: str):
        self.file_path = file_path


class WriteFileArgs:
    def __init__(self, file_path: str, content: str):
        if len(content) > 1000000:
            raise ValueError("Content exceeds 1MB limit")
        self.file_path = file_path
        self.content = content


class ListDirectoryArgs:
    def __init__(self, dir_path: str = "."):
        self.dir_path = dir_path


class ExecuteCommandArgs:
    def __init__(self, command: str):
        if len(command) > 500:
            raise ValueError("Command exceeds 500 character limit")
        self.command = command


def create_filesystem_tools(enabled=None):
    """Create filesystem tools for backward compatibility."""
    all_tools = {
        "read_file": ReadFileTool(),
        "write_file": WriteFileTool(),
        "list_directory": ListDirectoryTool(),
        "execute_command": ExecuteCommandTool(),
    }
    
    if enabled:
        return [all_tools[name] for name in enabled if name in all_tools]
    return list(all_tools.values())


def get_all_tool_metadata():
    """Get metadata for all tools."""
    return [
        {
            "name": "read_file",
            "description": "Read contents of a file",
            "risk_level": "safe",
            "args_schema": {"file_path": "string"}
        },
        {
            "name": "write_file",
            "description": "Write content to a file",
            "risk_level": "review",
            "args_schema": {"file_path": "string", "content": "string"}
        },
        {
            "name": "list_directory",
            "description": "List contents of a directory",
            "risk_level": "safe",
            "args_schema": {"dir_path": "string"}
        },
        {
            "name": "execute_command",
            "description": "Execute a shell command",
            "risk_level": "review",
            "args_schema": {"command": "string"}
        },
    ]

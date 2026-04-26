"""
Console Command Tool - Execute shell commands and return output to the agent
"""

import logging
import subprocess
import shlex
from typing import Optional, Dict, Any
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


class ConsoleCommandTool:
    """Tool for executing console commands and returning output to the agent."""
    
    risk_level = "review"
    name = "console_command"
    
    @staticmethod
    def execute(
        command: str,
        working_dir: Optional[str] = None,
        timeout: int = 60,
        shell: bool = True,
        capture_stderr: bool = True
    ) -> Dict[str, Any]:
        """Execute a console command and return structured output to the agent.
        
        Args:
            command: The shell command to execute.
            working_dir: Working directory for command execution (default: current dir).
            timeout: Maximum execution time in seconds (default: 60).
            shell: If True, execute through shell (default: True).
            capture_stderr: If True, capture stderr along with stdout (default: True).
            
        Returns:
            Dictionary with command execution results:
            - success: Boolean indicating if command succeeded
            - stdout: Standard output from the command
            - stderr: Standard error from the command (if captured)
            - return_code: Exit code of the command
            - command: The executed command
            - error: Error message if execution failed
        """
        result = {
            "success": False,
            "stdout": "",
            "stderr": "",
            "return_code": -1,
            "command": command,
            "error": None
        }
        
        try:
            logger.info(f"Executing command: {command}")
            
            # Prepare command execution
            cmd_args = command if shell else shlex.split(command)
            
            # Execute command
            proc_result = subprocess.run(
                cmd_args,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=working_dir,
                errors='replace'  # Handle encoding errors gracefully
            )
            
            # Populate result
            result["stdout"] = proc_result.stdout.strip() if proc_result.stdout else ""
            result["stderr"] = proc_result.stderr.strip() if proc_result.stderr and capture_stderr else ""
            result["return_code"] = proc_result.returncode
            result["success"] = (proc_result.returncode == 0)
            
            logger.debug(
                f"Command completed: return_code={proc_result.returncode}, "
                f"stdout_len={len(result['stdout'])}, stderr_len={len(result['stderr'])}"
            )
            
        except subprocess.TimeoutExpired as e:
            error_msg = f"Command timed out after {timeout} seconds"
            result["error"] = error_msg
            result["stdout"] = e.stdout.strip() if e.stdout else ""
            result["stderr"] = e.stderr.strip() if e.stderr and capture_stderr else ""
            logger.error(error_msg)
            
        except FileNotFoundError as e:
            error_msg = f"Command not found: {command}"
            result["error"] = error_msg
            logger.error(error_msg)
            
        except PermissionError as e:
            error_msg = f"Permission denied: {command}"
            result["error"] = error_msg
            logger.error(error_msg)
            
        except Exception as e:
            error_msg = f"Execution failed: {str(e)}"
            result["error"] = error_msg
            logger.error(error_msg)
        
        return result
    
    @staticmethod
    def execute_simple(command: str, timeout: int = 30) -> str:
        """Execute a simple console command and return combined output as string.
        
        This is a simplified version that returns a single string with both
        stdout and stderr combined, suitable for quick commands.
        
        Args:
            command: The shell command to execute.
            timeout: Maximum execution time in seconds (default: 30).
            
        Returns:
            Combined output (stdout + stderr) as a string, or error message.
        """
        try:
            logger.info(f"Executing simple command: {command}")
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                errors='replace'
            )
            
            output = []
            if result.stdout:
                output.append(result.stdout.strip())
            if result.stderr:
                output.append(f"STDERR: {result.stderr.strip()}")
            
            combined = "\n".join(output) if output else "Command executed successfully (no output)"
            
            if result.returncode != 0:
                combined = f"[Exit code: {result.returncode}]\n{combined}"
            
            logger.debug(f"Simple command completed, output length: {len(combined)}")
            return combined
            
        except subprocess.TimeoutExpired:
            error_msg = f"Command timed out after {timeout} seconds"
            logger.error(error_msg)
            return f"Error: {error_msg}"
        except Exception as e:
            error_msg = f"Error executing command: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"


# Create tool decorators separately
@tool
def execute_command_tool(
    command: str,
    working_dir: Optional[str] = None,
    timeout: int = 60,
    shell: bool = True,
    capture_stderr: bool = True
) -> Dict[str, Any]:
    """Execute a console command and return structured output to the agent.
    
    Args:
        command: The shell command to execute.
        working_dir: Working directory for command execution (default: current dir).
        timeout: Maximum execution time in seconds (default: 60).
        shell: If True, execute through shell (default: True).
        capture_stderr: If True, capture stderr along with stdout (default: True).
        
    Returns:
        Dictionary with command execution results:
        - success: Boolean indicating if command succeeded
        - stdout: Standard output from the command
        - stderr: Standard error from the command (if captured)
        - return_code: Exit code of the command
        - command: The executed command
        - error: Error message if execution failed
    """
    return ConsoleCommandTool.execute(command, working_dir, timeout, shell, capture_stderr)


@tool
def execute_simple_command_tool(command: str, timeout: int = 30) -> str:
    """Execute a simple console command and return combined output as string.
    
    This is a simplified version that returns a single string with both
    stdout and stderr combined, suitable for quick commands.
    
    Args:
        command: The shell command to execute.
        timeout: Maximum execution time in seconds (default: 30).
        
    Returns:
        Combined output (stdout + stderr) as a string, or error message.
    """
    return ConsoleCommandTool.execute_simple(command, timeout)


def get_console_command_tool(
    default_timeout: int = 60,
    default_working_dir: Optional[str] = None,
    safe_mode: bool = True,
    allowed_commands: Optional[list] = None
):
    """Create a configured console command tool with security settings.
    
    Args:
        default_timeout: Default timeout for command execution.
        default_working_dir: Default working directory for commands.
        safe_mode: If True, restrict commands to allowed list.
        allowed_commands: List of allowed command prefixes when safe_mode=True.
        
    Returns:
        A configured tool function for executing console commands.
    """
    from functools import partial
    
    if allowed_commands is None:
        allowed_commands = [
            "ls", "dir", "cat", "head", "tail", "pwd", "echo", 
            "find", "grep", "whoami", "date", "uname", "ps", "top",
            "cd", "mkdir", "rm", "cp", "mv", "chmod", "chown"
        ]
    
    def execute_with_security(command: str, **kwargs) -> Dict[str, Any]:
        """Wrapper that adds security checks before execution."""
        
        # Security check in safe mode
        if safe_mode:
            cmd_lower = command.lower().strip()
            base_cmd = cmd_lower.split()[0] if cmd_lower else ""
            
            if not any(base_cmd == prefix or cmd_lower.startswith(prefix + " ") for prefix in allowed_commands):
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "",
                    "return_code": -1,
                    "command": command,
                    "error": f"Command '{command}' is not allowed in safe mode.\nAllowed: {', '.join(allowed_commands)}"
                }
        
        # Set defaults
        if 'timeout' not in kwargs:
            kwargs['timeout'] = default_timeout
        if 'working_dir' not in kwargs or kwargs['working_dir'] is None:
            kwargs['working_dir'] = default_working_dir
        
        # Execute command
        return ConsoleCommandTool.execute(command, **kwargs)
    
    # Copy metadata
    execute_with_security.__name__ = 'console_command'
    execute_with_security.__doc__ = ConsoleCommandTool.execute.__doc__
    
    return execute_with_security


# Legacy compatibility
def create_console_tools(safe_mode: bool = True):
    """Create console command tools for backward compatibility."""
    tools = []
    
    # Add structured command tool
    exec_tool = get_console_command_tool(safe_mode=safe_mode)
    tools.append(type('ConsoleCommandToolInstance', (), {
        'risk_level': 'review',
        'name': 'console_command',
        'invoke': lambda self, args: exec_tool(args.get('command', ''))
    })())
    
    # Add simple command tool wrapper
    tools.append(type('SimpleConsoleCommandToolInstance', (), {
        'risk_level': 'review',
        'name': 'console_command_simple',
        'invoke': lambda self, args: ConsoleCommandTool.execute_simple(
            args.get('command', ''),
            args.get('timeout', 30)
        )
    })())
    
    return tools

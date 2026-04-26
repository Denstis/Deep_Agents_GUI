"""
DeepAgents Package - Modular AI Agent System with LM Studio Integration
"""

__version__ = "1.0.0"
__author__ = "DeepAgents Team"

# Re-export key components for convenience
from core.utils import LMStudioClient
from core.tools import (
    SimpleFilesystemTools,
    get_execute_command_tool,
    WebSearchTools,
    MathTools,
)

__all__ = [
    "LMStudioClient",
    "SimpleFilesystemTools",
    "get_execute_command_tool",
    "WebSearchTools",
    "MathTools",
]

"""
GUI Tool Manager - Real integration with core tools
Manages tool registration, enabling/disabling, and execution.
"""
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import logging

from langchain_core.tools import BaseTool
from core.tools import get_all_tools, get_tool_categories, get_tool_by_name

logger = logging.getLogger(__name__)


@dataclass
class ToolInfo:
    """Information about a tool"""
    name: str
    description: str
    category: str
    enabled: bool = True
    risk_level: str = "safe"  # safe, review, dangerous
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "enabled": self.enabled,
            "risk_level": self.risk_level
        }


class ToolManager:
    """
    Manages LangChain tools with real functionality.
    Handles registration, state, and execution callbacks.
    """
    
    # Risk classification for tools
    RISK_LEVELS = {
        "file_read": "safe",
        "file_write": "review",
        "file_list": "safe",
        "console_execute": "dangerous",
        "web_search": "safe",
        "web_fetch": "safe",
        "python_execute": "review",
        "math_evaluate": "safe",
        "get_current_time": "safe",
        "get_system_info": "safe"
    }
    
    def __init__(self, callback: Optional[Callable[[str, Dict], None]] = None):
        self.callback = callback
        self.tools: Dict[str, ToolInfo] = {}
        self.tool_instances: Dict[str, BaseTool] = {}
        self._lock = threading.Lock()
        
        # Initialize with all available tools
        self._load_tools()
    
    def _load_tools(self):
        """Load all available tools"""
        all_tools = get_all_tools()
        categories = get_tool_categories()
        
        # Create category lookup
        category_map = {}
        for cat, tool_names in categories.items():
            for name in tool_names:
                category_map[name] = cat
        
        for tool in all_tools:
            info = ToolInfo(
                name=tool.name,
                description=tool.description or "No description",
                category=category_map.get(tool.name, "other"),
                enabled=True,
                risk_level=self.RISK_LEVELS.get(tool.name, "review")
            )
            self.tools[tool.name] = info
            self.tool_instances[tool.name] = tool
            
        logger.info(f"Loaded {len(self.tools)} tools")
        
        if self.callback:
            self.callback("tools_loaded", {"count": len(self.tools)})
    
    def get_enabled_tools(self) -> List[BaseTool]:
        """Get list of enabled tool instances for agent use"""
        with self._lock:
            return [
                self.tool_instances[name]
                for name, info in self.tools.items()
                if info.enabled
            ]
    
    def get_all_tools_info(self) -> List[Dict[str, Any]]:
        """Get information about all tools"""
        with self._lock:
            return [info.to_dict() for info in self.tools.values()]
    
    def get_tools_by_category(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get tools organized by category"""
        result = {}
        with self._lock:
            for info in self.tools.values():
                if info.category not in result:
                    result[info.category] = []
                result[info.category].append(info.to_dict())
        return result
    
    def enable_tool(self, tool_name: str) -> bool:
        """Enable a tool"""
        with self._lock:
            if tool_name in self.tools:
                self.tools[tool_name].enabled = True
                logger.info(f"Enabled tool: {tool_name}")
                if self.callback:
                    self.callback("tool_enabled", {"name": tool_name})
                return True
        return False
    
    def disable_tool(self, tool_name: str) -> bool:
        """Disable a tool"""
        with self._lock:
            if tool_name in self.tools:
                self.tools[tool_name].enabled = False
                logger.info(f"Disabled tool: {tool_name}")
                if self.callback:
                    self.callback("tool_disabled", {"name": tool_name})
                return True
        return False
    
    def toggle_tool(self, tool_name: str) -> bool:
        """Toggle tool enabled state"""
        with self._lock:
            if tool_name in self.tools:
                self.tools[tool_name].enabled = not self.tools[tool_name].enabled
                state = self.tools[tool_name].enabled
                logger.info(f"Toggled tool {tool_name} to {'enabled' if state else 'disabled'}")
                if self.callback:
                    self.callback("tool_toggled", {"name": tool_name, "enabled": state})
                return state
        return False
    
    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a tool directly (for testing/manual use).
        Returns result dict with success status.
        """
        with self._lock:
            if tool_name not in self.tool_instances:
                return {
                    "success": False,
                    "error": f"Tool not found: {tool_name}"
                }
            
            if not self.tools[tool_name].enabled:
                return {
                    "success": False,
                    "error": f"Tool is disabled: {tool_name}"
                }
        
        tool = self.tool_instances[tool_name]
        
        try:
            # Execute tool
            result = tool.invoke(kwargs)
            
            if self.callback:
                self.callback("tool_executed", {
                    "name": tool_name,
                    "args": kwargs,
                    "result": result
                })
            
            return {
                "success": True,
                "result": result,
                "tool": tool_name
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Tool execution failed: {error_msg}")
            
            if self.callback:
                self.callback("tool_error", {
                    "name": tool_name,
                    "args": kwargs,
                    "error": error_msg
                })
            
            return {
                "success": False,
                "error": error_msg,
                "tool": tool_name
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get tool usage statistics"""
        with self._lock:
            total = len(self.tools)
            enabled = sum(1 for t in self.tools.values() if t.enabled)
            disabled = total - enabled
            
            by_risk = {}
            for info in self.tools.values():
                risk = info.risk_level
                if risk not in by_risk:
                    by_risk[risk] = 0
                by_risk[risk] += 1
            
            return {
                "total_tools": total,
                "enabled": enabled,
                "disabled": disabled,
                "by_risk_level": by_risk,
                "categories": list(set(t.category for t in self.tools.values()))
            }
    
    def reset_tools(self):
        """Reset all tools to enabled state"""
        with self._lock:
            for info in self.tools.values():
                info.enabled = True
            
        logger.info("Reset all tools to enabled")
        if self.callback:
            self.callback("tools_reset", {})

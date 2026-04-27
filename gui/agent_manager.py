"""
GUI Agent Manager - Real integration with DeepAgent
Manages agent creation, configuration, and execution.
"""
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import logging

from core.agent import DeepAgent, AgentStatus
from core.tools import get_all_tools
from gui.tool_manager import ToolManager

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Configuration for an agent"""
    name: str
    role: str
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    system_prompt: Optional[str] = None
    max_iterations: int = 15
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "model": self.model,
            "temperature": self.temperature,
            "system_prompt": self.system_prompt,
            "max_iterations": self.max_iterations
        }


@dataclass
class AgentStats:
    """Statistics for an agent"""
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_tool_calls: int = 0
    total_tokens_used: int = 0
    avg_execution_time: float = 0.0
    last_active: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "total_tool_calls": self.total_tool_calls,
            "total_tokens_used": self.total_tokens_used,
            "avg_execution_time": self.avg_execution_time,
            "last_active": self.last_active.isoformat() if self.last_active else None
        }


class AgentManager:
    """
    Manages multiple DeepAgents with real LangChain integration.
    Handles lifecycle, configuration, and monitoring.
    """
    
    DEFAULT_ROLES = [
        {"name": "assistant", "role": "General Assistant", "prompt": "You are a helpful general-purpose assistant."},
        {"name": "researcher", "role": "Research Specialist", "prompt": "You are a research specialist. Gather information, search the web, and analyze data thoroughly."},
        {"name": "coder", "role": "Software Developer", "prompt": "You are an expert software developer. Write clean, efficient, well-documented code."},
        {"name": "writer", "role": "Content Writer", "prompt": "You are a professional content writer. Create clear, engaging, well-structured content."},
        {"name": "reviewer", "role": "Quality Reviewer", "prompt": "You are a quality reviewer. Critically analyze work for accuracy and quality."},
        {"name": "planner", "role": "Task Planner", "prompt": "You are a strategic planner. Break down complex tasks into manageable steps."}
    ]
    
    def __init__(
        self,
        tool_manager: Optional[ToolManager] = None,
        llm_config: Optional[Dict[str, Any]] = None,
        callback: Optional[Callable[[str, Dict], None]] = None
    ):
        self.callback = callback
        self.llm_config = llm_config or {"model_name": "gpt-4o-mini"}
        self.tool_manager = tool_manager
        self.agents: Dict[str, DeepAgent] = {}
        self.configs: Dict[str, AgentConfig] = {}
        self.stats: Dict[str, AgentStats] = {}
        self._lock = threading.Lock()
        
        # Track active executions
        self._active_executions: Dict[str, bool] = {}
    
    def _create_agent_callback(self, agent_name: str) -> Callable[[str, Any], None]:
        """Create a callback handler for a specific agent"""
        def handler(event_type: str, data: Any):
            if self.callback:
                self.callback("agent_event", {
                    "agent": agent_name,
                    "event": event_type,
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Update stats based on events
            with self._lock:
                if agent_name in self.stats:
                    stats = self.stats[agent_name]
                    stats.last_active = datetime.now()
                    
                    if event_type == "task_complete":
                        stats.tasks_completed += 1
                    elif event_type == "tool_call":
                        stats.total_tool_calls += 1
                    elif event_type == "error":
                        stats.tasks_failed += 1
        
        return handler
    
    def create_agent(self, config: AgentConfig) -> bool:
        """Create a new agent with given configuration"""
        with self._lock:
            if config.name in self.agents:
                logger.warning(f"Agent already exists: {config.name}")
                return False
            
            try:
                # Get enabled tools
                tools = []
                if self.tool_manager:
                    tools = self.tool_manager.get_enabled_tools()
                
                # Create agent
                agent = DeepAgent(
                    name=config.name,
                    role=config.role,
                    model_name=config.model,
                    temperature=config.temperature,
                    system_prompt=config.system_prompt,
                    tools=tools,
                    callback=self._create_agent_callback(config.name)
                )
                
                self.agents[config.name] = agent
                self.configs[config.name] = config
                self.stats[config.name] = AgentStats()
                
                logger.info(f"Created agent: {config.name} ({config.role})")
                
                if self.callback:
                    self.callback("agent_created", {
                        "name": config.name,
                        "role": config.role,
                        "config": config.to_dict()
                    })
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to create agent: {e}")
                if self.callback:
                    self.callback("agent_error", {
                        "name": config.name,
                        "error": str(e)
                    })
                return False
    
    def remove_agent(self, agent_name: str) -> bool:
        """Remove an agent"""
        with self._lock:
            if agent_name not in self.agents:
                return False
            
            del self.agents[agent_name]
            del self.configs[agent_name]
            if agent_name in self.stats:
                del self.stats[agent_name]
            
            logger.info(f"Removed agent: {agent_name}")
            
            if self.callback:
                self.callback("agent_removed", {"name": agent_name})
            
            return True
    
    def get_agent(self, agent_name: str) -> Optional[DeepAgent]:
        """Get an agent by name"""
        with self._lock:
            return self.agents.get(agent_name)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all agents with their status"""
        result = []
        with self._lock:
            for name, agent in self.agents.items():
                config = self.configs.get(name, AgentConfig(name, "Unknown"))
                stats = self.stats.get(name, AgentStats())
                
                result.append({
                    "name": name,
                    "role": config.role,
                    "model": config.model,
                    "status": agent.get_status()["status"],
                    "config": config.to_dict(),
                    "stats": stats.to_dict()
                })
        return result
    
    def execute_task(
        self,
        agent_name: str,
        task: str,
        async_mode: bool = False
    ) -> Dict[str, Any]:
        """Execute a task with specified agent"""
        with self._lock:
            if agent_name not in self.agents:
                return {
                    "success": False,
                    "error": f"Agent not found: {agent_name}"
                }
            
            if agent_name in self._active_executions and self._active_executions[agent_name]:
                return {
                    "success": False,
                    "error": f"Agent {agent_name} is already executing a task"
                }
            
            self._active_executions[agent_name] = True
            agent = self.agents[agent_name]
        
        try:
            # Reset agent state
            agent.reset()
            
            # Execute task
            start_time = datetime.now()
            result_state = agent.run(task)
            end_time = datetime.now()
            
            # Update stats
            with self._lock:
                if agent_name in self.stats:
                    stats = self.stats[agent_name]
                    execution_time = (end_time - start_time).total_seconds()
                    
                    # Update average execution time
                    if stats.tasks_completed > 0:
                        stats.avg_execution_time = (
                            (stats.avg_execution_time * stats.tasks_completed + execution_time)
                            / (stats.tasks_completed + 1)
                        )
                    else:
                        stats.avg_execution_time = execution_time
            
            # Extract response
            messages = result_state.messages
            response = ""
            for msg in reversed(messages):
                from langchain_core.messages import AIMessage
                if isinstance(msg, AIMessage):
                    response = msg.content
                    break
            
            return {
                "success": True,
                "response": response,
                "iterations": result_state.iterations,
                "errors": result_state.errors,
                "execution_time": (end_time - start_time).total_seconds()
            }
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            with self._lock:
                self._active_executions[agent_name] = False
    
    def update_agent_tools(self, agent_name: str) -> bool:
        """Update an agent's available tools from tool manager"""
        with self._lock:
            if agent_name not in self.agents:
                return False
            
            if not self.tool_manager:
                return False
            
            agent = self.agents[agent_name]
            tools = self.tool_manager.get_enabled_tools()
            
            # Clear existing tools
            for tool_name in list(agent.tools.keys()):
                agent.unregister_tool(tool_name)
            
            # Add current enabled tools
            for tool in tools:
                agent.register_tool(tool)
            
            logger.info(f"Updated tools for agent: {agent_name}")
            return True
    
    def update_all_agents_tools(self):
        """Update tools for all agents"""
        with self._lock:
            for agent_name in list(self.agents.keys()):
                self.update_agent_tools(agent_name)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics"""
        with self._lock:
            total_agents = len(self.agents)
            active_agents = sum(
                1 for a in self.agents.values()
                if a.get_status()["status"] != "idle"
            )
            
            total_tasks = sum(s.tasks_completed + s.tasks_failed for s in self.stats.values())
            total_completed = sum(s.tasks_completed for s in self.stats.values())
            total_tool_calls = sum(s.total_tool_calls for s in self.stats.values())
            
            return {
                "total_agents": total_agents,
                "active_agents": active_agents,
                "idle_agents": total_agents - active_agents,
                "total_tasks": total_tasks,
                "total_completed": total_completed,
                "total_failed": total_tasks - total_completed,
                "total_tool_calls": total_tool_calls,
                "agents": {name: stats.to_dict() for name, stats in self.stats.items()}
            }
    
    def reset_all(self):
        """Reset all agents"""
        with self._lock:
            for agent in self.agents.values():
                agent.reset()
            for name in self._active_executions:
                self._active_executions[name] = False
        
        logger.info("Reset all agents")
        if self.callback:
            self.callback("agents_reset", {})
    
    def create_default_agents(self):
        """Create default set of specialized agents"""
        created = []
        for role_config in self.DEFAULT_ROLES:
            config = AgentConfig(
                name=role_config["name"],
                role=role_config["role"],
                system_prompt=role_config["prompt"],
                **self.llm_config
            )
            if self.create_agent(config):
                created.append(role_config["name"])
        
        logger.info(f"Created {len(created)} default agents: {created}")
        return created

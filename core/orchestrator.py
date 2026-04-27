"""
Multi-Agent Orchestrator with LangGraph
Coordinates multiple agents working together on complex tasks.
"""
import asyncio
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from core.agent import DeepAgent, AgentStatus, AgentState
from core.tools import get_all_tools

logger = logging.getLogger(__name__)


class OrchestratorMode(Enum):
    SEQUENTIAL = "sequential"  # Agents work one after another
    PARALLEL = "parallel"      # Agents work simultaneously
    HIERARCHICAL = "hierarchical"  # Manager delegates to workers


@dataclass
class Task:
    """Represents a task to be executed"""
    id: str
    description: str
    assigned_to: Optional[str] = None
    status: str = "pending"  # pending, in_progress, completed, failed
    result: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)


@dataclass
class OrchestratorState:
    """State for the orchestrator"""
    tasks: List[Task] = field(default_factory=list)
    current_task_index: int = 0
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    status: str = "idle"


class MultiAgentOrchestrator:
    """
    Orchestrates multiple DeepAgents using LangGraph workflows.
    Supports different collaboration patterns.
    """
    
    def __init__(
        self,
        mode: OrchestratorMode = OrchestratorMode.SEQUENTIAL,
        callback: Optional[Callable[[str, Any], None]] = None
    ):
        self.mode = mode
        self.callback = callback
        self.agents: Dict[str, DeepAgent] = {}
        self.state = OrchestratorState()
        self._build_graph()
    
    def add_agent(self, agent: DeepAgent):
        """Add an agent to the orchestrator"""
        self.agents[agent.name] = agent
        logger.info(f"Added agent: {agent.name}")
        if self.callback:
            self.callback("agent_added", {"name": agent.name, "role": agent.role})
    
    def remove_agent(self, agent_name: str):
        """Remove an agent from the orchestrator"""
        if agent_name in self.agents:
            del self.agents[agent_name]
            logger.info(f"Removed agent: {agent_name}")
            if self.callback:
                self.callback("agent_removed", {"name": agent_name})
    
    def add_task(self, task: Task):
        """Add a task to the queue"""
        self.state.tasks.append(task)
        if self.callback:
            self.callback("task_added", {"id": task.id, "description": task.description})
    
    def _build_graph(self):
        """Build LangGraph workflow for orchestration"""
        
        def select_next_task(state: OrchestratorState) -> str:
            """Determine which task to execute next"""
            if state.current_task_index >= len(state.tasks):
                return "end"
            
            task = state.tasks[state.current_task_index]
            
            # Check dependencies
            for dep_id in task.dependencies:
                if dep_id not in state.results:
                    return "wait"
            
            return "execute"
        
        def execute_task(state: OrchestratorState) -> OrchestratorState:
            """Execute the current task with assigned agent"""
            if state.current_task_index >= len(state.tasks):
                return state
            
            task = state.tasks[state.current_task_index]
            task.status = "in_progress"
            
            if self.callback:
                self.callback("task_started", {"id": task.id, "agent": task.assigned_to})
            
            # Find assigned agent
            if not task.assigned_to or task.assigned_to not in self.agents:
                # Use first available agent
                agent_name = list(self.agents.keys())[0] if self.agents else None
            else:
                agent_name = task.assigned_to
            
            if not agent_name:
                error_msg = "No agents available"
                task.status = "failed"
                task.result = error_msg
                state.errors.append(error_msg)
                state.current_task_index += 1
                return state
            
            agent = self.agents[agent_name]
            
            try:
                # Run agent with task description
                result_state = agent.run(task.description)
                
                # Extract final response
                messages = result_state.messages
                final_response = ""
                for msg in reversed(messages):
                    if isinstance(msg, AIMessage):
                        final_response = msg.content
                        break
                
                task.result = final_response
                task.status = "completed"
                state.results[task.id] = final_response
                
                if self.callback:
                    self.callback("task_completed", {
                        "id": task.id,
                        "result": final_response
                    })
                    
            except Exception as e:
                error_msg = f"Task execution failed: {str(e)}"
                task.status = "failed"
                task.result = error_msg
                state.errors.append(error_msg)
                logger.error(error_msg)
                
                if self.callback:
                    self.callback("task_failed", {
                        "id": task.id,
                        "error": error_msg
                    })
            
            state.current_task_index += 1
            return state
        
        def wait_for_dependencies(state: OrchestratorState) -> OrchestratorState:
            """Wait for dependencies to complete"""
            # In a real implementation, this would check periodically
            # For now, just move to next task to avoid infinite loop
            state.current_task_index += 1
            return state
        
        # Build graph
        self.workflow = StateGraph(OrchestratorState)
        
        # Add nodes
        self.workflow.add_node("select", select_next_task)
        self.workflow.add_node("execute", execute_task)
        self.workflow.add_node("wait", wait_for_dependencies)
        
        # Set entry point
        self.workflow.set_entry_point("select")
        
        # Add edges
        self.workflow.add_conditional_edges(
            source="select",
            path=lambda s: select_next_task(s),
            path_map={  # Изменено с mapping на path_map для новой версии LangGraph
                "execute": "execute",
                "wait": "wait",
                "end": END
            }
        )
        
        self.workflow.add_edge("execute", "select")
        self.workflow.add_edge("wait", "select")
        
        # Compile
        self.app = self.workflow.compile()
    
    async def run_async(self, tasks: List[Task]) -> OrchestratorState:
        """Run orchestrator asynchronously with list of tasks"""
        self.state = OrchestratorState()
        self.state.tasks = tasks
        
        if self.callback:
            self.callback("orchestration_started", {
                "mode": self.mode.value,
                "task_count": len(tasks),
                "agents": list(self.agents.keys())
            })
        
        try:
            config = {"recursion_limit": 100}
            result = await self.app.ainvoke(self.state, config=config)
            
            self.state = result
            self.state.status = "completed"
            
            if self.callback:
                self.callback("orchestration_completed", {
                    "results": self.state.results,
                    "errors": self.state.errors
                })
                
        except Exception as e:
            self.state.status = "error"
            self.state.errors.append(f"Orchestration failed: {str(e)}")
            logger.error(f"Orchestration failed: {e}")
            
            if self.callback:
                self.callback("orchestration_error", {"error": str(e)})
        
        return self.state
    
    def run(self, tasks: List[Task]) -> OrchestratorState:
        """Run orchestrator synchronously"""
        return asyncio.run(self.run_async(tasks))
    
    def create_specialized_agents(self, llm_config: Dict[str, Any]):
        """Create a team of specialized agents"""
        
        roles = [
            {
                "name": "researcher",
                "role": "Research Specialist",
                "prompt": "You are a research specialist. Your job is to gather information, search the web, and analyze data. Always cite sources and provide evidence-based conclusions."
            },
            {
                "name": "coder",
                "role": "Software Developer",
                "prompt": "You are an expert software developer. Write clean, efficient, well-documented code. Follow best practices and explain your implementation decisions."
            },
            {
                "name": "writer",
                "role": "Content Writer",
                "prompt": "You are a professional content writer. Create clear, engaging, well-structured content. Adapt your tone to the audience and purpose."
            },
            {
                "name": "reviewer",
                "role": "Quality Reviewer",
                "prompt": "You are a quality reviewer. Critically analyze work for accuracy, completeness, and quality. Provide constructive feedback and identify improvements."
            },
            {
                "name": "planner",
                "role": "Task Planner",
                "prompt": "You are a strategic planner. Break down complex tasks into manageable steps. Identify dependencies and create efficient execution plans."
            }
        ]
        
        tools = get_all_tools()
        
        for role_config in roles:
            agent = DeepAgent(
                name=role_config["name"],
                role=role_config["role"],
                system_prompt=role_config["prompt"],
                tools=tools.copy(),
                callback=self.callback,
                **llm_config
            )
            self.add_agent(agent)
        
        return list(self.agents.keys())
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        return {
            "mode": self.mode.value,
            "status": self.state.status,
            "agent_count": len(self.agents),
            "agents": [agent.get_status() for agent in self.agents.values()],
            "total_tasks": len(self.state.tasks),
            "completed_tasks": sum(1 for t in self.state.tasks if t.status == "completed"),
            "failed_tasks": sum(1 for t in self.state.tasks if t.status == "failed"),
            "current_task_index": self.state.current_task_index,
            "errors": self.state.errors
        }
    
    def reset(self):
        """Reset orchestrator state"""
        self.state = OrchestratorState()
        for agent in self.agents.values():
            agent.reset()
        if self.callback:
            self.callback("orchestration_reset", {})

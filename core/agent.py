"""
Core Agent Module - Real LangChain/LangGraph Integration
Provides the base agent implementation with tool execution capabilities.
"""
import asyncio
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import logging

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.tools import BaseTool, Tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING_TOOL = "executing_tool"
    WAITING = "waiting"
    ERROR = "error"
    COMPLETED = "completed"


@dataclass
class AgentState:
    """State container for agent execution"""
    messages: List[BaseMessage] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    current_task: Optional[str] = None
    status: AgentStatus = AgentStatus.IDLE
    iterations: int = 0
    max_iterations: int = 15
    errors: List[str] = field(default_factory=list)
    
    def add_message(self, message: BaseMessage):
        self.messages.append(message)
        
    def add_error(self, error: str):
        self.errors.append(error)
        if len(self.errors) > 10:
            self.errors = self.errors[-10:]


class ToolResult(BaseModel):
    """Structured tool execution result"""
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DeepAgent:
    """
    Real LangChain/LangGraph powered agent with tool execution.
    Supports dynamic tool registration and stateful conversations.
    """
    
    def __init__(
        self,
        name: str,
        role: str,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        tools: Optional[List[BaseTool]] = None,
        callback: Optional[Callable[[str, Any], None]] = None
    ):
        self.name = name
        self.role = role
        self.model_name = model_name
        self.temperature = temperature
        self.callback = callback
        
        # Initialize LLM
        try:
            self.llm = ChatOpenAI(
                model=model_name,
                temperature=temperature,
                streaming=True
            )
        except Exception as e:
            logger.warning(f"Could not initialize OpenAI: {e}. Using mock mode.")
            self.llm = None
            
        # Initialize tools
        self.tools: Dict[str, BaseTool] = {}
        if tools:
            for tool in tools:
                self.register_tool(tool)
        
        # Default system prompt
        self.system_prompt = system_prompt or (
            f"You are {name}, a {role}. "
            f"You have access to various tools to help accomplish tasks. "
            f"Think step-by-step and use tools when needed. "
            f"Always provide clear, concise responses."
        )
        
        # State
        self.state = AgentState()
        self._build_graph()
    
    def register_tool(self, tool: BaseTool):
        """Register a tool with the agent"""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
        # Вызываем callback только для важных событий, не для регистрации
        # if self.callback:
        #     self.callback("tool_registered", {"name": tool.name, "agent": self.name})
    
    def unregister_tool(self, tool_name: str):
        """Unregister a tool"""
        if tool_name in self.tools:
            del self.tools[tool_name]
            logger.info(f"Unregistered tool: {tool_name}")
            if self.callback:
                self.callback("tool_unregistered", {"name": tool_name, "agent": self.name})
    
    def _build_graph(self):
        """Build LangGraph workflow"""
        
        def should_continue(state: AgentState) -> str:
            """Determine next step based on state"""
            if state.iterations >= state.max_iterations:
                return "end"
            if state.errors and len(state.errors) > 3:
                return "end"
            
            # Check if last message is from AI with tool calls
            if state.messages:
                last_msg = state.messages[-1]
                if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
                    return "tools"
            
            return "end"
        
        def call_model(state: AgentState) -> AgentState:
            """Call the LLM with current state"""
            if not self.llm:
                state.add_error("LLM not initialized")
                return state
            
            state.status = AgentStatus.THINKING
            if self.callback:
                self.callback("status_change", {"agent": self.name, "status": "thinking"})
            
            try:
                # Bind tools to LLM
                llm_with_tools = self.llm.bind_tools(list(self.tools.values()))
                
                # Prepare messages
                messages = [SystemMessage(content=self.system_prompt)] + state.messages
                
                # Invoke LLM
                response = llm_with_tools.invoke(messages)
                state.add_message(response)
                state.iterations += 1
                
                if self.callback:
                    self.callback("message", {"role": "assistant", "content": response.content})
                
            except Exception as e:
                error_msg = f"LLM error: {str(e)}"
                state.add_error(error_msg)
                state.status = AgentStatus.ERROR
                logger.error(error_msg)
                if self.callback:
                    self.callback("error", {"agent": self.name, "error": error_msg})
            
            return state
        
        def execute_tools(state: AgentState) -> AgentState:
            """Execute tools requested by the model"""
            if not state.messages:
                return state
            
            last_msg = state.messages[-1]
            if not isinstance(last_msg, AIMessage) or not last_msg.tool_calls:
                return state
            
            state.status = AgentStatus.EXECUTING_TOOL
            
            for tool_call in last_msg.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call.get("args", {})
                
                if self.callback:
                    self.callback("tool_call", {
                        "agent": self.name,
                        "tool": tool_name,
                        "args": tool_args
                    })
                
                try:
                    if tool_name in self.tools:
                        tool = self.tools[tool_name]
                        result = tool.invoke(tool_args)
                        
                        # Add tool result to state
                        tool_message = {
                            "type": "tool_result",
                            "name": tool_name,
                            "result": result,
                            "call_id": tool_call.get("id", "")
                        }
                        state.context[f"tool_result_{tool_call.get('id', '')}"] = result
                        
                        if self.callback:
                            self.callback("tool_result", {
                                "agent": self.name,
                                "tool": tool_name,
                                "result": result
                            })
                    else:
                        state.add_error(f"Tool not found: {tool_name}")
                        
                except Exception as e:
                    error_msg = f"Tool execution error ({tool_name}): {str(e)}"
                    state.add_error(error_msg)
                    logger.error(error_msg)
                    if self.callback:
                        self.callback("tool_error", {
                            "agent": self.name,
                            "tool": tool_name,
                            "error": str(e)
                        })
            
            return state
        
        # Build graph
        self.workflow = StateGraph(AgentState)
        
        # Add nodes
        self.workflow.add_node("model", call_model)
        self.workflow.add_node("tools", execute_tools)
        
        # Set entry point
        self.workflow.set_entry_point("model")
        
        # Add edges
        self.workflow.add_conditional_edges(
            source="model",
            path=should_continue,
            path_map={  # Изменено с mapping на path_map для новой версии LangGraph
                "tools": "tools",
                "end": END
            }
        )
        
        self.workflow.add_edge("tools", "model")
        
        # Compile
        self.app = self.workflow.compile()
    
    async def run_async(self, user_input: str) -> AgentState:
        """Run agent asynchronously with user input"""
        self.state = AgentState()
        self.state.current_task = user_input
        
        # Add user message
        self.state.add_message(HumanMessage(content=user_input))
        
        if self.callback:
            self.callback("message", {"role": "user", "content": user_input})
        
        try:
            # Execute graph
            config = {"recursion_limit": 50}
            result = await self.app.ainvoke(self.state, config=config)
            
            self.state = result
            self.state.status = AgentStatus.COMPLETED
            
            if self.callback:
                self.callback("status_change", {"agent": self.name, "status": "completed"})
                self.callback("task_complete", {"agent": self.name, "result": result})
                
        except Exception as e:
            self.state.status = AgentStatus.ERROR
            self.state.add_error(f"Execution error: {str(e)}")
            logger.error(f"Agent execution failed: {e}")
            if self.callback:
                self.callback("error", {"agent": self.name, "error": str(e)})
        
        return self.state
    
    def run(self, user_input: str) -> AgentState:
        """Run agent synchronously"""
        return asyncio.run(self.run_async(user_input))
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "name": self.name,
            "role": self.role,
            "status": self.state.status.value,
            "iterations": self.state.iterations,
            "max_iterations": self.state.max_iterations,
            "errors": self.state.errors,
            "tool_count": len(self.tools),
            "message_count": len(self.state.messages)
        }
    
    def reset(self):
        """Reset agent state"""
        self.state = AgentState()
        if self.callback:
            self.callback("status_change", {"agent": self.name, "status": "idle"})

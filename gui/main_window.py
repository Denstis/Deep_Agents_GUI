"""
Main Application Window - DeepAgents GUI
Real LangChain/LangGraph integration with multi-agent support.
"""
import customtkinter as ctk
from typing import Dict, List, Any, Optional
from datetime import datetime
import threading
import queue
import logging
import os

from core.agent import DeepAgent, AgentStatus
from core.tools import get_all_tools, get_tool_categories
from core.orchestrator import MultiAgentOrchestrator, OrchestratorMode, Task
from gui.tool_manager import ToolManager
from gui.agent_manager import AgentManager, AgentConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeepAgentsGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("DeepAgents GUI - LangChain Multi-Agent System")
        self.geometry("1400x900")
        self.minsize(1200, 800)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.event_queue = queue.Queue()
        self.is_processing = False
        self.current_agent = None
        
        self.tool_manager = ToolManager(callback=self._on_tool_event)
        self.agent_manager = AgentManager(
            tool_manager=self.tool_manager,
            llm_config={"model_name": os.getenv("DEFAULT_MODEL", "gpt-4o-mini")},
            callback=self._on_agent_event
        )
        
        self._create_layout()
        self._create_menu()
        self._create_chat_panel()
        self._create_tools_panel()
        self._create_status_bar()
        self.after(100, self._process_events)
        self.after(500, self._create_default_agent)  # Отложенный вызов после отображения окна
        logger.info("DeepAgents GUI initialized")

    def _create_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)
        self.left_frame = left_frame
        right_frame = ctk.CTkFrame(main_frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame = right_frame

    def _create_menu(self):
        menubar = ctk.CTkFrame(self, height=40)
        menubar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=(5, 0))
        menubar.grid_propagate(False)
        title_label = ctk.CTkLabel(menubar, text="DeepAgents GUI", font=ctk.CTkFont(size=16, weight="bold"))
        title_label.pack(side="left", padx=10, pady=10)
        btn_frame = ctk.CTkFrame(menubar, fg_color="transparent")
        btn_frame.pack(side="right", padx=10, pady=5)
        self.reset_btn = ctk.CTkButton(btn_frame, text="Reset", width=80, command=self._reset_all)
        self.reset_btn.pack(side="left", padx=5)
        self.settings_btn = ctk.CTkButton(btn_frame, text="Settings", width=80, command=self._show_settings)
        self.settings_btn.pack(side="left", padx=5)
        self.help_btn = ctk.CTkButton(btn_frame, text="Help", width=80, command=self._show_help)
        self.help_btn.pack(side="left", padx=5)

    def _create_chat_panel(self):
        chat_container = ctk.CTkFrame(self.left_frame)
        chat_container.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        chat_container.grid_rowconfigure(0, weight=1)
        chat_container.grid_columnconfigure(0, weight=1)
        header = ctk.CTkFrame(chat_container)
        header.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 0))
        self.agent_selector = ctk.CTkComboBox(header, values=["Select Agent"], command=self._on_agent_selected, width=200)
        self.agent_selector.grid(row=0, column=0, padx=10, pady=10)
        self.status_indicator = ctk.CTkLabel(header, text="Idle", text_color="gray")
        self.status_indicator.grid(row=0, column=1, padx=10, pady=10)
        self.chat_display = ctk.CTkTextbox(chat_container, state="disabled", font=ctk.CTkFont(family="Consolas", size=12))
        self.chat_display.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        input_frame = ctk.CTkFrame(chat_container)
        input_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        input_frame.grid_columnconfigure(0, weight=1)
        self.chat_input = ctk.CTkEntry(input_frame, placeholder_text="Type your message...", font=ctk.CTkFont(size=13))
        self.chat_input.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.chat_input.bind("<Return>", lambda e: self._send_message())
        self.send_btn = ctk.CTkButton(input_frame, text="Send", width=100, command=self._send_message)
        self.send_btn.grid(row=0, column=1)
        self.stop_btn = ctk.CTkButton(input_frame, text="Stop", width=100, fg_color="red", hover_color="darkred", command=self._stop_execution)

    def _create_tools_panel(self):
        tools_container = ctk.CTkScrollableFrame(self.right_frame)
        tools_container.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        tools_container.grid_columnconfigure(0, weight=1)
        header = ctk.CTkLabel(tools_container, text="Tools", font=ctk.CTkFont(size=14, weight="bold"))
        header.grid(row=0, column=0, sticky="ew", padx=5, pady=10)
        tools_by_category = self.tool_manager.get_tools_by_category()
        row = 1
        self.tool_checkboxes = {}
        for category, tools in tools_by_category.items():
            cat_label = ctk.CTkLabel(tools_container, text=f"{category.upper()}", font=ctk.CTkFont(weight="bold"), anchor="w")
            cat_label.grid(row=row, column=0, sticky="ew", padx=5, pady=(10, 5))
            row += 1
            for tool in tools:
                frame = ctk.CTkFrame(tools_container)
                frame.grid(row=row, column=0, sticky="ew", padx=5, pady=2)
                frame.grid_columnconfigure(0, weight=1)
                risk_colors = {"safe": "green", "review": "orange", "dangerous": "red"}
                risk_dot = ctk.CTkLabel(frame, text="*", text_color=risk_colors.get(tool["risk_level"], "gray"), width=20)
                risk_dot.grid(row=0, column=0, padx=5)
                info_frame = ctk.CTkFrame(frame, fg_color="transparent")
                info_frame.grid(row=0, column=1, sticky="ew")
                info_frame.grid_columnconfigure(0, weight=1)
                name_label = ctk.CTkLabel(info_frame, text=tool["name"], font=ctk.CTkFont(weight="bold"), anchor="w")
                name_label.grid(row=0, column=0, sticky="w")
                desc_label = ctk.CTkLabel(info_frame, text=tool["description"][:50] + "...", font=ctk.CTkFont(size=10), text_color="gray", anchor="w")
                desc_label.grid(row=1, column=0, sticky="w")
                switch = ctk.CTkSwitch(frame, text="", width=40, command=lambda t=tool["name"]: self._toggle_tool(t))
                switch.select()
                switch.grid(row=0, column=2, padx=10)
                self.tool_checkboxes[tool["name"]] = switch
                row += 1
        self.tools_frame = tools_container

    def _create_status_bar(self):
        status_bar = ctk.CTkFrame(self, height=30)
        status_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 5))
        status_bar.grid_propagate(False)
        self.status_label = ctk.CTkLabel(status_bar, text="Ready", font=ctk.CTkFont(size=11))
        self.status_label.pack(side="left", padx=10)
        stats_frame = ctk.CTkFrame(status_bar, fg_color="transparent")
        stats_frame.pack(side="right", padx=10)
        self.tools_stat = ctk.CTkLabel(stats_frame, text="Tools: 0", font=ctk.CTkFont(size=11), text_color="gray")
        self.tools_stat.pack(side="left", padx=10)
        self.agents_stat = ctk.CTkLabel(stats_frame, text="Agents: 0", font=ctk.CTkFont(size=11), text_color="gray")
        self.agents_stat.pack(side="left", padx=10)
        self._update_stats()

    def _create_default_agent(self):
        """Create default assistant agent after GUI is displayed"""
        try:
            config = AgentConfig(
                name="assistant", 
                role="General Assistant", 
                system_prompt="You are a helpful AI assistant with access to various tools.", 
                model=os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
            )
            if self.agent_manager.create_agent(config):
                self._update_agent_selector()
                self.agent_selector.set("assistant")
                self.current_agent = "assistant"
                self._add_chat_message("system", "Assistant agent ready. How can I help you today?")
        except Exception as e:
            logger.error(f"Failed to create default agent: {e}")
            self._add_chat_message("system", f"Error creating agent: {e}")

    def _update_agent_selector(self):
        agents = self.agent_manager.list_agents()
        agent_names = [a["name"] for a in agents]
        self.agent_selector.configure(values=agent_names)
        if not self.current_agent and agent_names:
            self.current_agent = agent_names[0]
            self.agent_selector.set(agent_names[0])

    def _on_agent_selected(self, selection):
        self.current_agent = selection
        self._add_chat_message("system", f"Switched to agent: {selection}")
        self._update_status_indicator()

    def _send_message(self):
        if self.is_processing:
            return
        message = self.chat_input.get().strip()
        if not message:
            return
        if not self.current_agent:
            self._add_chat_message("system", "Please select an agent first.")
            return
        self._add_chat_message("user", message)
        self.chat_input.delete(0, "end")
        self.is_processing = True
        self._update_status_indicator()
        self.send_btn.grid_forget()
        self.stop_btn.grid(row=0, column=1)
        def execute_task():
            try:
                result = self.agent_manager.execute_task(self.current_agent, message)
                self.event_queue.put(("task_result", result))
            except Exception as e:
                self.event_queue.put(("task_error", str(e)))
            finally:
                self.event_queue.put(("task_complete", None))
        threading.Thread(target=execute_task, daemon=True).start()

    def _stop_execution(self):
        self.is_processing = False
        self._add_chat_message("system", "Execution stopped by user.")
        self._reset_ui_state()

    def _reset_ui_state(self):
        self.is_processing = False
        self._update_status_indicator()
        self.stop_btn.grid_forget()
        self.send_btn.grid(row=0, column=1)

    def _add_chat_message(self, role: str, content: str):
        self.chat_display.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        tags = {"user": "#4CAF50", "assistant": "#2196F3", "system": "#FF9800", "tool": "#9C27B0"}
        self.chat_display.insert("end", f"\n[{timestamp}] {role.title()}: {content}\n", role)
        self.chat_display.tag_config(role, foreground=tags.get(role, "white"))
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")

    def _update_status_indicator(self):
        if self.is_processing:
            self.status_indicator.configure(text="Working", text_color="#FF9800")
            self.status_label.configure(text="Processing...")
        else:
            self.status_indicator.configure(text="Idle", text_color="#4CAF50")
            self.status_label.configure(text="Ready")

    def _update_stats(self):
        tool_stats = self.tool_manager.get_statistics()
        agent_stats = self.agent_manager.get_statistics()
        self.tools_stat.configure(text=f"Tools: {tool_stats['enabled']}/{tool_stats['total_tools']}")
        self.agents_stat.configure(text=f"Agents: {agent_stats['total_agents']}")

    def _toggle_tool(self, tool_name: str):
        enabled = self.tool_manager.toggle_tool(tool_name)
        self.agent_manager.update_all_agents_tools()
        logger.info(f"Tool {tool_name} {'enabled' if enabled else 'disabled'}")
        self._update_stats()

    def _reset_all(self):
        self.agent_manager.reset_all()
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.configure(state="disabled")
        self._add_chat_message("system", "All agents reset. Ready for new tasks.")
        self._update_status_indicator()
        self._update_stats()

    def _show_settings(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Settings")
        dialog.geometry("500x400")
        dialog.transient(self)
        frame = ctk.CTkFrame(dialog)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(frame, text="Settings", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        ctk.CTkLabel(frame, text="Model:").pack(anchor="w", pady=5)
        model_combo = ctk.CTkComboBox(frame, values=["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"])
        model_combo.set(os.getenv("DEFAULT_MODEL", "gpt-4o-mini"))
        model_combo.pack(fill="x", pady=5)
        ctk.CTkLabel(frame, text="Temperature: 0.7").pack(anchor="w", pady=(20, 5))
        temp_slider = ctk.CTkSlider(frame, from_=0, to=1, number_of_steps=10)
        temp_slider.set(0.7)
        temp_slider.pack(fill="x", pady=5)
        ctk.CTkButton(frame, text="Save", command=dialog.destroy).pack(pady=20)

    def _show_help(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Help")
        dialog.geometry("600x500")
        dialog.transient(self)
        text = ctk.CTkTextbox(dialog)
        text.pack(fill="both", expand=True, padx=20, pady=20)
        help_content = """DeepAgents GUI - Help

GETTING STARTED:
1. Select an agent from the dropdown
2. Type your message in the input field
3. Press Enter or click Send

AVAILABLE AGENTS:
- Assistant - General purpose helper
- Researcher - Web search and analysis  
- Coder - Software development
- Writer - Content creation
- Reviewer - Quality assurance
- Planner - Task decomposition

TOOLS:
Enable/disable tools in the right panel:
- Filesystem - Read/write files
- Console - Execute commands
- Web - Search and fetch
- Code - Python execution
- Math - Calculations
- Utility - Time and system info

REQUIREMENTS:
- OpenAI API key (set in .env file)
- Python 3.9+
"""
        text.insert("1.0", help_content)
        text.configure(state="disabled")

    def _process_events(self):
        try:
            while True:
                event_type, data = self.event_queue.get_nowait()
                if event_type == "task_result":
                    if data.get("success"):
                        response = data.get("response", "No response")
                        self._add_chat_message("assistant", response)
                    else:
                        self._add_chat_message("system", f"Error: {data.get('error', 'Unknown')}")
                elif event_type == "task_error":
                    self._add_chat_message("system", f"Error: {data}")
                elif event_type == "task_complete":
                    self._reset_ui_state()
                    self._update_stats()
                elif event_type == "agent_event":
                    event_data = data.get("event", "")
                    if event_data == "tool_call":
                        tool_name = data.get("data", {}).get("name", "unknown")
                        self._add_chat_message("tool", f"Using {tool_name}...")
        except queue.Empty:
            pass
        self.after(100, self._process_events)

    def _on_tool_event(self, event_type: str, data: Dict):
        self.event_queue.put(("tool_event", {"type": event_type, "data": data}))

    def _on_agent_event(self, event_type: str, data: Dict):
        self.event_queue.put(("agent_event", {"type": event_type, "data": data}))

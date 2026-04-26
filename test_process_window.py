#!/usr/bin/env python3
"""Тестовый скрипт для демонстрации ProcessWindow."""

import customtkinter as ctk
from core.gui import ProcessWindow, ToolExecutionPanel

class TestApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Test Process Window")
        self.geometry("1000x700")
        
        # Main layout
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Chat area (placeholder)
        chat_frame = ctk.CTkFrame(self, fg_color="#1e1e1e")
        chat_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        
        ctk.CTkLabel(
            chat_frame,
            text="Chat Area\n(Placeholder)",
            font=ctk.CTkFont(size=20),
            text_color="#7f8c8d"
        ).place(relx=0.5, rely=0.5, anchor="center")
        
        # Process panel
        process_container = ctk.CTkFrame(self, fg_color="#1e1e1e")
        process_container.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        process_container.grid_columnconfigure(0, weight=1)
        process_container.grid_rowconfigure(0, weight=1)
        process_container.grid_rowconfigure(1, weight=0)
        
        # Process window
        self.process_window = ProcessWindow(
            process_container,
            max_events=500,
            fg_color="transparent"
        )
        self.process_window.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Tool execution panel
        self.tool_panel = ToolExecutionPanel(process_container, fg_color="#2a2a2a")
        self.tool_panel.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
        
        # Demo buttons
        btn_frame = ctk.CTkFrame(self, fg_color="#2b2b2b", height=100)
        btn_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        
        ctk.CTkButton(
            btn_frame,
            text="Add Action",
            command=self.demo_action
        ).pack(side="left", padx=5, pady=10)
        
        ctk.CTkButton(
            btn_frame,
            text="Add Tool Use",
            command=self.demo_tool
        ).pack(side="left", padx=5, pady=10)
        
        ctk.CTkButton(
            btn_frame,
            text="Add Message",
            command=self.demo_message
        ).pack(side="left", padx=5, pady=10)
        
        ctk.CTkButton(
            btn_frame,
            text="Add Error",
            command=self.demo_error,
            fg_color="#e74c3c"
        ).pack(side="left", padx=5, pady=10)
        
        ctk.CTkButton(
            btn_frame,
            text="Clear",
            command=self.clear_logs,
            fg_color="#555555"
        ).pack(side="left", padx=5, pady=10)
    
    def demo_action(self):
        self.process_window.add_action(
            "Анализ запроса пользователя",
            details="Обработка естественного языка..."
        )
    
    def demo_tool(self):
        self.process_window.add_tool_use(
            tool_name="read_file",
            tool_input={"path": "/home/user/document.txt"},
            tool_output="File content: Hello World!"
        )
        self.tool_panel.start_tool("read_file", {"path": "/home/user/document.txt"})
        self.after(2000, lambda: self.tool_panel.stop_tool())
    
    def demo_message(self):
        self.process_window.add_message("Запрос обработан успешно")
    
    def demo_error(self):
        self.process_window.add_error(
            "Ошибка подключения к API",
            details="Timeout after 30 seconds"
        )
    
    def clear_logs(self):
        self.process_window.clear()

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = TestApp()
    app.mainloop()

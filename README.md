# DeepAgents GUI

Multi-agent system with real LangChain/LangGraph integration and modern GUI.

## Features

- **Real LangChain Integration**: Full implementation using LangChain and LangGraph
- **Multi-Agent Support**: Create and manage multiple specialized agents
- **10+ Real Tools**: File operations, web search, code execution, math, and more
- **Modern GUI**: Built with CustomTkinter for a clean, dark-themed interface
- **Tool Management**: Enable/disable tools by category and risk level
- **Agent Orchestration**: Coordinate multiple agents on complex tasks

## Installation

### Prerequisites
- Python 3.9 or higher
- OpenAI API key (or compatible API)

### Setup

1. Clone or download the repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure API key:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

## Usage

### Windows
Double-click `run.bat` or run:
```cmd
python app.py
```

### Linux/Mac
```bash
python app.py
```

## Architecture

```
/workspace/
├── app.py                 # Main entry point
├── run.bat                # Windows launcher
├── requirements.txt       # Dependencies
├── .env.example          # Environment template
│
├── core/                  # Core engine
│   ├── __init__.py
│   ├── agent.py          # DeepAgent with LangGraph
│   ├── tools.py          # Real tool implementations
│   └── orchestrator.py   # Multi-agent coordination
│
└── gui/                   # GUI components
    ├── __init__.py
    ├── main_window.py    # Main application window
    ├── tool_manager.py   # Tool management
    └── agent_manager.py  # Agent management
```

## Available Tools

| Category | Tools |
|----------|-------|
| Filesystem | file_read, file_write, file_list |
| Console | console_execute |
| Web | web_search, web_fetch |
| Code | python_execute |
| Math | math_evaluate |
| Utility | get_current_time, get_system_info |

## Agent Roles

Default specialized agents:
- **Assistant** - General purpose helper
- **Researcher** - Web search and data analysis
- **Coder** - Software development
- **Writer** - Content creation
- **Reviewer** - Quality assurance
- **Planner** - Task decomposition

## Configuration

Edit `.env` file:

```env
OPENAI_API_KEY=sk-your-key-here
DEFAULT_MODEL=gpt-4o-mini
TEMPERATURE=0.7
MAX_ITERATIONS=15
```

## License

MIT License

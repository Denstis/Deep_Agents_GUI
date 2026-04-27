#!/usr/bin/env python3
"""
DeepAgents GUI - Модульная архитектура
Главный файл запуска
"""

import sys
from pathlib import Path

# Добавляем корень проекта в путь
sys.path.insert(0, str(Path(__file__).parent))

from gui.main_window import DeepAgentsMainWindow

if __name__ == "__main__":
    app = DeepAgentsMainWindow()
    app.mainloop()

"""
Модуль графического интерфейса для чата с локальной языковой моделью.
Реализует требования к отображению сообщений, стримингу и управлению состоянием.
"""

__all__ = [
    'ChatWindow',
    'MessageBubble',
]

from .chat_window import ChatWindow
from .message_bubble import MessageBubble

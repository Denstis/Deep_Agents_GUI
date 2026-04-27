"""
Менеджер инструментов - управление доступными инструментами агента
"""

import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ToolRiskLevel(Enum):
    """Уровни риска для инструментов."""
    SAFE = "safe"
    REVIEW = "review"
    DANGEROUS = "dangerous"


@dataclass
class ToolInfo:
    """Информация об инструменте."""
    name: str
    description: str
    risk_level: ToolRiskLevel
    enabled: bool = True
    category: str = "general"
    icon: str = "🔧"
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolManager:
    """
    Менеджер инструментов для DeepAgents.
    
    Функционал:
    - Регистрация и удаление инструментов
    - Включение/выключение инструментов
    - Категоризация инструментов
    - Проверка прав доступа
    - Получение активных инструментов
    """
    
    def __init__(self):
        self._tools: Dict[str, ToolInfo] = {}
        self._tool_instances: Dict[str, Any] = {}
        self._callbacks: List[Callable] = []
        
        # Регистрируем стандартные инструменты
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Регистрация инструментов по умолчанию."""
        
        # Файловая система
        self.register_tool(ToolInfo(
            name="read_file",
            description="Чтение содержимого файла",
            risk_level=ToolRiskLevel.SAFE,
            category="filesystem",
            icon="📄"
        ))
        
        self.register_tool(ToolInfo(
            name="write_file",
            description="Запись содержимого в файл",
            risk_level=ToolRiskLevel.REVIEW,
            category="filesystem",
            icon="✍️"
        ))
        
        self.register_tool(ToolInfo(
            name="list_directory",
            description="Список файлов в директории",
            risk_level=ToolRiskLevel.SAFE,
            category="filesystem",
            icon="📁"
        ))
        
        # Командная строка
        self.register_tool(ToolInfo(
            name="execute_command",
            description="Выполнение системной команды",
            risk_level=ToolRiskLevel.REVIEW,
            category="console",
            icon="💻"
        ))
        
        # Веб-поиск
        self.register_tool(ToolInfo(
            name="web_search",
            description="Поиск информации в интернете",
            risk_level=ToolRiskLevel.SAFE,
            category="web",
            icon="🌐"
        ))
        
        # Математика
        self.register_tool(ToolInfo(
            name="calculate",
            description="Математические вычисления",
            risk_level=ToolRiskLevel.SAFE,
            category="math",
            icon="🧮"
        ))
        
        # Python инструменты
        self.register_tool(ToolInfo(
            name="python_exec",
            description="Выполнение Python кода",
            risk_level=ToolRiskLevel.REVIEW,
            category="python",
            icon="🐍"
        ))
        
        self.register_tool(ToolInfo(
            name="pip_install",
            description="Установка Python пакетов",
            risk_level=ToolRiskLevel.REVIEW,
            category="python",
            icon="📦"
        ))
        
        # Изображения
        self.register_tool(ToolInfo(
            name="image_info",
            description="Получение информации об изображении",
            risk_level=ToolRiskLevel.SAFE,
            category="media",
            icon="🖼️"
        ))
    
    def register_tool(self, tool_info: ToolInfo, instance: Optional[Any] = None):
        """
        Регистрация инструмента.
        
        Args:
            tool_info: Информация об инструменте
            instance: Экземпляр инструмента (опционально)
        """
        if tool_info.name in self._tools:
            logger.warning(f"Инструмент '{tool_info.name}' уже зарегистрирован")
            return False
        
        self._tools[tool_info.name] = tool_info
        if instance is not None:
            self._tool_instances[tool_info.name] = instance
        
        self._notify_change()
        logger.info(f"Зарегистрирован инструмент: {tool_info.name}")
        return True
    
    def unregister_tool(self, name: str):
        """Удаление инструмента."""
        if name not in self._tools:
            logger.warning(f"Инструмент '{name}' не найден")
            return False
        
        del self._tools[name]
        if name in self._tool_instances:
            del self._tool_instances[name]
        
        self._notify_change()
        logger.info(f"Удален инструмент: {name}")
        return True
    
    def enable_tool(self, name: str) -> bool:
        """Включение инструмента."""
        if name not in self._tools:
            logger.error(f"Инструмент '{name}' не найден")
            return False
        
        self._tools[name].enabled = True
        self._notify_change()
        return True
    
    def disable_tool(self, name: str) -> bool:
        """Выключение инструмента."""
        if name not in self._tools:
            logger.error(f"Инструмент '{name}' не найден")
            return False
        
        self._tools[name].enabled = False
        self._notify_change()
        return True
    
    def toggle_tool(self, name: str) -> bool:
        """Переключение состояния инструмента."""
        if name not in self._tools:
            return False
        
        tool = self._tools[name]
        tool.enabled = not tool.enabled
        self._notify_change()
        return tool.enabled
    
    def is_enabled(self, name: str) -> bool:
        """Проверка включен ли инструмент."""
        if name not in self._tools:
            return False
        return self._tools[name].enabled
    
    def get_tool(self, name: str) -> Optional[ToolInfo]:
        """Получение информации об инструменте."""
        return self._tools.get(name)
    
    def get_tool_instance(self, name: str) -> Optional[Any]:
        """Получение экземпляра инструмента."""
        return self._tool_instances.get(name)
    
    def set_tool_instance(self, name: str, instance: Any):
        """Установка экземпляра инструмента."""
        if name in self._tools:
            self._tool_instances[name] = instance
    
    def get_enabled_tools(self) -> List[ToolInfo]:
        """Получение списка включенных инструментов."""
        return [t for t in self._tools.values() if t.enabled]
    
    def get_all_tools(self) -> List[ToolInfo]:
        """Получение списка всех инструментов."""
        return list(self._tools.values())
    
    def get_tools_by_category(self, category: str) -> List[ToolInfo]:
        """Получение инструментов по категории."""
        return [t for t in self._tools.values() if t.category == category]
    
    def get_categories(self) -> List[str]:
        """Получение списка категорий."""
        return list(set(t.category for t in self._tools.values()))
    
    def get_tools_by_risk(self, risk_level: ToolRiskLevel) -> List[ToolInfo]:
        """Получение инструментов по уровню риска."""
        return [t for t in self._tools.values() if t.risk_level == risk_level]
    
    def add_callback(self, callback: Callable):
        """Добавление колбэка на изменение списка инструментов."""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable):
        """Удаление колбэка."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def _notify_change(self):
        """Уведомление об изменении списка инструментов."""
        for callback in self._callbacks:
            try:
                callback(self.get_enabled_tools())
            except Exception as e:
                logger.error(f"Ошибка при вызове колбэка: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь."""
        return {
            name: {
                "description": info.description,
                "risk_level": info.risk_level.value,
                "enabled": info.enabled,
                "category": info.category,
                "icon": info.icon,
            }
            for name, info in self._tools.items()
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Десериализация из словаря."""
        for name, info_data in data.items():
            if name in self._tools:
                tool = self._tools[name]
                tool.enabled = info_data.get("enabled", True)
                tool.description = info_data.get("description", tool.description)
                tool.category = info_data.get("category", tool.category)
                tool.icon = info_data.get("icon", tool.icon)

"""
Менеджер агентов - управление суб-агентами и их состоянием
"""

import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Статусы агента."""
    IDLE = "idle"
    WORKING = "working"
    WAITING = "waiting"
    ERROR = "error"
    STOPPED = "stopped"


class AgentRole(Enum):
    """Роли агентов."""
    MAIN = "main"
    RESEARCHER = "researcher"
    CODER = "coder"
    WRITER = "writer"
    REVIEWER = "reviewer"
    CUSTOM = "custom"


@dataclass
class AgentInfo:
    """Информация об агенте."""
    id: str
    name: str
    role: AgentRole
    status: AgentStatus = AgentStatus.IDLE
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    tasks_completed: int = 0
    tasks_failed: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        """Процент успешных задач."""
        total = self.tasks_completed + self.tasks_failed
        if total == 0:
            return 100.0
        return (self.tasks_completed / total) * 100
    
    @property
    def uptime(self) -> str:
        """Время работы в читаемом формате."""
        delta = datetime.now() - self.created_at
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        return f"{hours}ч {minutes}м"


@dataclass
class AgentTask:
    """Задача агента."""
    id: str
    agent_id: str
    description: str
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AgentManager:
    """
    Менеджер агентов для DeepAgents.
    
    Функционал:
    - Создание и удаление агентов
    - Управление статусами агентов
    - Отслеживание задач
    - История активности
    - Статистика производительности
    """
    
    def __init__(self):
        self._agents: Dict[str, AgentInfo] = {}
        self._tasks: Dict[str, AgentTask] = {}
        self._callbacks: List[Callable] = []
        self._max_agents = 10
        
        # Создаем главного агента по умолчанию
        self._create_main_agent()
    
    def _create_main_agent(self):
        """Создание главного агента."""
        main_agent = AgentInfo(
            id="main-agent",
            name="Главный агент",
            role=AgentRole.MAIN,
            description="Основной агент для обработки запросов пользователя"
        )
        self._agents[main_agent.id] = main_agent
        logger.info("Создан главный агент")
    
    def create_agent(
        self,
        name: str,
        role: AgentRole = AgentRole.CUSTOM,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[AgentInfo]:
        """
        Создание нового агента.
        
        Args:
            name: Имя агента
            role: Роль агента
            description: Описание
            metadata: Дополнительные метаданные
            
        Returns:
            AgentInfo или None если не удалось создать
        """
        if len(self._agents) >= self._max_agents:
            logger.error(f"Достигнут лимит агентов ({self._max_agents})")
            return None
        
        agent_id = f"agent-{uuid.uuid4().hex[:8]}"
        agent = AgentInfo(
            id=agent_id,
            name=name,
            role=role,
            description=description,
            metadata=metadata or {}
        )
        
        self._agents[agent_id] = agent
        self._notify_change()
        logger.info(f"Создан агент: {name} ({agent_id})")
        return agent
    
    def remove_agent(self, agent_id: str) -> bool:
        """Удаление агента."""
        if agent_id not in self._agents:
            logger.error(f"Агент '{agent_id}' не найден")
            return False
        
        if agent_id == "main-agent":
            logger.error("Нельзя удалить главного агента")
            return False
        
        agent = self._agents[agent_id]
        if agent.status == AgentStatus.WORKING:
            logger.error(f"Нельзя удалить работающего агента '{agent.name}'")
            return False
        
        del self._agents[agent_id]
        self._notify_change()
        logger.info(f"Удален агент: {agent.name}")
        return True
    
    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """Получение информации об агенте."""
        return self._agents.get(agent_id)
    
    def get_all_agents(self) -> List[AgentInfo]:
        """Получение списка всех агентов."""
        return list(self._agents.values())
    
    def get_active_agents(self) -> List[AgentInfo]:
        """Получение списка активных агентов."""
        return [
            a for a in self._agents.values()
            if a.status in (AgentStatus.WORKING, AgentStatus.WAITING)
        ]
    
    def get_idle_agents(self) -> List[AgentInfo]:
        """Получение списка свободных агентов."""
        return [a for a in self._agents.values() if a.status == AgentStatus.IDLE]
    
    def update_agent_status(self, agent_id: str, status: AgentStatus) -> bool:
        """Обновление статуса агента."""
        if agent_id not in self._agents:
            return False
        
        agent = self._agents[agent_id]
        old_status = agent.status
        agent.status = status
        agent.last_active = datetime.now()
        
        logger.info(f"Агент '{agent.name}': {old_status.value} -> {status.value}")
        self._notify_change()
        return True
    
    def assign_task(
        self,
        agent_id: str,
        description: str,
        task_id: Optional[str] = None
    ) -> Optional[AgentTask]:
        """
        Назначение задачи агенту.
        
        Args:
            agent_id: ID агента
            description: Описание задачи
            task_id: ID задачи (генерируется если не указан)
            
        Returns:
            AgentTask или None
        """
        if agent_id not in self._agents:
            logger.error(f"Агент '{agent_id}' не найден")
            return None
        
        agent = self._agents[agent_id]
        if agent.status != AgentStatus.IDLE:
            logger.error(f"Агент '{agent.name}' занят (статус: {agent.status.value})")
            return None
        
        if task_id is None:
            task_id = f"task-{uuid.uuid4().hex[:8]}"
        
        task = AgentTask(
            id=task_id,
            agent_id=agent_id,
            description=description,
            status="running"
        )
        task.started_at = datetime.now()
        
        self._tasks[task_id] = task
        self.update_agent_status(agent_id, AgentStatus.WORKING)
        
        logger.info(f"Задача '{task_id}' назначена агенту '{agent.name}'")
        return task
    
    def complete_task(
        self,
        task_id: str,
        result: Optional[str] = None,
        success: bool = True
    ) -> bool:
        """Завершение задачи."""
        if task_id not in self._tasks:
            logger.error(f"Задача '{task_id}' не найдена")
            return False
        
        task = self._tasks[task_id]
        task.status = "completed" if success else "failed"
        task.result = result
        task.completed_at = datetime.now()
        
        # Обновляем статистику агента
        if task.agent_id in self._agents:
            agent = self._agents[task.agent_id]
            if success:
                agent.tasks_completed += 1
            else:
                agent.tasks_failed += 1
            self.update_agent_status(task.agent_id, AgentStatus.IDLE)
        
        logger.info(f"Задача '{task_id}' завершена: {'успешно' if success else 'ошибка'}")
        self._notify_change()
        return True
    
    def get_agent_tasks(self, agent_id: str) -> List[AgentTask]:
        """Получение задач агента."""
        return [t for t in self._tasks.values() if t.agent_id == agent_id]
    
    def get_task(self, task_id: str) -> Optional[AgentTask]:
        """Получение информации о задаче."""
        return self._tasks.get(task_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики по всем агентам."""
        total_tasks = len(self._tasks)
        completed_tasks = sum(1 for t in self._tasks.values() if t.status == "completed")
        failed_tasks = sum(1 for t in self._tasks.values() if t.status == "failed")
        
        return {
            "total_agents": len(self._agents),
            "active_agents": len(self.get_active_agents()),
            "idle_agents": len(self.get_idle_agents()),
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 100.0,
        }
    
    def add_callback(self, callback: Callable):
        """Добавление колбэка на изменения."""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable):
        """Удаление колбэка."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def _notify_change(self):
        """Уведомление об изменениях."""
        for callback in self._callbacks:
            try:
                callback(self.get_all_agents())
            except Exception as e:
                logger.error(f"Ошибка при вызове колбэка: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь."""
        return {
            "agents": [
                {
                    "id": a.id,
                    "name": a.name,
                    "role": a.role.value,
                    "status": a.status.value,
                    "description": a.description,
                    "tasks_completed": a.tasks_completed,
                    "tasks_failed": a.tasks_failed,
                    "success_rate": a.success_rate,
                    "uptime": a.uptime,
                }
                for a in self._agents.values()
            ],
            "statistics": self.get_statistics(),
        }

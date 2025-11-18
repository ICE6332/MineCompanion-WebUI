"""监控事件总线实现。"""

from typing import Dict, List, Callable, Any, Optional
from collections import deque
from datetime import datetime, timezone
from core.monitor.event_types import MonitorEventType
import uuid


class EventBus:
    """负责事件分发与记录的单例事件总线。"""

    _instance: Optional["EventBus"] = None
    _subscribers: Dict[MonitorEventType, List[Callable[[Dict[str, Any]], None]]] = {}
    _event_history: deque = deque(maxlen=100)

    def __new__(cls) -> "EventBus":
        """确保只能创建一个事件总线实例。"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._subscribers = {}
            cls._event_history = deque(maxlen=100)
        return cls._instance

    @classmethod
    def publish(
        cls,
        event_type: MonitorEventType,
        data: Dict[str, Any],
        severity: str = "info",
    ) -> None:
        """发布事件并通知订阅者。"""
        if cls._instance is None:
            cls()

        event = {
            "id": str(uuid.uuid4()),
            "type": event_type.value,
            # 使用带时区的 UTC 时间，避免 Python 3.14+ 弃用 utcnow
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
            "severity": severity,
        }

        cls._event_history.append(event)

        for callback in cls._subscribers.get(event_type, []):
            callback(event)

    @classmethod
    def subscribe(cls, event_type: MonitorEventType, callback: Callable[[Dict[str, Any]], None]) -> None:
        """订阅指定类型事件。"""
        if cls._instance is None:
            cls()

        cls._subscribers.setdefault(event_type, []).append(callback)

    @classmethod
    def get_recent_events(cls, limit: int = 100) -> List[Dict[str, Any]]:
        """返回最近的事件记录。"""
        if cls._instance is None:
            cls()

        if limit <= 0:
            return []
        events = list(cls._event_history)
        return events[-limit:]

    @classmethod
    def clear_history(cls) -> None:
        """清空事件历史。"""
        if cls._instance is None:
            cls()

        cls._event_history.clear()

"""WebSocket 连接管理器的最小实现。

首期用于替换散落的全局字典，后续可接入 Redis 等共享存储。
"""

from __future__ import annotations

from typing import Dict, Any
from fastapi import WebSocket

from core.interfaces import ConnectionManagerInterface


class ConnectionManager(ConnectionManagerInterface):
    """在内存中管理活跃 WebSocket 连接。"""

    def __init__(self) -> None:
        self._connections: Dict[str, WebSocket] = {}

    def add(self, client_id: str, websocket: WebSocket) -> None:
        self._connections[client_id] = websocket

    def remove(self, client_id: str) -> None:
        self._connections.pop(client_id, None)

    def get(self, client_id: str) -> WebSocket | None:
        return self._connections.get(client_id)

    def get_all_ids(self) -> list[str]:
        return list(self._connections.keys())

    def count(self) -> int:
        return len(self._connections)

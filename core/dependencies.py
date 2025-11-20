"""FastAPI 依赖注入工厂。

当前仍返回现有实现，后续移除单例/全局状态时可无感替换。
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from core.interfaces import (
    EventBusInterface,
    MetricsInterface,
    LLMServiceInterface,
    ConnectionManagerInterface,
)
from core.monitor.event_bus import EventBus
from core.monitor.metrics_collector import MetricsCollector
from core.llm.service import LLMService


# 下面的缓存实例将逐步替换为真正的实例生命周期管理（如 request/session）。
_event_bus_instance: EventBusInterface | None = None
_metrics_instance: MetricsInterface | None = None
_llm_instance: LLMServiceInterface | None = None
_connection_manager_instance: ConnectionManagerInterface | None = None


def get_event_bus() -> EventBusInterface:
    """获取事件总线实例。"""
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = EventBus()
    return _event_bus_instance


def get_metrics() -> MetricsInterface:
    """获取监控指标收集器实例。"""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = MetricsCollector()
    return _metrics_instance


def get_llm_service() -> LLMServiceInterface:
    """获取 LLM 服务实例。"""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = LLMService()
    return _llm_instance


# 占位：待实现 ConnectionManager 实例化
def get_connection_manager() -> ConnectionManagerInterface:
    """获取连接管理器实例（后续替换全局字典）。"""
    global _connection_manager_instance
    if _connection_manager_instance is None:
        # 临时空实现，后续步骤会提供真正的类
        from core.monitor.connection_manager import ConnectionManager  # 延迟导入以避免循环

        _connection_manager_instance = ConnectionManager()
    return _connection_manager_instance


# 类型别名，便于在路由上直接声明
EventBusDep = Annotated[EventBusInterface, Depends(get_event_bus)]
MetricsDep = Annotated[MetricsInterface, Depends(get_metrics)]
LLMDep = Annotated[LLMServiceInterface, Depends(get_llm_service)]
ConnectionManagerDep = Annotated[ConnectionManagerInterface, Depends(get_connection_manager)]

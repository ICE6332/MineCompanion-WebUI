"""FastAPI 依赖注入工厂（通过 app.state 管理实例）。"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from core.interfaces import (
    EventBusInterface,
    MetricsInterface,
    LLMServiceInterface,
    ConnectionManagerInterface,
)
from core.storage.interfaces import CacheStorage

# 获取依赖实例（均由 lifespan 初始化存入 app.state）


def get_event_bus(request: Request) -> EventBusInterface:
    return request.app.state.event_bus


def get_metrics(request: Request) -> MetricsInterface:
    return request.app.state.metrics


def get_llm_service(request: Request) -> LLMServiceInterface:
    return request.app.state.llm_service


def get_connection_manager(request: Request) -> ConnectionManagerInterface:
    return request.app.state.connection_manager


def get_cache_storage(request: Request) -> CacheStorage:
    return request.app.state.cache_storage


# 类型别名，便于在路由上直接声明
EventBusDep = Annotated[EventBusInterface, Depends(get_event_bus)]
MetricsDep = Annotated[MetricsInterface, Depends(get_metrics)]
LLMDep = Annotated[LLMServiceInterface, Depends(get_llm_service)]
ConnectionManagerDep = Annotated[ConnectionManagerInterface, Depends(get_connection_manager)]
CacheStorageDep = Annotated[CacheStorage, Depends(get_cache_storage)]

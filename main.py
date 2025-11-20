from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import logging
from contextlib import asynccontextmanager

from api import websocket, monitor_ws, stats
from api.routes import llm
from api.middleware import SecurityHeadersMiddleware
from api.monitor_ws import register_monitor_subscriptions
from api.health import router as health_router
from core.logging_config import setup_logging
from config.settings import settings
from core.monitor.event_bus import EventBus
from core.monitor.metrics_collector import MetricsCollector
from core.monitor.connection_manager import ConnectionManager
from core.llm.service import LLMService
from core.storage.memory import MemoryCacheStorage
from core.storage.redis import RedisCacheStorage


logger = setup_logging(level=os.getenv("LOG_LEVEL", "INFO"), log_file=os.getenv("LOG_FILE"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: 初始化共享资源
    cache_storage = (
        RedisCacheStorage(settings.redis_url) if settings.storage_backend == "redis" else MemoryCacheStorage()
    )
    app.state.cache_storage = cache_storage
    app.state.event_bus = EventBus(history_size=settings.event_history_size)
    app.state.metrics = MetricsCollector()
    app.state.connection_manager = ConnectionManager()
    app.state.llm_service = LLMService(cache_storage=cache_storage)

    logger.info("存储后端: %s", settings.storage_backend)
    # 注册监控事件订阅，将事件广播到前端监控页面
    register_monitor_subscriptions(app.state.event_bus)
    yield

    # Shutdown: 清理资源
    if hasattr(cache_storage, "close"):
        try:
            await cache_storage.close()  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: BLE001
            logger.warning("关闭缓存存储失败: %s", exc)


app = FastAPI(
    title="MineCompanionAI-WebUI",
    version="0.4.0",
    description="AI Companion Control Panel & Service",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加安全头部中间件
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(websocket.router, tags=["WebSocket"])
app.include_router(monitor_ws.router, tags=["Monitor"])
app.include_router(stats.router, prefix="/api/stats", tags=["Statistics"])
app.include_router(llm.router)
app.include_router(health_router)
@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("MineCompanionAI-WebUI Starting...")
    logger.info("API Docs:  http://localhost:8080/docs")
    logger.info("Frontend:  http://localhost:5173 (dev)")
    logger.info("WebSocket: ws://localhost:8080/ws")
    logger.info("Monitor WS: ws://localhost:8080/ws/monitor")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("MineCompanionAI-WebUI shutting down...")


@app.get("/health", include_in_schema=False)
@app.get("/health/", include_in_schema=False)
async def root_health_check():
    return {"status": "ok", "version": app.version}


@app.get("/api/health")
@app.get("/api/health/")
async def health_check():
    return {"status": "ok", "version": app.version}


@app.get("/", include_in_schema=False)
@app.get("", include_in_schema=False)
async def index():
    # 根路径默认跳转到 API 文档，避免返回 404 Not Found
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from api import websocket, monitor_ws, stats
from api.routes import llm
from api.middleware import SecurityHeadersMiddleware
from core.dependencies import get_event_bus
from api.monitor_ws import register_monitor_subscriptions
from api.health import router as health_router
from core.logging_config import setup_logging
import os
import logging

app = FastAPI(
    title="MineCompanionAI-WebUI",
    version="0.4.0",
    description="AI Companion Control Panel & Service",
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

# 初始化日志
logger = setup_logging(level=os.getenv("LOG_LEVEL", "INFO"), log_file=os.getenv("LOG_FILE"))
@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("MineCompanionAI-WebUI Starting...")
    logger.info("API Docs:  http://localhost:8080/docs")
    logger.info("Frontend:  http://localhost:5173 (dev)")
    logger.info("WebSocket: ws://localhost:8080/ws")
    logger.info("Monitor WS: ws://localhost:8080/ws/monitor")
    logger.info("=" * 60)
    # 注册监控事件订阅，将事件广播到前端监控页面
    event_bus = get_event_bus()
    register_monitor_subscriptions(event_bus)


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

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from api import websocket, monitor_ws, stats
from api.routes import llm

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

app.include_router(websocket.router, tags=["WebSocket"])
app.include_router(monitor_ws.router, tags=["Monitor"])
app.include_router(stats.router, prefix="/api/stats", tags=["Statistics"])
app.include_router(llm.router)


@app.on_event("startup")
async def startup_event():
    print("=" * 60)
    print("MineCompanionAI-WebUI Starting...")
    print("=" * 60)
    print("API Docs:  http://localhost:8080/docs")
    print("Frontend:  http://localhost:5173 (dev)")
    print("WebSocket: ws://localhost:8080/ws")
    print("Monitor WS: ws://localhost:8080/ws/monitor")
    print("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    print("MineCompanionAI-WebUI shutting down...")


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

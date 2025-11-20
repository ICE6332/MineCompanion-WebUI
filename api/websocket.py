import json
from datetime import datetime, timezone
from uuid import uuid4
from typing import Any, Dict

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException

from core.monitor.event_types import MonitorEventType
from api.protocol import CompactProtocol
from api.validation import ModMessage
from api.rate_limiter import WebSocketRateLimiter
from core.monitor.token_tracker import TokenTracker
from core.dependencies import EventBusDep, MetricsDep, ConnectionManagerDep
from config.settings import settings

router = APIRouter()
logger = logging.getLogger("api.websocket")

# WebSocket 速率限制器（配置驱动）
mod_rate_limiter = WebSocketRateLimiter(
    max_messages=settings.rate_limit_messages, window_seconds=settings.rate_limit_window
)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    event_bus: EventBusDep,
    metrics: MetricsDep,
    conn_mgr: ConnectionManagerDep,
):
    """
    WebSocket 端点
    当前实现：解析模组消息并触发监控事件
    TODO: 集成 LLM、记忆系统、决策引擎
    """
    client_id = f"mod-{uuid4()}"
    await websocket.accept()
    conn_mgr.add(client_id, websocket)
    logger.info("[OK] Client connected: %s", client_id)
    connection_timestamp = datetime.now(timezone.utc).isoformat()
    event_bus.publish(
        MonitorEventType.MOD_CONNECTED,
        {"client_id": client_id, "timestamp": connection_timestamp},
    )
    metrics.set_mod_connected(client_id)

    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            
            # 检查速率限制
            if not mod_rate_limiter.check_rate_limit(client_id):
                error_response = {
                    "type": "error",
                    "data": {"message": "消息发送过快，请稍后再试（限制：100条/分钟）"},
                }
                await websocket.send_json(error_response)
                continue  # 跳过此消息，但不断开连接

            logger.debug("← Received from %s: %s...", client_id, data[:100])
            try:
                # 解析来自 Mod 的 JSON 消息
                message = json.loads(data)
            except json.JSONDecodeError:
                error_response = {
                    "type": "error",
                    "data": {"message": "无法解析 JSON 数据"},
                }
                await websocket.send_json(error_response)
                logger.debug("→ Sent to %s: %s...", client_id, json.dumps(error_response)[:100])
                error_timestamp = datetime.now(timezone.utc).isoformat()
                event_bus.publish(
                    MonitorEventType.MESSAGE_RECEIVED,
                    {
                        "client_id": client_id,
                        "message_type": "invalid_json",
                        "timestamp": error_timestamp,
                        "preview": data[:100],
                    },
                )
                metrics.record_message_received("invalid_json")
                metrics.update_mod_last_message()
                metrics.record_message_sent("error")
                event_bus.publish(
                    MonitorEventType.MESSAGE_SENT,
                    {
                        "client_id": client_id,
                        "message_type": "error",
                        "timestamp": error_timestamp,
                    },
                )
                continue

            # 预解析：统一紧凑/标准/旧版 data 结构，确保路由基于长类型值
            try:
                normalized_msg = CompactProtocol.parse(message)
            except Exception:
                error_payload = {
                    "type": "error",
                    "data": {"message": "无法解析协议字段"},
                }
                await websocket.send_json(error_payload)
                metrics.record_message_sent("error")
                event_bus.publish(
                    MonitorEventType.MESSAGE_SENT,
                    {
                        "client_id": client_id,
                        "message_type": "error",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )
                continue

            msg_type = normalized_msg.get("type", "unknown")
            timestamp = datetime.now(timezone.utc).isoformat()
            preview = data[:100]
            event_bus.publish(
                MonitorEventType.MESSAGE_RECEIVED,
                {
                    "client_id": client_id,
                    "message_type": msg_type,
                    "timestamp": timestamp,
                    "preview": preview,
                },
            )
            metrics.record_message_received(msg_type)
            metrics.update_mod_last_message()

            response_preview = None
            if msg_type == "connection_init":
                response_preview = await handle_connection_init(
                    websocket, message, client_id, event_bus, metrics
                )
            elif msg_type == "game_state_update":
                response_preview = await handle_game_state_update(
                    websocket, message, client_id, event_bus, metrics
                )
            elif msg_type == "conversation_request":
                response_preview = await handle_conversation_request(
                    websocket, message, client_id, event_bus, metrics
                )
            else:
                error_payload = {
                    "type": "error",
                    "data": {
                        "message": f"未知消息类型: {msg_type}",
                        "client_id": client_id,
                    },
                }
                await websocket.send_json(error_payload)
                response_preview = json.dumps(error_payload)
                metrics.record_message_sent("error")
                event_bus.publish(
                    MonitorEventType.MESSAGE_SENT,
                    {
                        "client_id": client_id,
                        "message_type": "error",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )

            if response_preview:
                logger.debug("→ Sent to %s: %s...", client_id, response_preview[:100])

    except WebSocketDisconnect:
        logger.warning("[ERR] Client disconnected: %s", client_id)
        event_bus.publish(
            MonitorEventType.MOD_DISCONNECTED,
            {"client_id": client_id, "timestamp": datetime.now(timezone.utc).isoformat()},
        )
        metrics.set_mod_disconnected()
    except Exception as e:
        logger.error("[ERR] WebSocket error for %s: %s", client_id, e)
    finally:
        mod_rate_limiter.clear(client_id)
        conn_mgr.remove(client_id)


async def handle_connection_init(
    websocket: WebSocket,
    message: Dict[str, Any],
    client_id: str,
    event_bus: EventBusDep,
    metrics: MetricsDep,
):
    """处理连接初始化并返回确认"""
    response = {
        "type": "connection_ack",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {"client_id": client_id},
    }
    await websocket.send_json(response)
    event_bus.publish(
        MonitorEventType.MESSAGE_SENT,
        {
            "client_id": client_id,
            "message_type": "connection_ack",
            "timestamp": response["timestamp"],
        },
    )
    metrics.record_message_sent("connection_ack")
    return json.dumps(response)


async def handle_game_state_update(
    websocket: WebSocket,
    message: Dict[str, Any],
    client_id: str,
    event_bus: EventBusDep,
    metrics: MetricsDep,
):
    """处理游戏状态更新"""
    try:
        # 提取游戏状态数据
        game_state = message.get("data", {})
        player_name = game_state.get("player_name", "Unknown")

        # 这里未来会处理游戏状态
        # 目前只是记录和确认
        response = {
            "type": "game_state_ack",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {"status": "received", "player": player_name},
        }
        await websocket.send_json(response)
        metrics.record_message_sent("game_state_ack")
        event_bus.publish(
            MonitorEventType.MESSAGE_SENT,
            {
                "client_id": client_id,
                "message_type": "game_state_ack",
                "timestamp": response["timestamp"],
            },
        )
        return json.dumps(response)
    except Exception as e:
        logger.error("Error handling game state: %s", e)
        return None


async def handle_conversation_request(
    websocket: WebSocket,
    message: Dict[str, Any],
    client_id: str,
    event_bus: EventBusDep,
    metrics: MetricsDep,
):
    """处理对话请求"""
    try:
        # 1. 解析紧凑消息（兼容标准/旧版 data 结构）
        standard_message: Dict[str, Any] = CompactProtocol.parse(message)

        # 2. 提取数据
        player_name: str = standard_message.get("playerName", "Player")
        player_message: str = standard_message.get("message", "")
        message_id: str = standard_message.get("id", str(uuid4()))

        # 3. Echo 模式（模拟 LLM）
        reply: str = f"[Echo] 收到：{player_message}"

        # 4. 构造标准响应（顶层长字段，无 data 嵌套）
        standard_response: Dict[str, Any] = {
            "id": message_id,
            "type": "conversation_response",
            "companionName": "AICompanion",
            "message": reply,
        }

        # 5. 转为紧凑格式（仅用于token统计，不发送）
        compact_response: Dict[str, Any] = CompactProtocol.compact(standard_response)

        # 6. Token 统计
        stats: Dict[str, Any] = TokenTracker.compare(standard_response, compact_response)
        stats["client_id"] = client_id
        stats["message_type"] = "conversation"
        logger.info(
            "[Token Stats] 标准=%s 紧凑=%s 节省=%s%%",
            stats["standard_tokens"],
            stats["compact_tokens"],
            stats["saved_percent"],
        )

        # 7. 发送响应（发送标准格式给Mod，紧凑格式只用于LLM）
        await websocket.send_json(standard_response)
        metrics.record_message_sent("conversation_response")

        # 8. 发布统计事件（供前端监控）
        # 记录实际消耗的紧凑格式 token 数量
        metrics.record_token_usage(stats["compact_tokens"])
        event_bus.publish(
            MonitorEventType.TOKEN_STATS,
            stats,
        )

        event_bus.publish(
            MonitorEventType.MESSAGE_SENT,
            {
                "client_id": client_id,
                "message_type": "conversation_response",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        return json.dumps(standard_response)
    except Exception as e:
        logger.exception("Error handling conversation request: %s", e)
        return None


@router.post("/api/ws/send-json")
@router.post("/api/ws/send-json")
async def send_json_to_mod(
    message: ModMessage,
    event_bus: EventBusDep,
    metrics: MetricsDep,
    conn_mgr: ConnectionManagerDep,
):
    """
    从 Web UI 转发原始 JSON 消息到当前已连接的模组。
    主要用于开发阶段临时调试通信链路。
    """
    if conn_mgr.count() == 0:
        raise HTTPException(status_code=503, detail="当前没有任何模组通过 WebSocket 连接")

    # 优先使用 MetricsCollector 记录的模组连接 ID
    connection_status = metrics.get_connection_status()
    target_id = connection_status.mod_client_id

    if not target_id or not conn_mgr.get(target_id):
        # 回退：选择任意一个活跃连接
        ids = conn_mgr.get_all_ids()
        target_id = ids[0] if ids else None

    if not target_id:
        raise HTTPException(status_code=503, detail="找不到可用的模组连接")

    websocket = conn_mgr.get(target_id)
    if websocket is None:
        raise HTTPException(status_code=503, detail="模组连接已失效，请重新连接后重试")

    # 将前端提供的 JSON 原样下发给模组（已通过 Pydantic 验证）
    await websocket.send_json(message.model_dump(exclude_none=True))

    msg_type = message.type
    metrics.record_message_sent(msg_type)
    event_bus.publish(
        MonitorEventType.MESSAGE_SENT,
        {
            "client_id": target_id,
            "message_type": msg_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

    return {"status": "ok", "target": target_id, "type": msg_type}

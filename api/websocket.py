import json
from datetime import datetime
from uuid import uuid4
from typing import Any, Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException

from core.monitor.event_bus import EventBus
from core.monitor.event_types import MonitorEventType
from core.monitor.metrics_collector import MetricsCollector
from api.protocol import CompactProtocol
from api.validation import ModMessage
from api.rate_limiter import WebSocketRateLimiter
from core.monitor.token_tracker import TokenTracker

router = APIRouter()

# 简单的内存连接管理器（后续可扩展为更复杂的实现）
active_connections: Dict[str, WebSocket] = {}

# WebSocket 速率限制器（每分钟最多 100 条消息）
mod_rate_limiter = WebSocketRateLimiter(max_messages=100, window_seconds=60)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 端点
    当前实现：解析模组消息并触发监控事件
    TODO: 集成 LLM、记忆系统、决策引擎
    """
    client_id = f"mod-{uuid4()}"
    await websocket.accept()
    active_connections[client_id] = websocket
    print(f"[OK] Client connected: {client_id}")
    connection_timestamp = datetime.utcnow().isoformat()
    EventBus.publish(
        MonitorEventType.MOD_CONNECTED,
        {"client_id": client_id, "timestamp": connection_timestamp},
    )
    MetricsCollector.set_mod_connected(client_id)

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
            
            print(f"← Received from {client_id}: {data[:100]}...")
            try:
                # 解析来自 Mod 的 JSON 消息
                message = json.loads(data)
            except json.JSONDecodeError:
                error_response = {
                    "type": "error",
                    "data": {"message": "无法解析 JSON 数据"},
                }
                await websocket.send_json(error_response)
                print(
                    f"→ Sent to {client_id}: {json.dumps(error_response)[:100]}..."
                )
                error_timestamp = datetime.utcnow().isoformat()
                EventBus.publish(
                    MonitorEventType.MESSAGE_RECEIVED,
                    {
                        "client_id": client_id,
                        "message_type": "invalid_json",
                        "timestamp": error_timestamp,
                        "preview": data[:100],
                    },
                )
                MetricsCollector.record_message_received("invalid_json")
                MetricsCollector.update_mod_last_message()
                MetricsCollector.record_message_sent("error")
                EventBus.publish(
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
                MetricsCollector.record_message_sent("error")
                EventBus.publish(
                    MonitorEventType.MESSAGE_SENT,
                    {
                        "client_id": client_id,
                        "message_type": "error",
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )
                continue

            msg_type = normalized_msg.get("type", "unknown")
            timestamp = datetime.utcnow().isoformat()
            preview = data[:100]
            EventBus.publish(
                MonitorEventType.MESSAGE_RECEIVED,
                {
                    "client_id": client_id,
                    "message_type": msg_type,
                    "timestamp": timestamp,
                    "preview": preview,
                },
            )
            MetricsCollector.record_message_received(msg_type)
            MetricsCollector.update_mod_last_message()

            response_preview = None
            if msg_type == "connection_init":
                response_preview = await handle_connection_init(
                    websocket, message, client_id
                )
            elif msg_type == "game_state_update":
                response_preview = await handle_game_state_update(
                    websocket, message, client_id
                )
            elif msg_type == "conversation_request":
                response_preview = await handle_conversation_request(
                    websocket, message, client_id
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
                MetricsCollector.record_message_sent("error")
                EventBus.publish(
                    MonitorEventType.MESSAGE_SENT,
                    {
                        "client_id": client_id,
                        "message_type": "error",
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )

            if response_preview:
                print(f"→ Sent to {client_id}: {response_preview[:100]}...")

    except WebSocketDisconnect:
        print(f"[ERR] Client disconnected: {client_id}")
        EventBus.publish(
            MonitorEventType.MOD_DISCONNECTED,
            {"client_id": client_id, "timestamp": datetime.utcnow().isoformat()},
        )
        MetricsCollector.set_mod_disconnected()
    except Exception as e:
        print(f"[ERR] WebSocket error for {client_id}: {e}")
    finally:
        mod_rate_limiter.clear(client_id)
        active_connections.pop(client_id, None)


async def handle_connection_init(
    websocket: WebSocket, message: Dict[str, Any], client_id: str
):
    """处理连接初始化并返回确认"""
    response = {
        "type": "connection_ack",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {"client_id": client_id},
    }
    await websocket.send_json(response)
    EventBus.publish(
        MonitorEventType.MESSAGE_SENT,
        {
            "client_id": client_id,
            "message_type": "connection_ack",
            "timestamp": response["timestamp"],
        },
    )
    MetricsCollector.record_message_sent("connection_ack")
    return json.dumps(response)


async def handle_game_state_update(
    websocket: WebSocket, message: Dict[str, Any], client_id: str
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
            "timestamp": datetime.utcnow().isoformat(),
            "data": {"status": "received", "player": player_name},
        }
        await websocket.send_json(response)
        MetricsCollector.record_message_sent("game_state_ack")
        EventBus.publish(
            MonitorEventType.MESSAGE_SENT,
            {
                "client_id": client_id,
                "message_type": "game_state_ack",
                "timestamp": response["timestamp"],
            },
        )
        return json.dumps(response)
    except Exception as e:
        print(f"Error handling game state: {e}")
        return None


async def handle_conversation_request(
    websocket: WebSocket, message: Dict[str, Any], client_id: str
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
        print(
            f'[Token Stats] 标准={stats["standard_tokens"]} 紧凑={stats["compact_tokens"]} 节省={stats["saved_percent"]}%'
        )

        # 7. 发送响应（发送标准格式给Mod，紧凑格式只用于LLM）
        await websocket.send_json(standard_response)
        MetricsCollector.record_message_sent("conversation_response")

        # 8. 发布统计事件（供前端监控）
        # 记录实际消耗的紧凑格式 token 数量
        MetricsCollector.record_token_usage(stats["compact_tokens"])
        EventBus.publish(
            MonitorEventType.TOKEN_STATS,
            stats,
        )

        EventBus.publish(
            MonitorEventType.MESSAGE_SENT,
            {
                "client_id": client_id,
                "message_type": "conversation_response",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return json.dumps(standard_response)
    except Exception as e:
        print(f"Error handling conversation request: {e}")
        import traceback
        traceback.print_exc()
        return None


@router.post("/api/ws/send-json")
async def send_json_to_mod(message: ModMessage):
    """
    从 Web UI 转发原始 JSON 消息到当前已连接的模组。
    主要用于开发阶段临时调试通信链路。
    """
    if not active_connections:
        raise HTTPException(status_code=503, detail="当前没有任何模组通过 WebSocket 连接")

    # 优先使用 MetricsCollector 记录的模组连接 ID
    connection_status = MetricsCollector.get_connection_status()
    target_id = connection_status.mod_client_id

    if not target_id or target_id not in active_connections:
        # 回退：选择任意一个活跃连接
        target_id = next(iter(active_connections.keys()), None)

    if not target_id:
        raise HTTPException(status_code=503, detail="找不到可用的模组连接")

    websocket = active_connections.get(target_id)
    if websocket is None:
        raise HTTPException(status_code=503, detail="模组连接已失效，请重新连接后重试")

    # 将前端提供的 JSON 原样下发给模组（已通过 Pydantic 验证）
    await websocket.send_json(message.model_dump(exclude_none=True))

    msg_type = message.type
    MetricsCollector.record_message_sent(msg_type)
    EventBus.publish(
        MonitorEventType.MESSAGE_SENT,
        {
            "client_id": target_id,
            "message_type": msg_type,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    return {"status": "ok", "target": target_id, "type": msg_type}

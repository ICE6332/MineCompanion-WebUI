"""处理 conversation_request 消息。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import WebSocket

from api.handlers.base import MessageHandler
from api.handlers.context import HandlerContext
from api.protocol import CompactProtocol
from core.monitor.event_types import MonitorEventType
from core.monitor.token_tracker import TokenTracker


class ConversationHandler(MessageHandler):
    async def handle(self, websocket: WebSocket, message: Dict[str, Any], context: HandlerContext) -> str:
        standard_message: Dict[str, Any] = CompactProtocol.parse(message)

        player_name: str = standard_message.get("playerName", "Player")
        player_message: str = standard_message.get("message", "")
        message_id: str = standard_message.get("id", "")

        reply: str = f"[Echo] 收到：{player_message}"

        standard_response: Dict[str, Any] = {
            "id": message_id,
            "type": "conversation_response",
            "companionName": "AICompanion",
            "message": reply,
        }

        compact_response: Dict[str, Any] = CompactProtocol.compact(standard_response)

        stats: Dict[str, Any] = TokenTracker.compare(standard_response, compact_response)
        stats["client_id"] = context.client_id
        stats["message_type"] = "conversation"

        context.metrics.record_message_sent("conversation_response")
        context.metrics.record_token_usage(stats["compact_tokens"])

        context.event_bus.publish(MonitorEventType.TOKEN_STATS, stats)
        context.event_bus.publish(
            MonitorEventType.MESSAGE_SENT,
            {
                "client_id": context.client_id,
                "message_type": "conversation_response",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        await websocket.send_json(standard_response)
        return json.dumps(standard_response)

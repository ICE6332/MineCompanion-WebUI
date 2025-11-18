"""LLM 路由（Mock 版本）。

该路由演示标准 JSON 请求与紧凑协议之间的转换流程，返回硬编码的对话响应。
"""

from typing import Any, Dict, List, Literal, Optional
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from api.protocol import CompactProtocol

logger = logging.getLogger("api.routes.llm")

router = APIRouter(prefix="/api/llm", tags=["LLM"])


class ActionCommand(BaseModel):
    """玩家指令动作。"""

    type: str = Field(..., description="动作类型")
    command: Optional[str] = Field(None, description="指令内容")


class ConversationRequest(BaseModel):
    """会话请求模型。"""

    id: Optional[str] = Field(None, description="请求唯一标识")
    type: Literal["conversation_request"] = Field(
        ..., description="消息类型，期望为 conversation_request"
    )
    playerName: str = Field(..., min_length=1, description="玩家名称")
    companionName: Optional[str] = Field(None, description="伙伴名称")
    message: Optional[str] = Field(None, description="玩家消息")
    action: Optional[List[Dict[str, Any]]] = Field(
        None, description="动作列表，保持与前端兼容"
    )
    timestamp: Optional[str] = Field(None, description="时间戳，ISO8601 字符串")
    position: Optional[Dict[str, Any]] = Field(None, description="玩家位置信息")
    health: Optional[float] = Field(None, description="玩家生命值")

    model_config = ConfigDict(populate_by_name=True)


@router.post("/player")
async def handle_player_request(payload: ConversationRequest) -> Dict[str, Any]:
    """接收玩家消息，压缩为紧凑协议并返回模拟响应。"""

    try:
        standard_request: Dict[str, Any] = payload.model_dump(
            by_alias=True, exclude_none=True
        )
        compact_request = CompactProtocol.compact(standard_request)
        logger.info("收到会话请求，已压缩为紧凑协议: %s", compact_request)

        mock_standard_response: Dict[str, Any] = {
            "type": "conversation_response",
            "playerName": standard_request.get("playerName"),
            "message": "好的，我会跟着你！",
            "action": [
                {
                    "type": "command",
                    "command": "/say 收到指令！",
                }
            ],
        }

        compact_response = CompactProtocol.compact(mock_standard_response)
        expanded_response = CompactProtocol.parse(compact_response)
        logger.info("返回展开后的响应: %s", expanded_response)

        return expanded_response
    except Exception as exc:  # noqa: BLE001
        logger.exception("处理 LLM 请求失败: %s", exc)
        raise HTTPException(status_code=500, detail="LLM 处理失败，请稍后重试") from exc

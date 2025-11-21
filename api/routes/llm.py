"""LLM 路由（真实服务版本）。

该路由接收玩家消息，通过 LLMService 调用真实大模型，并返回响应。
"""

import json
import logging
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from api.protocol import CompactProtocol
from core.dependencies import LLMDep

logger = logging.getLogger("api.routes.llm")

router = APIRouter(prefix="/api/llm", tags=["LLM"])


def _mask_api_key(api_key: Optional[str]) -> str:
    """日志中隐藏 API Key，仅展示前 8 位。"""
    if not api_key:
        return ""
    return f"{api_key[:8]}***"


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
    # 新增：LLM 配置
    llmConfig: Optional[Dict[str, str]] = Field(
        None, description="LLM 配置（provider, model, apiKey, baseUrl）"
    )

    model_config = ConfigDict(populate_by_name=True)


@router.post("/player")
async def handle_player_request(payload: ConversationRequest, llm: LLMDep) -> Dict[str, Any]:
    """接收玩家消息，压缩为紧凑协议并调用真实 LLM 服务。"""

    standard_request: Dict[str, Any] = payload.model_dump(
        by_alias=True, exclude_none=True
    )
    masked_payload = standard_request.copy()
    llm_config_log = standard_request.get("llmConfig")
    if llm_config_log:
        masked_payload["llmConfig"] = llm_config_log.copy()
        if llm_config_log.get("apiKey"):
            masked_payload["llmConfig"]["apiKey"] = _mask_api_key(llm_config_log.get("apiKey"))
    logger.info("收到玩家 LLM 请求: payload=%s", masked_payload)

    try:
        
        # 如果前端提供了 LLM 配置，则覆盖后端默认配置
        if payload.llmConfig:
            logger.info(f"使用前端提供的 LLM 配置: provider={payload.llmConfig.get('provider')}, model={payload.llmConfig.get('model')}")
            llm.config["provider"] = payload.llmConfig.get("provider", llm.config["provider"])
            llm.config["model"] = payload.llmConfig.get("model", llm.config["model"])
            llm.config["api_key"] = payload.llmConfig.get("apiKey", llm.config["api_key"])
            llm.config["base_url"] = payload.llmConfig.get("baseUrl", llm.config["base_url"])

        api_key = llm.config.get("api_key")
        if not api_key:
            logger.error("LLM 请求失败：API Key 未配置")
            raise HTTPException(status_code=400, detail="API Key 未配置")
        
        # 1. 构造 Prompt
        player_name = standard_request.get("playerName", "Player")
        message_content = standard_request.get("message", "")
        
        # 简单的 Prompt 构造 (后续可移至 core/personality)
        messages = [
            {"role": "system", "content": f"你是一个 Minecraft 游戏中的 AI 伙伴。你的名字叫 {standard_request.get('companionName', 'AI')}。"},
            {"role": "user", "content": f"[{player_name}]: {message_content}"}
        ]

        # 2. 调用 LLM 服务
        logger.info("LLM 消息内容: %s", messages)
        response = await llm.chat_completion(messages=messages)

        # 3. 解析响应
        llm_reply = response["choices"][0]["message"]["content"]
        try:
            response_preview = json.dumps(response, ensure_ascii=False)
        except TypeError:
            response_preview = str(response)
        logger.info("LLM 原始响应（前 200 字符）: %s", response_preview[:200])
        
        # 4. 构造标准响应
        standard_response: Dict[str, Any] = {
            "type": "conversation_response",
            "playerName": player_name,
            "message": llm_reply,
            # 暂时保留简单的动作逻辑，或者让 LLM 输出 JSON 格式的动作
            "action": [], 
        }

        # 5. 协议转换 (保持兼容性)
        compact_response = CompactProtocol.compact(standard_response)
        expanded_response = CompactProtocol.parse(compact_response)
        logger.info("LLM 响应: %s", expanded_response)

        return expanded_response
    except Exception as exc:
        logger.exception("处理 LLM 请求失败: %s", exc)
        raise HTTPException(status_code=500, detail=f"LLM 处理失败: {str(exc)}") from exc

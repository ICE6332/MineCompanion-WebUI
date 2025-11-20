"""LLM 服务核心实现。

使用 LiteLLM 统一接口，支持 OpenAI、Anthropic、Gemini 以及兼容 OpenAI 格式的第三方服务。
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from dotenv import load_dotenv

import litellm

# 加载环境变量
load_dotenv()

logger = logging.getLogger("core.llm.service")


class LLMService:
    """LLM 服务类，封装 LiteLLM 调用。"""

    def __init__(self):
        self.config = self._load_config()
        self._setup_litellm()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置，优先使用环境变量，其次是 settings.json。"""
        settings_path = Path("config/settings.json")
        file_config = {}
        
        if settings_path.exists():
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    file_config = data.get("llm", {})
            except Exception as e:
                logger.error(f"加载 settings.json 失败: {e}")

        # 环境变量优先级更高
        config = {
            "provider": os.getenv("LLM_PROVIDER", file_config.get("provider", "openai")),
            "model": os.getenv("LLM_MODEL", file_config.get("model", "gpt-4")),
            "api_key": os.getenv("LLM_API_KEY", file_config.get("api_key", "")),
            "base_url": os.getenv("LLM_BASE_URL", file_config.get("base_url", "")),
            "api_version": os.getenv("LLM_API_VERSION", file_config.get("api_version", "")),
        }
        
        return config

    def _setup_litellm(self):
        """配置 LiteLLM。"""
        # 设置 API Key
        if self.config["api_key"]:
            # LiteLLM 会自动查找环境变量，但这里显式设置更安全
            # 注意：不同 provider 需要不同的环境变量名，但 LiteLLM 支持通过参数传递 api_key
            pass
        
        # 配置日志
        litellm.set_verbose = False  # 设置为 True 可开启详细调试日志

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        发送聊天请求到 LLM。

        Args:
            messages: 消息列表，例如 [{"role": "user", "content": "hello"}]
            temperature: 温度参数
            max_tokens: 最大生成 token 数
            **kwargs: 其他 LiteLLM 支持的参数

        Returns:
            LiteLLM 的响应对象（字典格式）
        """
        try:
            model = self.config["model"]
            provider = self.config["provider"]
            
            # 构建完整的模型名称
            # 如果是 openai 兼容的第三方服务，通常不需要加 provider 前缀，或者直接用 model 名
            # LiteLLM 约定：对于 openai 兼容接口，如果 provider 是 openai，可以直接用 model 名
            # 如果是 anthropic/gemini 等，litellm 通常需要前缀，如 "anthropic/claude-3"
            # 这里我们做一个简单的处理：如果 provider 不是 openai，且 model 不包含 /，则加上前缀
            
            full_model_name = model
            if provider != "openai" and "/" not in model:
                full_model_name = f"{provider}/{model}"
            
            # 准备参数
            params = {
                "model": full_model_name,
                "messages": messages,
                "temperature": temperature,
                "api_key": self.config["api_key"],
            }

            if max_tokens:
                params["max_tokens"] = max_tokens
            
            # 如果有 base_url (用于 DeepSeek, Moonshot, Local 等)
            if self.config["base_url"]:
                params["api_base"] = self.config["base_url"]
            
            # 如果有 api_version
            if self.config["api_version"]:
                params["api_version"] = self.config["api_version"]

            # 合并其他参数
            params.update(kwargs)

            logger.info(f"发送 LLM 请求: model={full_model_name}, base_url={self.config.get('base_url')}")
            
            # 调用 LiteLLM (异步)
            response = await litellm.acompletion(**params)
            
            return response

        except Exception as e:
            logger.error(f"LLM 请求失败: {e}")
            # 可以在这里做更细致的错误处理，比如重试或返回特定错误码
            raise e

# 单例实例
llm_service = LLMService()

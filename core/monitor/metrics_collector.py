"""监控指标收集器实现。"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict

from models.monitor import MessageStats, ConnectionStatus, TokenTrendStats, TokenTrendPoint


class MetricsCollector:
    """负责聚合消息统计与连接状态的单例工具。"""

    _instance: "MetricsCollector" | None = None
    _stats: MessageStats
    _connection_status: ConnectionStatus
    _token_trend: Dict[str, int]

    def __new__(cls) -> "MetricsCollector":
        """确保仅创建一个指标收集器实例。"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls.reset_stats()
            cls._connection_status = ConnectionStatus()
            cls._token_trend = {}
        return cls._instance

    @classmethod
    def _ensure_instance(cls) -> None:
        """保证在访问前已经完成初始化。"""
        if cls._instance is None:
            cls()

    @classmethod
    def _ensure_messages_dict(cls) -> None:
        """保证消息类型统计一直使用 defaultdict。"""
        cls._ensure_instance()
        if not isinstance(cls._stats.messages_per_type, defaultdict):
            existing: Dict[str, int] = dict(cls._stats.messages_per_type or {})
            cls._stats.messages_per_type = defaultdict(int, existing)

    @classmethod
    def record_message_received(cls, message_type: str) -> None:
        """记录接收到的消息数量。"""
        cls._ensure_instance()
        cls._stats.total_received += 1
        cls._ensure_messages_dict()
        messages_per_type: Dict[str, int] = cls._stats.messages_per_type
        messages_per_type[message_type] += 1

    @classmethod
    def record_message_sent(cls, message_type: str) -> None:
        """记录发送出去的消息数量。"""
        cls._ensure_instance()
        cls._stats.total_sent += 1
        cls._ensure_messages_dict()
        messages_per_type: Dict[str, int] = cls._stats.messages_per_type
        messages_per_type[message_type] += 1

    @classmethod
    def set_mod_connected(cls, client_id: str) -> None:
        """更新模组连接状态。"""
        cls._ensure_instance()
        cls._connection_status.mod_client_id = client_id
        cls._connection_status.mod_connected_at = datetime.utcnow()

    @classmethod
    def set_mod_disconnected(cls) -> None:
        """标记模组断开连接。"""
        cls._ensure_instance()
        cls._connection_status.mod_client_id = None
        cls._connection_status.mod_connected_at = None

    @classmethod
    def update_mod_last_message(cls) -> None:
        """刷新模组最近一次消息时间。"""
        cls._ensure_instance()
        cls._connection_status.mod_last_message_at = datetime.utcnow()

    @classmethod
    def set_llm_status(cls, provider: str, ready: bool) -> None:
        """设置当前 LLM 连接状态。"""
        cls._ensure_instance()
        cls._connection_status.llm_provider = provider
        cls._connection_status.llm_ready = ready

    @classmethod
    def get_stats(cls) -> MessageStats:
        """返回当前消息统计信息。"""
        cls._ensure_instance()
        return cls._stats

    @classmethod
    def get_connection_status(cls) -> ConnectionStatus:
        """返回当前连接状态。"""
        cls._ensure_instance()
        return cls._connection_status

    @classmethod
    def record_token_usage(cls, tokens: int) -> None:
        """记录 token 消耗，自动按当前小时聚合。"""
        cls._ensure_instance()
        now = datetime.now(timezone.utc)
        hour_key = now.strftime("%Y-%m-%d %H:00")
        cls._token_trend[hour_key] = cls._token_trend.get(hour_key, 0) + tokens

        cutoff = now - timedelta(hours=24)
        outdated_keys = [
            key for key in cls._token_trend
            # 将存储键解析为 UTC aware 时间以避免时区比较错误
            if datetime.strptime(key, "%Y-%m-%d %H:00").replace(tzinfo=timezone.utc) < cutoff
        ]
        for key in outdated_keys:
            del cls._token_trend[key]

    @classmethod
    def get_token_trend(cls) -> TokenTrendStats:
        """返回最近 24 小时的 token 趋势统计。"""
        cls._ensure_instance()
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)

        trend_points = []
        total_tokens = 0

        for offset in range(23, -1, -1):
            hour_dt = now - timedelta(hours=offset)
            hour_key = hour_dt.strftime("%Y-%m-%d %H:00")
            tokens = cls._token_trend.get(hour_key, 0)
            total_tokens += tokens
            trend_points.append(
                TokenTrendPoint(
                    hour=hour_dt.strftime("%H:00"),
                    tokens=tokens,
                    timestamp=hour_dt,
                )
            )

        return TokenTrendStats(
            trend=trend_points,
            total_tokens=total_tokens,
            last_updated=now,
        )

    @classmethod
    def reset_stats(cls) -> None:
        """重置全部统计计数。"""
        cls._stats = MessageStats(
            total_received=0,
            total_sent=0,
            messages_per_type={},
            last_reset_at=datetime.now(timezone.utc),
        )
        cls._stats.messages_per_type = defaultdict(int)

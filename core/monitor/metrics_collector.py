"""监控指标收集器实现。"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict

from models.monitor import MessageStats, ConnectionStatus, TokenTrendStats, TokenTrendPoint


class MetricsCollector:
    """负责聚合消息统计与连接状态的实例化收集器。"""

    def __init__(self) -> None:
        self._stats: MessageStats
        self._connection_status: ConnectionStatus
        self._token_trend: Dict[str, int]
        self.reset_stats()
        self._connection_status = ConnectionStatus()
        self._token_trend = {}

    def _ensure_messages_dict(self) -> None:
        """保证消息类型统计一直使用 defaultdict。"""
        if not isinstance(self._stats.messages_per_type, defaultdict):
            existing: Dict[str, int] = dict(self._stats.messages_per_type or {})
            self._stats.messages_per_type = defaultdict(int, existing)

    def record_message_received(self, message_type: str) -> None:
        """记录接收到的消息数量。"""
        self._stats.total_received += 1
        self._ensure_messages_dict()
        messages_per_type: Dict[str, int] = self._stats.messages_per_type
        messages_per_type[message_type] += 1

    def record_message_sent(self, message_type: str) -> None:
        """记录发送出去的消息数量。"""
        self._stats.total_sent += 1
        self._ensure_messages_dict()
        messages_per_type: Dict[str, int] = self._stats.messages_per_type
        messages_per_type[message_type] += 1

    def set_mod_connected(self, client_id: str) -> None:
        """更新模组连接状态。"""
        self._connection_status.mod_client_id = client_id
        self._connection_status.mod_connected_at = datetime.now(timezone.utc)

    def set_mod_disconnected(self) -> None:
        """标记模组断开连接。"""
        self._connection_status.mod_client_id = None
        self._connection_status.mod_connected_at = None

    def update_mod_last_message(self) -> None:
        """刷新模组最近一次消息时间。"""
        self._connection_status.mod_last_message_at = datetime.now(timezone.utc)

    def set_llm_status(self, provider: str, ready: bool) -> None:
        """设置当前 LLM 连接状态。"""
        self._connection_status.llm_provider = provider
        self._connection_status.llm_ready = ready

    def get_stats(self) -> MessageStats:
        """返回当前消息统计信息。"""
        return self._stats

    def get_connection_status(self) -> ConnectionStatus:
        """返回当前连接状态。"""
        return self._connection_status

    def record_token_usage(self, tokens: int) -> None:
        """记录 token 消耗，自动按当前小时聚合。"""
        now = datetime.now(timezone.utc)
        hour_key = now.strftime("%Y-%m-%d %H:00")
        self._token_trend[hour_key] = self._token_trend.get(hour_key, 0) + tokens

        cutoff = now - timedelta(hours=24)
        outdated_keys = [
            key
            for key in list(self._token_trend.keys())
            if datetime.strptime(key, "%Y-%m-%d %H:00").replace(tzinfo=timezone.utc) < cutoff
        ]
        for key in outdated_keys:
            del self._token_trend[key]

    def get_token_trend(self) -> TokenTrendStats:
        """返回最近 24 小时的 token 趋势统计。"""
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)

        trend_points = []
        total_tokens = 0

        for offset in range(23, -1, -1):
            hour_dt = now - timedelta(hours=offset)
            hour_key = hour_dt.strftime("%Y-%m-%d %H:00")
            tokens = self._token_trend.get(hour_key, 0)
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

    def reset_stats(self) -> None:
        """重置全部统计计数。"""
        self._stats = MessageStats(
            total_received=0,
            total_sent=0,
            messages_per_type={},
            last_reset_at=datetime.now(timezone.utc),
        )
        self._stats.messages_per_type = defaultdict(int)

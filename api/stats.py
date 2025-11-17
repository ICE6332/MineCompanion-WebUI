"""统计相关接口。"""

from fastapi import APIRouter

from core.monitor.metrics_collector import MetricsCollector
from models.monitor import TokenTrendStats

router = APIRouter()


@router.get("/token-trend", response_model=TokenTrendStats)
async def get_token_trend() -> TokenTrendStats:
    """获取最近 24 小时的 token 消耗趋势。"""
    # 直接通过监控采集器获取趋势数据，保持与后端统计逻辑一致
    return MetricsCollector.get_token_trend()


@router.post("/token-trend/test")
async def inject_test_tokens(tokens: int = 100) -> dict:
    """测试用：注入指定数量的 token 到当前小时统计。"""
    MetricsCollector.record_token_usage(tokens)
    return {
        "status": "ok",
        "tokens_added": tokens,
        "message": f"已添加 {tokens} tokens 到当前小时统计",
    }

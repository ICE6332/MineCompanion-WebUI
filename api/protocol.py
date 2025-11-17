"""紧凑 JSON 协议解析与压缩工具。

该模块提供 `CompactProtocol`，用于在“紧凑格式(短字段)”与“内部标准格式(长字段)”之间转换，
并保持向后兼容：同时支持旧版包含 `data` 字段的标准消息结构。
"""

from typing import Any, Dict


class CompactProtocol:
    """紧凑协议编解码器。

    - parse: 将紧凑格式/旧版标准格式解析为内部标准格式（展字段名与类型）。
    - compact: 将内部标准格式压缩为紧凑格式（短字段名与短类型）。
    """

    # 字段映射表（短 → 长）
    SHORT_TO_LONG: Dict[str, str] = {
        "i": "id",
        "t": "type",
        "ts": "timestamp",
        "p": "playerName",
        "c": "companionName",
        "m": "message",
        "a": "action",
        "pos": "position",
        "hp": "health",
    }

    # 类型映射表（短 → 长）
    TYPE_MAP: Dict[str, str] = {
        "cr": "conversation_request",
        "cs": "conversation_response",
        "gs": "game_state_update",
        "ac": "action_command",
        "er": "error",
    }

    _LONG_TO_SHORT: Dict[str, str] = {v: k for k, v in SHORT_TO_LONG.items()}
    _TYPE_LONG_TO_SHORT: Dict[str, str] = {v: k for k, v in TYPE_MAP.items()}

    @classmethod
    def _expand_type(cls, value: Any) -> Any:
        """将类型值从短码展开为长字符串；若已为长字符串则原样返回。"""
        if isinstance(value, str) and value in cls.TYPE_MAP:
            return cls.TYPE_MAP[value]
        return value

    @classmethod
    def _compact_type(cls, value: Any) -> Any:
        """将类型值从长字符串压缩为短码；若无对应短码则原样返回。"""
        if isinstance(value, str) and value in cls._TYPE_LONG_TO_SHORT:
            return cls._TYPE_LONG_TO_SHORT[value]
        return value

    @classmethod
    def parse(cls, compact_msg: Dict[str, Any]) -> Dict[str, Any]:
        """紧凑格式 → 内部标准格式。

        兼容输入：
        - 紧凑格式（短字段：如 `t`, `m` 等）；
        - 新标准格式（长字段：如 `type`, `message` 等）；
        - 旧版标准格式（顶层包含 `data`，内部键名如 `player_name`, `player`）。

        返回：展开后的标准格式字典（顶层长字段，无 `data` 嵌套）。
        """
        if not isinstance(compact_msg, dict):
            raise ValueError("parse 期望 dict 输入")

        # 先浅拷贝，避免副作用
        src: Dict[str, Any] = dict(compact_msg)
        result: Dict[str, Any] = {}

        # 1) 处理紧凑键名映射与已是长键名的回填
        for key, value in src.items():
            if key in cls.SHORT_TO_LONG:
                long_key = cls.SHORT_TO_LONG[key]
                # 展开类型字段
                if long_key == "type":
                    result[long_key] = cls._expand_type(value)
                else:
                    result[long_key] = value
            elif key == "type":
                result["type"] = cls._expand_type(value)
            elif key != "data":
                # 直接透传其他长键或非 data 字段
                result[key] = value

        # 2) 处理旧版带 data 的结构（向后兼容）
        if isinstance(src.get("data"), dict):
            data_obj: Dict[str, Any] = src["data"]
            # 兼容不同命名：player_name / player / playerName → playerName
            if "playerName" in data_obj:
                result["playerName"] = data_obj.get("playerName")
            elif "player_name" in data_obj:
                result["playerName"] = data_obj.get("player_name")
            elif "player" in data_obj:
                result["playerName"] = data_obj.get("player")

            # message / msg → message
            if "message" in data_obj:
                result["message"] = data_obj.get("message")
            elif "msg" in data_obj:
                result["message"] = data_obj.get("msg")

            # companionName / companion / companion_name → companionName
            if "companionName" in data_obj:
                result["companionName"] = data_obj.get("companionName")
            elif "companion_name" in data_obj:
                result["companionName"] = data_obj.get("companion_name")
            elif "companion" in data_obj:
                result["companionName"] = data_obj.get("companion")

            # 其他常见字段
            if "action" in data_obj:
                result["action"] = data_obj.get("action")
            if "position" in data_obj:
                result["position"] = data_obj.get("position")
            if "hp" in data_obj and "health" not in data_obj:
                result["health"] = data_obj.get("hp")
            elif "health" in data_obj:
                result["health"] = data_obj.get("health")

        # 3) 最终兜底：确保 type 字段为长字符串（若存在）
        if "type" in result:
            result["type"] = cls._expand_type(result["type"])  # 再次保证

        return result

    @classmethod
    def compact(cls, standard_msg: Dict[str, Any]) -> Dict[str, Any]:
        """内部标准格式 → 紧凑格式。

        要求输入为“顶层长字段，无 data 嵌套”的标准结构；
        未知字段将原样透传。
        """
        if not isinstance(standard_msg, dict):
            raise ValueError("compact 期望 dict 输入")

        dest: Dict[str, Any] = {}
        for key, value in standard_msg.items():
            if key == "type":
                dest_key = cls._LONG_TO_SHORT.get(key, key)
                dest[dest_key] = cls._compact_type(value)
                continue

            short_key = cls._LONG_TO_SHORT.get(key)
            if short_key is not None:
                dest[short_key] = value
            else:
                # 未知字段：保持原名避免数据丢失
                dest[key] = value

        return dest

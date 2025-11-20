"""消息处理器注册表。"""

from api.handlers.connection import ConnectionInitHandler
from api.handlers.game_state import GameStateHandler
from api.handlers.conversation import ConversationHandler

MESSAGE_HANDLERS = {
    "connection_init": ConnectionInitHandler(),
    "game_state_update": GameStateHandler(),
    "conversation_request": ConversationHandler(),
}


def get_handler(message_type: str):
    """根据消息类型获取处理器。"""
    return MESSAGE_HANDLERS.get(message_type)

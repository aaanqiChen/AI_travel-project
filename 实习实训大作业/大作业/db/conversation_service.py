from typing import Optional, List, Dict
from .conversation_dao import ConversationDAO
from .message_dao import MessageDAO

class ConversationService:
    """会话业务逻辑服务，处理会话创建、消息交互等核心流程"""

    @staticmethod
    def create_new_conversation(
        user_id: int,
        model_name: str,
        initial_user_msg: Optional[str] = None
    ) -> Optional[Dict]:
        conv_id = ConversationDAO.create_conversation(
            user_id=user_id,
            model_name=model_name
        )
        if not conv_id:
            return None
        if initial_user_msg:
            MessageDAO.save_message(
                conversation_id=conv_id,
                user_id=user_id,
                message_type="user",
                content=initial_user_msg
            )
            short_title = initial_user_msg[:20] + ("..." if len(initial_user_msg) > 20 else "")
            ConversationDAO.update_conversation_title(conv_id, user_id, short_title)
        return ConversationDAO.get_conversation_by_id(conv_id, user_id)

    @staticmethod
    def get_user_conversation_list(user_id: int) -> List[Dict]:
        conversations = ConversationDAO.get_user_conversations(user_id)
        for conv in conversations:
            latest_msg = MessageDAO.get_latest_message(conv["conversation_id"])
            conv["latest_msg_preview"] = latest_msg["content"][:30] + "..." if latest_msg else "无消息"
            conv["latest_time"] = latest_msg["created_at"] if latest_msg else conv["created_at"]
        return conversations

conversation_service = ConversationService()

from typing import Optional, List, Dict
from db.database import db

class ConversationDAO:
    """会话数据访问对象，封装conversations表操作"""

    @staticmethod
    def create_conversation(
        user_id: int,
        model_name: str,
        title: str = "新对话"
    ) -> Optional[int]:
        try:
            db.execute(
                "UPDATE conversations SET is_active = 0 WHERE user_id = %s AND is_active = 1",
                (user_id,)
            )
            db.execute(
                """INSERT INTO conversations 
                   (user_id, title, model_name, is_active) 
                   VALUES (%s, %s, %s, 1)""",
                (user_id, title, model_name)
            )
            return db.fetchone("SELECT LAST_INSERT_ID() AS conversation_id")['conversation_id']
        except Exception as e:
            print(f"创建会话失败: {str(e)}")
            return None

    @staticmethod
    def get_user_conversations(user_id: int) -> List[Dict]:
        try:
            return db.fetchall(
                """SELECT conversation_id, title, model_name, is_active, 
                          created_at, updated_at 
                   FROM conversations 
                   WHERE user_id = %s 
                   ORDER BY updated_at DESC""",
                (user_id,)
            )
        except Exception as e:
            print(f"查询用户会话失败: {str(e)}")
            return []

    @staticmethod
    def get_conversation_by_id(conversation_id: int, user_id: int) -> Optional[Dict]:
        try:
            return db.fetchone(
                """SELECT conversation_id, user_id, title, model_name, is_active, created_at, updated_at, metadata 
                   FROM conversations WHERE conversation_id = %s AND user_id = %s""",
                (conversation_id, user_id)
            )
        except Exception as e:
            print(f"查询会话失败: {str(e)}")
            return None

    @staticmethod
    def update_conversation_title(conversation_id: int, user_id: int, title: str) -> bool:
        try:
            rows_affected = db.execute(
                "UPDATE conversations SET title = %s, updated_at = NOW() WHERE conversation_id = %s AND user_id = %s",
                (title, conversation_id, user_id)
            )
            return rows_affected > 0
        except Exception as e:
            print(f"更新会话标题失败: {str(e)}")
            return False

conversation_dao = ConversationDAO()

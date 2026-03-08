from typing import Optional, Dict, List
from db.database import db

class MessageDAO:
    """消息数据访问对象，封装conversation_messages表操作"""

    @staticmethod
    def save_message(
        conversation_id: int,
        user_id: int,
        message_type: str,
        content: str,
        langgraph_state: Optional[dict] = None,
        tokens: Optional[int] = None,
        sequence: Optional[int] = None,
        metadata: Optional[dict] = None
    ) -> Optional[int]:
        sql = """
        INSERT INTO conversation_messages (
            conversation_id, user_id, message_type, content, langgraph_state, tokens, sequence, metadata
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            conversation_id, user_id, message_type, content,
            langgraph_state, tokens, sequence, metadata
        )
        try:
            with db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                message_id = cursor.lastrowid
                conn.commit()
                cursor.close()
                return message_id
        except Exception as e:
            print(f"保存消息失败: {str(e)}")
            return None

    @staticmethod
    def get_latest_message(conversation_id: int) -> Optional[Dict]:
        sql = """
        SELECT * FROM conversation_messages
        WHERE conversation_id = %s
        ORDER BY sequence DESC, created_at DESC
        LIMIT 1
        """
        try:
            return db.fetchone(sql, (conversation_id,))
        except Exception as e:
            print(f"查询最新消息失败: {str(e)}")
            return None

    @staticmethod
    def get_conversation_messages(conversation_id: int) -> List[Dict]:
        """获取会话的所有消息"""
        sql = """
        SELECT message_id, conversation_id, user_id, message_type, content, 
               langgraph_state, tokens, created_at, sequence, metadata
        FROM conversation_messages
        WHERE conversation_id = %s
        ORDER BY sequence ASC, created_at ASC
        """
        try:
            return db.fetchall(sql, (conversation_id,))
        except Exception as e:
            print(f"查询会话消息失败: {str(e)}")
            return []

    @staticmethod
    def get_message_by_id(message_id: int) -> Optional[Dict]:
        """根据消息ID获取消息"""
        sql = """
        SELECT * FROM conversation_messages
        WHERE message_id = %s
        """
        try:
            return db.fetchone(sql, (message_id,))
        except Exception as e:
            print(f"查询消息失败: {str(e)}")
            return None

    @staticmethod
    def update_message_posters(message_id: int, posters: str) -> bool:
        sql = """
        UPDATE conversation_messages SET posters = %s WHERE message_id = %s
        """
        try:
            with db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (posters, message_id))
                conn.commit()
                cursor.close()
                return True
        except Exception as e:
            print(f"更新消息海报失败: {str(e)}")
            return False

    @staticmethod
    def get_conversation_posters(conversation_id: int) -> list:
        sql = """
        SELECT posters FROM conversation_messages WHERE conversation_id = %s AND posters IS NOT NULL AND posters != ''
        """
        try:
            results = db.fetchall(sql, (conversation_id,))
            posters = []
            for row in results:
                if row['posters']:
                    posters.extend(eval(row['posters']))  # posters字段为JSON字符串
            return posters
        except Exception as e:
            print(f"获取会话海报失败: {str(e)}")
            return []

message_dao = MessageDAO()

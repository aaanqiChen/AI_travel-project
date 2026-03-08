from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime


class ChatMessage(BaseModel):
    """聊天消息单元"""
    role: str = Field(..., description="角色，只能是'user'或'assistant'")
    content: str = Field(..., description="消息内容")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="消息时间戳，ISO格式"
    )


class ChatHistory(BaseModel):
    """聊天历史记录"""
    thread_id: str = Field(..., description="会话线程ID，与行程规划共享")
    messages: List[ChatMessage] = Field(default_factory=list, description="消息列表")
    last_updated: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="最后更新时间"
    )

    def add_message(self, message: ChatMessage):
        """添加消息并更新时间戳"""
        self.messages.append(message)
        self.last_updated = datetime.now().isoformat()

    def get_recent_messages(self, limit: int = 10) -> List[ChatMessage]:
        """获取最近N条消息，避免历史过长"""
        return self.messages[-limit:]
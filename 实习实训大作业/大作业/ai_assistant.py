#!/usr/bin/env python3
"""
AI助手管理类
用于管理AI实例，避免重复创建
"""

import threading
from typing import Dict, Optional
from test_planner import TravelAssistant

class AIAssistantManager:
    """AI助手管理器"""
    
    def __init__(self):
        self._assistants: Dict[str, TravelAssistant] = {}
        self._lock = threading.Lock()
    
    def get_assistant(self, user_id: int, conversation_id: int) -> TravelAssistant:
        """获取或创建AI助手实例"""
        key = f"{user_id}_{conversation_id}"
        
        with self._lock:
            if key not in self._assistants:
                # 创建新的AI助手实例
                self._assistants[key] = TravelAssistant(
                    user=f"user_{user_id}", 
                    session=f"session_{conversation_id}"
                )
            
            return self._assistants[key]
    
    def remove_assistant(self, user_id: int, conversation_id: int):
        """移除AI助手实例"""
        key = f"{user_id}_{conversation_id}"
        
        with self._lock:
            if key in self._assistants:
                del self._assistants[key]
    
    def clear_all(self):
        """清空所有AI助手实例"""
        with self._lock:
            self._assistants.clear()

    # 新增：暴露TravelAssistant实例，便于调用smart_reply
    def get_travel_assistant(self, user_id: int, conversation_id: int):
        return self.get_assistant(user_id, conversation_id)

# 全局AI助手管理器实例
ai_manager = AIAssistantManager() 
import logging
from typing import List, Dict, Optional, Callable  # 新增Callable类型
from datetime import datetime

from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.chains import LLMChain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from models.chat_model import ChatMessage, ChatHistory
from models.request_model import TravelPlanRequest


class QwenChatPlanner:
    """基于Qwen-Max的聊天模型，支持流式输出暂停"""

    def __init__(self, user: str, session: str):
        self.user = user
        self.session = session
        self.thread_id = f"{user}_{session}"
        self.reset()

    def reset(self):
        """重置聊天状态"""
        self.chat_llm = ChatTongyi(model_name="qwen-max", streaming=True)
        self.history = ChatHistory(thread_id=self.thread_id)
        self.config = {"configurable": {"thread_id": self.thread_id}}

    def _build_chat_system_prompt(self) -> str:
        """构建聊天模式的系统提示词"""
        return """
        你是一个友好、智能的旅行助手，既可以闲聊也能提供旅行相关建议。
        核心能力：
        1. 旅行知识：景点背景、当地文化、美食推荐、交通贴士
        2. 闲聊互动：自然对话、幽默回应、情感共鸣
        3. 上下文关联：记住用户提到的旅行计划、偏好和历史对话

        聊天规则：
        - 当用户讨论旅行相关话题时，主动关联之前的行程规划（如果有）
        - 避免使用专业术语，用口语化表达
        - 回答简洁明了，根据用户输入长度调整回复篇幅
        - 若用户问行程规划相关问题，可引导使用行程规划功能（但不强制）
        """

    def generate_response(self, user_input: str, pause_checker: Optional[Callable[[], bool]] = None) -> str:
        """生成聊天回复（支持暂停检查）
        :param pause_checker: 检查暂停的函数，返回True则停止输出
        """
        try:
            # 1. 添加用户消息到历史记录
            user_msg = ChatMessage(role="user", content=user_input)
            self.history.add_message(user_msg)

            # 2. 构建聊天提示
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=self._build_chat_system_prompt()),
                MessagesPlaceholder(variable_name="history"),
                HumanMessage(content=user_input)
            ])

            # 3. 转换历史记录为LangChain消息格式
            langchain_history = [
                HumanMessage(content=msg.content) if msg.role == "user"
                else AIMessage(content=msg.content)
                for msg in self.history.get_recent_messages()
            ]

            # 4. 构建流式调用的输入
            chain_input = {"history": langchain_history}

            # 5. 流式调用LLM链（支持暂停检查）
            full_reply = ""
            for chunk in self.chat_llm.stream(
                    prompt.format_prompt(**chain_input).to_messages(),
                    config=self.config, streaming=True
            ):
                # 检查暂停信号（如果提供了检查函数）
                if pause_checker and pause_checker():
                    print("\n[已暂停输出]", end='', flush=True)
                    full_reply += "\n[已暂停输出]"
                    break  # 中断流式生成

                if isinstance(chunk, AIMessage):
                    print(chunk.content, end="", flush=True)
                    full_reply += chunk.content

            print()  # 输出完毕后换行
            # 6. 保存完整回复到历史记录
            assistant_msg = ChatMessage(role="assistant", content=full_reply)
            self.history.add_message(assistant_msg)

            return full_reply

        except Exception as e:
            logging.error(f"聊天回复生成失败: {str(e)}")
            import traceback
            logging.debug(traceback.format_exc())
            print("\n助手: 抱歉，刚才没听清，可以再讲一遍吗？")
            return "抱歉，刚才没听清，可以再讲一遍吗？"

    def generate_response_stream(self, user_input: str, pause_checker: Optional[Callable[[], bool]] = None):
        """流式生成聊天回复，每次yield一段内容"""
        try:
            user_msg = ChatMessage(role="user", content=user_input)
            self.history.add_message(user_msg)
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=self._build_chat_system_prompt()),
                MessagesPlaceholder(variable_name="history"),
                HumanMessage(content=user_input)
            ])
            langchain_history = [
                HumanMessage(content=msg.content) if msg.role == "user"
                else AIMessage(content=msg.content)
                for msg in self.history.get_recent_messages()
            ]
            chain_input = {"history": langchain_history}
            full_reply = ""
            for chunk in self.chat_llm.stream(
                    prompt.format_prompt(**chain_input).to_messages(),
                    config=self.config, streaming=True
            ):
                if pause_checker and pause_checker():
                    yield "\n[已暂停输出]"
                    break
                if isinstance(chunk, AIMessage):
                    yield chunk.content
                    full_reply += chunk.content
            assistant_msg = ChatMessage(role="assistant", content=full_reply)
            self.history.add_message(assistant_msg)
        except Exception as e:
            yield "抱歉，刚才没听清，可以再讲一遍吗？"

    def get_chat_history(self) -> List[Dict]:
        """获取格式化的聊天历史（与行程规划器兼容）"""
        return [
            {"role": msg.role, "content": msg.content, "timestamp": msg.timestamp}
            for msg in self.history.messages
        ]

    def clear_chat_history(self):
        """清空聊天历史（与行程规划器同步）"""
        self.history = ChatHistory(thread_id=self.thread_id)
        logging.info(f"已清空会话 {self.thread_id} 的聊天历史")
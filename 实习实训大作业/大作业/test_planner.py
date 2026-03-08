import logging
import re
from typing import List, Dict, Optional
from models.trip_plan_model import TravelPlanResponse
from planner.planner import QwenTravelPlanner
from models.request_model import TravelPlanRequest
from planner.chat_planner import QwenChatPlanner
from models.chat_model import ChatMessage
from enum import Enum, auto

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("TravelAssistant")


class ConversationMode(Enum):
    """对话模式枚举"""
    CHAT = auto()
    TRIP_PLANNING = auto()
    UNKNOWN = auto()


class TravelAssistant:
    """整合行程规划与聊天功能的助手（改进版）"""

    def __init__(self, user: str = "default_user", session: str = "default_session"):
        self.user = user
        self.session = session
        self.trip_planner = QwenTravelPlanner(user=user, session=session)
        self.chat_planner = QwenChatPlanner(user=user, session=session)
        self.logger = logger
        self.conversation_mode = ConversationMode.UNKNOWN
        self.conversation_history = []  # 记录对话历史
        self.trip_keywords = {
            # 关键词: 权重
            "规划": 2, "行程": 2, "旅游": 2, "旅行": 2, "攻略": 2,
            "景点": 1, "酒店": 1, "天数": 1, "日期": 1, "预算": 1,
            "路线": 1, "安排": 1, "行程表": 2, "想去": 1, "推荐": 1,
            "计划": 2, "行程": 2, "目的地": 1, "机票": 1, "住宿": 1
        }
        self.chat_keywords = {
            "你好": 2, "嗨": 2, "问候": 2, "聊天": 2, "对话": 1,
            "天气": 1, "时间": 1, "日期": 1, "帮助": 2, "介绍": 1
        }
        self.negative_words = ["不", "不想", "不要", "别", "拒绝", "无需"]

    def _calculate_intent_score(self, text: str, keyword_weights: Dict[str, int]) -> float:
        """计算意图匹配分数"""
        score = 0
        text_lower = text.lower()

        # 关键词匹配
        for keyword, weight in keyword_weights.items():
            if keyword in text_lower:
                score += weight

        # 正则模式匹配（行程规划相关）
        trip_patterns = [
            r".*几[天|日].*[去|玩].*",
            r".*[计划|准备].*[旅行|旅游].*",
            r".*[推荐|介绍].*[景点|地方].*",
            r".*[怎么|如何].*安排.*行程.*",
            r".*[想去|打算].*[哪里|什么地方].*"
        ]

        if keyword_weights == self.trip_keywords:
            for pattern in trip_patterns:
                if re.search(pattern, text_lower):
                    score += 2

        return score

    def _contains_negative_word(self, text: str) -> bool:
        """检查是否包含否定词"""
        return any(neg_word in text for neg_word in self.negative_words)

    def _determine_conversation_mode(self, user_input: str) -> ConversationMode:
        # 检查明确的模式切换指令
        if any(cmd in user_input for cmd in ["切换行程模式", "开始规划", "旅行模式"]):
            return ConversationMode.TRIP_PLANNING
        if any(cmd in user_input for cmd in ["切换聊天模式", "闲聊模式", "聊天模式"]):
            return ConversationMode.CHAT

        # 检查否定词（避免误判）
        if self._contains_negative_word(user_input):
            return ConversationMode.CHAT

        # 检查是否是询问之前提到的信息（应该用聊天模式）
        if self._is_asking_about_previous_info(user_input):
            return ConversationMode.CHAT

        # 明确的“目的地+天数/日期/预算/计划/安排/帮我规划”组合才判为行程规划
        # 例如“我想去北京玩1天”，“帮我规划去上海的行程”
        import re
        if re.search(r'(去|玩|旅游|旅行|行程|规划|安排).{0,10}(北京|上海|广州|[a-zA-Z]+市|[a-zA-Z]+县|[a-zA-Z]+区)', user_input) and \
           re.search(r'(天|日|日期|预算|计划|安排|帮我规划)', user_input):
            return ConversationMode.TRIP_PLANNING

        # 仅有“几天”、“X天”、“X日”也判为行程规划
        if re.search(r'(\d+天|\d+日|几天|几日)', user_input):
            return ConversationMode.TRIP_PLANNING

        # 仅有“如何安排行程”、“我想去哪里玩”、“北京好玩吗”等泛问句，判为聊天
        return ConversationMode.CHAT

    def _is_asking_about_previous_info(self, user_input: str) -> bool:
        """检查用户是否在询问之前提到的信息"""
        # 询问模式的关键词
        asking_patterns = [
            r"我想去哪里",
            r"我要去哪里",
            r"我去哪里",
            r"目的地是哪里",
            r"去哪里",
            r"什么[地方|城市]",
            r"哪个[地方|城市]",
            r"哪里",
            r"什么时候",
            r"什么时间",
            r"几天",
            r"多少天",
            r"玩几天",
            r"待几天"
        ]
        
        import re
        for pattern in asking_patterns:
            if re.search(pattern, user_input):
                return True
        
        return False

    def _update_conversation_history(self, user_input: str, response: str):
        """更新对话历史"""
        self.conversation_history.append({"user": user_input, "assistant": response})
        if len(self.conversation_history) > 5:  # 保留最近5轮对话
            self.conversation_history.pop(0)

    def _get_recent_context(self) -> str:
        """获取最近对话上下文"""
        return "\n".join(
            f"用户: {item['user']}\n助手: {item['assistant']}"
            for item in self.conversation_history[-3:]
        )

    def smart_reply(self, user_input: str) -> str:
        """智能判断并调用对应planner/chat_planner"""
        mode = self._determine_conversation_mode(user_input)
        if mode == ConversationMode.TRIP_PLANNING:
            self.logger.info("调用行程规划器...")
            response = self.trip_planner.generate_plan(user_input)
            return response if isinstance(response, str) else str(response)
        else:
            self.logger.info("调用聊天模型...")
            return self.chat_planner.generate_response(user_input)

    def smart_reply_stream(self, user_input: str):
        """流式智能判断并调用对应planner/chat_planner"""
        mode = self._determine_conversation_mode(user_input)
        if mode == ConversationMode.TRIP_PLANNING:
            self.logger.info("调用行程规划器(流式)...")
            yield from self.trip_planner.generate_plan_stream(user_input)
        else:
            self.logger.info("调用聊天模型(流式)...")
            yield from self.chat_planner.generate_response_stream(user_input)

    def run(self):
        """启动交互循环"""
        self.logger.info("旅行助手已启动")
        print("欢迎使用旅行助手！输入'退出'结束对话，输入'清空记忆'重置对话历史\n")
        print("提示：你可以说'开始规划行程'进入旅行规划模式，或'切换聊天模式'返回普通聊天")

        while True:
            try:
                user_input = input("你: ").strip()

                # 处理系统指令
                if user_input == "退出":
                    print("助手: 再见！祝你旅途愉快～")
                    break

                if user_input == "清空记忆":
                    self.trip_planner.clear_conversation_history()
                    self.chat_planner.clear_chat_history()  # 使用clear_chat_history而不是reset
                    self.conversation_mode = ConversationMode.UNKNOWN
                    self.conversation_history = []
                    print("助手: 已清空对话历史，我们可以重新开始～")
                    continue

                if not user_input:
                    print("助手: 请输入内容哦～")
                    continue

                # 确定对话模式
                new_mode = self._determine_conversation_mode(user_input)
                if new_mode != self.conversation_mode:
                    self.logger.info(f"对话模式切换: {self.conversation_mode} -> {new_mode}")
                    self.conversation_mode = new_mode

                # 根据模式处理请求
                print("助手: ", end="", flush=True)

                if self.conversation_mode == ConversationMode.TRIP_PLANNING:
                    self.logger.info("调用行程规划器...")
                    response = self.trip_planner.generate_plan(user_input)
                    
                    # 如果响应包含计划信息，更新聊天模块
                    if hasattr(response, 'plan_info') and response.plan_info:
                        self.chat_planner.update_travel_plan_info(response.plan_info)
                        self.logger.info(f"已更新聊天模块的旅行计划信息: {response.plan_info}")
                    
                    print(f"\n(当前处于行程规划模式，如需切换可输入'切换聊天模式')")
                else:
                    self.logger.info("调用聊天模型...")
                    response = self.chat_planner.generate_response(user_input)

                # 更新对话历史
                self._update_conversation_history(user_input, response.content if hasattr(response, 'content') else response)
                print()  # 每条回复结束后换行

            except Exception as e:
                self.logger.error(f"处理请求失败: {str(e)}", exc_info=True)
                print("\n助手: 抱歉，处理时出错了，请再试一次～\n")
                self.conversation_mode = ConversationMode.UNKNOWN  # 出错时重置模式


if __name__ == "__main__":
    assistant = TravelAssistant(user="test_user", session="test_session_001")
    assistant.run()
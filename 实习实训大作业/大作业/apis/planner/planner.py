# import datetime
# import json
# import logging
# from typing import Dict, List, Optional, Any, TypedDict, Sequence
# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langgraph.prebuilt import create_react_agent
# from langchain.chains import LLMChain
# from langchain_community.chat_models.tongyi import ChatTongyi
# from langgraph.checkpoint.memory import MemorySaver
# from langgraph.graph import START, MessagesState, StateGraph, END, add_messages
# from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
# from typing_extensions import Annotated
# from models.request_model import TravelPlanRequest
# from models.trip_plan_model import TravelPlanResponse, Activity, DayPlan
# from tools import ALL_TOOLS  # 所有工具集合
#
# import sys
# import os
#
# sys.path.append(os.path.abspath(os.path.dirname(__file__)))  # 加入 test_planner.py 所在目录
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))  # 加入项目根目录
# # 配置日志
# logger = logging.getLogger(__name__)
#
#
# class State(TypedDict):
#     messages: Annotated[Sequence[BaseMessage], add_messages]
#     request: Optional[TravelPlanRequest]
#
#
# class QwenTravelPlanner:
#     """基于 Qwen-Max 模型的行程规划器（使用 LangGraph 实现消息持久化）"""
#
#     # 1.创建agent调用工具进行输入输出
#     # 2.创建结构化输出，用于提取，辅助agent
#     def __init__(self, user: str, session: str):
#         self.user = user
#         self.session = session
#         self.reset()
#
#     def reset(self):
#         # 初始化 Qwen-Max 模型
#         self.chat_llm = ChatTongyi(model_name='qwen-max', streaming=True)
#
#         # 创建检查点存储器
#         self.checkpointer = MemorySaver()
#
#         # 对用户输入的文本进行提取，然后结构化输出
#         self.struct_request_llm = self.chat_llm.with_structured_output(TravelPlanRequest)
#
#         # 使用agent根据API搜索的消息进行整合
#         self.agent = create_react_agent(self.chat_llm, ALL_TOOLS, checkpointer=self.checkpointer)
#
#         # 对大模型响应的内容进行结构化
#         self.struct_response_llm = self.chat_llm.with_structured_output(TravelPlanResponse)
#
#         # 定义工作流的应用程序
#         self.app = self._build_graph()
#
#         # 定义会话线程id
#         self.config = {'configurable': {'thread_id': self.user + '_' + self.session}}
#
#     def _build_system_prompt(self) -> str:
#         """构建更专业规范的系统提示词"""
#         return """
#         你是一位专业的智能旅行规划助手，具备整合天气、地图、POI、预算等多种信息资源的能力。
#
#         你的任务是根据用户提供的出行需求，生成**准确、实用且富有创意的旅行行程方案**。你拥有以下功能工具支持：
#         1. 地图查询：定位地点；
#         2. 天气预报：提供每日报告并建议穿衣；
#         3. POI 检索：搜索景点、酒店、餐饮、计算路线和交通时间等，并提供评分、地址、营业时间；
#         4. 预算估算：根据消费水平计算大致费用。
#
#         ### 输出要求：
#         - 提供**3 套行程方案**，风格不同（如文化体验、美食购物、自然探索等）；
#         - 每套方案包含：
#           - 目的地、出发和结束日期；
#           - 每日活动安排（含时间、地点、活动描述）；
#           - 每天住宿推荐（含评分和价格范围）；
#           - 天气提示与穿衣建议；
#           - 总体费用估算（按预算级别）；
#           - 可能注意事项与安全建议；
#         - 如天气不佳，自动提供备选活动；
#         - 对高人流景点应提供避开建议或预约提示。
#
#         ### 输出格式：
#           1. 目的地：精确到城市或区域
#           2. 日期范围：格式YYYY-MM-DD
#           3. 每日安排：
#               a) 时间分配需合理，避免行程过于紧张
#               b) 各项活动包含详细定位信息
#               c) 住宿酒店包含评分和价格区间
#               d) 交通方式明确具体类型和路线
#           4. 天气信息：展示对应时段的精确预报；并且根据当天的温度建议用户穿什么衣服；如果会下雨的话要提醒用户带伞
#           5. 费用预估：按用户级别提供不同精确度的预算
#           6. 注意事项：包含安全提醒和特殊提示
#           7. 地图可视化：提供可在前端展示的交互式路线图
#
#         ### 工作原则：
#         - 精准理解用户输入，自动补足缺失信息（如默认出发日期为今天）；
#         - 在有限预算下最大化旅行体验；
#         - 活动分布合理，不宜过于紧凑或重复；
#         - 保证每日活动不超过 3~5 个，适量休息；
#         - 每日行程符合交通可达性，避免穿插无序。
#
#         请始终保证内容专业、真实、清晰。
#
#         ### 格式约束：
#         - 初始输出必须是**纯自然语言描述**，禁止包含任何JSON、代码块或结构化标记（如`{}`、`[]`）。
#         - 工具调用的结果（如景点列表、天气数据）需转换为流畅的自然语言后呈现。
#         - 结构化JSON仅在后续专用转换步骤中生成，初始方案输出不涉及。
#         """
#
#     def _build_user_prompt(self, request: TravelPlanRequest) -> str:
#         """构建用户输入摘要提示，包含默认日期推理逻辑"""
#         # 判断 start_date 和 end_date 是否缺失或为空
#         today = datetime.datetime.now()
#         start_date = request.start_date.strip() if request.start_date else ""
#         end_date = request.end_date.strip() if request.end_date else ""
#
#         # 以今天为默认出发日期
#         if not start_date or start_date.lower() in ["unknown", "未知", ""]:
#             start_date = today.strftime("%Y-%m-%d")
#
#         # 若结束日期为空，则使用 start + duration 天推算
#         if not end_date or end_date.lower() in ["unknown", "未知", ""]:
#             try:
#                 start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
#             except ValueError:
#                 start_dt = today  # fallback
#             end_dt = start_dt + datetime.timedelta(days=request.duration)
#             end_date = end_dt.strftime("%Y-%m-%d")
#
#         return f"""
#         以下是用户的出行需求，请基于此规划一个{request.duration}天的行程：
#
#         - 出发城市: {request.departure_city or "未知（可使用当前位置）"}
#         - 目的地: {request.destination}
#         - 出发日期: {start_date}
#         - 结束日期: {end_date}
#         - 出行天数: {request.duration} 天
#         - 人数: {request.travelers} 人
#         - 类型: {request.trip_type}
#         - 兴趣偏好: {request.interests or "无特别偏好"}
#         - 预算: {request.budget or "无预算限制"}
#         - 特殊需求: {request.special_requests or "无"}
#
#         请尽可能满足用户的兴趣和需求，并推荐合适的交通、住宿、活动和每日安排。
#         """
#
#     def _build_structured_prompt(self, plan_text: str) -> str:
#         return f"""
#            请将以下行程计划转换为结构化JSON格式：
#
#            ### 原始行程计划
#            {plan_text}
#
#            ### 结构化要求
#            请转换为以下JSON格式：
#            {{
#              "destination": "目的地",
#              "start_date": "开始日期",
#              "end_date": "结束日期",
#              "summary": "行程概述",
#              "days": [
#                {{
#                  "date": "YYYY-MM-DD",
#                  "weather": "天气信息",
#                  "activities": [
#                    {{
#                      "time": "时间段",
#                      "name": "活动名称",
#                      "location": "地点名称",
#                      "type": "活动类型",
#                      "description": "活动描述"
#                    }}
#                  ],
#                  "hotel": {{"name": "酒店名称", "address": "酒店地址"}}
#                }}
#              ],
#              "notes": ["建议1", "建议2"]
#            }}
#
#            请只输出JSON格式的内容，不要包含任何其他文本。
#            """
#
#     def handle_request(self, state: State):
#         last_message = state['messages'][-1].content if state['messages'] else ""
#         request = self.struct_request_llm.invoke(last_message, config=self.config)
#
#         # ✅ 修复 start_date 和 end_date
#         today = datetime.datetime.now()
#         try:
#             start_dt = datetime.datetime.strptime(request.start_date, "%Y-%m-%d")
#         except Exception:
#             start_dt = today
#             request.start_date = today.strftime("%Y-%m-%d")
#
#         try:
#             end_dt = datetime.datetime.strptime(request.end_date, "%Y-%m-%d")
#         except Exception:
#             end_dt = start_dt + datetime.timedelta(days=request.duration)
#             request.end_date = end_dt.strftime("%Y-%m-%d")
#
#         return {
#             'request': request,
#             'messages': []
#         }
#
#     def call_agent(self, state: State):
#         """处理请求并使用agent生成响应"""
#         request = state.get('request')
#         if not request:
#             logger.error("调用代理时请求对象不存在")
#             return {"messages": [AIMessage(content="无法处理请求，缺少必要参数")]}
#
#         try:
#             # 构建提示
#             user_msg1 = HumanMessage(content=self._build_system_prompt())
#             user_msg2 = HumanMessage(content=self._build_user_prompt(request))
#
#             # 获取历史消息
#             history = state.get("messages", [])
#             filtered_history = [msg for msg in history if not isinstance(msg, SystemMessage)]
#
#             # 构造完整对话（SystemMessage 必须第一个）
#             full_messages = [user_msg1] + filtered_history + [user_msg2]
#
#             # 构造 agent 输入
#             agent_input = {
#                 "input": "",  # 必须有这个字段
#                 "messages": full_messages
#             }
#             # print("调用 agent 之前的消息列表：")
#             # for i, msg in enumerate(full_messages):
#             #     print(f"{i}: {msg.__class__.__name__} | {msg.content}")
#
#             agent_output = self.agent.invoke(agent_input, config=self.config)
#
#             # 确保返回一个有效的消息对象
#             if isinstance(agent_output, dict) and "text" in agent_output:
#                 raw_text = agent_output["text"]
#                 # 简单判断是否为纯JSON，若是则尝试转换为自然语言
#                 if raw_text.strip().startswith("{") and raw_text.strip().endswith("}"):
#                     try:
#                         json_data = json.loads(raw_text)
#                         # 示例：将景点JSON转换为自然语言
#                         if "景点" in json_data:
#                             raw_text = "推荐景点：" + "、".join([x["名称"] for x in json_data["景点"]])
#                     except:
#                         pass
#                 response_message = AIMessage(content=raw_text)
#             elif isinstance(agent_output, BaseMessage):
#                 response_message = agent_output
#             else:
#                 response_message = AIMessage(content=str(agent_output))
#
#             # 将有效的消息对象添加到状态中
#             return {
#                 "messages": [response_message],
#                 "request": request  # 保留请求对象
#             }
#
#         except Exception as e:
#             logger.error(f"Agent调用失败: {str(e)}")
#             import traceback
#             logger.error(traceback.format_exc())
#             return {
#                 "messages": [AIMessage(content=f"行程规划出错: {str(e)}")],
#                 "request": request
#             }
#
#     def _build_graph(self):
#         workflow = StateGraph(state_schema=State)
#
#         workflow.add_edge(START, 'struct_request_llm')
#         workflow.add_edge('struct_request_llm', 'agent')
#         workflow.add_edge('agent', END)
#
#         workflow.add_node('struct_request_llm', self.handle_request)
#         workflow.add_node('agent', self.call_agent)
#
#         app = workflow.compile(checkpointer=self.checkpointer)
#         return app
#
#     def generate_plan(self, user_input: str):
#         """生成旅行计划"""
#         try:
#             initial_state = {"messages": [HumanMessage(content=user_input)], "request": None}
#             final_state = self.app.stream(initial_state, config=self.config, stream_mode='messages')
#
#             for chunk, metadata in final_state:
#                 content = chunk.content
#                 # 过滤纯JSON内容
#                 if content.strip().startswith("{") and content.strip().endswith("}"):
#                     try:
#                         json_data = json.loads(content)
#                         # 示例：将JSON转换为自然语言描述
#                         content = f"获取到信息：{json.dumps(json_data, ensure_ascii=False)[:100]}..."  # 简化展示
#                     except:
#                         content = "[过滤无效内容]"
#                 print(content, end='', flush=True)
#
#         except Exception as e:
#             logger.error(f"行程规划失败: {str(e)}")
#             raise
#
#     def generate_struct_plan(self, plan_text: str):
#         """生成结构化json消息"""
#         try:
#             # 确保输入是字符串
#             if not isinstance(plan_text, str):
#                 plan_text = str(plan_text)
#
#             prompt = self._build_structured_prompt(plan_text)
#             response = self.struct_response_llm.invoke(
#                 [HumanMessage(content=prompt)],  # 改为直接传入消息列表
#                 config=self.config
#             )
#             return response.model_dump_json()
#         except Exception as e:
#             logger.exception(f"结构化输出失败: {str(e)}")
#             return self._fallback_parse_plan(plan_text)  # 确保返回回退结果
#
#     def _fallback_parse_plan(self, plan_text: str) -> TravelPlanResponse:
#         """回退解析方法（当结构化解析失败时使用）"""
#         # 尝试从文本中提取JSON
#         try:
#             json_start = plan_text.find('{')
#             json_end = plan_text.rfind('}') + 1
#             if json_start != -1 and json_end != -1:
#                 json_str = plan_text[json_start:json_end]
#                 return TravelPlanResponse.model_validate(json_str)
#         except Exception:
#             pass
#
#         # 如果无法解析JSON，创建默认响应
#         return TravelPlanResponse(
#             destination="目的地",
#             start_date="开始日期",
#             end_date="结束日期",
#             days=[]
#         )
#
#     def get_conversation_history(self) -> List[Dict]:
#         """获取会话历史"""
#         try:
#             # 从检查点获取状态
#             checkpoint = self.checkpointer.get(self.config)
#             if checkpoint:
#                 messages = checkpoint.get('messages', [])
#                 return [
#                     {"role": msg.type, "content": msg.content}
#                     for msg in messages
#                 ]
#             return []
#         except Exception as e:
#             logger.error(f"获取消息历史失败: {str(e)}")
#             return []
#
#     def clear_conversation_history(self):
#         """清除当前用户的会话历史"""
#         try:
#             self.checkpointer.delete_thread(self.config['configurable']['thread_id'])
#             self.reset()
#         except Exception as e:
#             logger.error(f"清除会话历史失败: {str(e)}")


import datetime
import json
import logging
from typing import Dict, List, Optional, Any, TypedDict, Sequence
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.prebuilt import create_react_agent
from langchain.chains import LLMChain
from langchain_community.chat_models.tongyi import ChatTongyi
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph, END, add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from typing_extensions import Annotated
from models.request_model import TravelPlanRequest
from models.trip_plan_model import TravelPlanResponse, Activity, DayPlan
from tools import ALL_TOOLS  # 所有工具集合
from apis.weather import QWeatherAPI  # 导入天气API类
from datetime import datetime, timedelta  # 用于日期计算
import dateparser

import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))  # 加入 test_planner.py 所在目录
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))  # 加入项目根目录
# 配置日志
logger = logging.getLogger(__name__)


class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    request: Optional[TravelPlanRequest]


class QwenTravelPlanner:
    """基于 Qwen-Max 模型的行程规划器（使用 LangGraph 实现消息持久化）"""

    # 1.创建agent调用工具进行输入输出
    # 2.创建结构化输出，用于提取，辅助agent
    def __init__(self, user: str, session: str):
        self.user = user
        self.session = session
        self.reset()

    def reset(self):
        # 初始化 Qwen-Max 模型
        self.chat_llm = ChatTongyi(model_name='qwen-max', streaming=True)

        # 创建检查点存储器
        self.checkpointer = MemorySaver()

        # 对用户输入的文本进行提取，然后结构化输出
        self.struct_request_llm = self.chat_llm.with_structured_output(TravelPlanRequest)

        # 使用agent根据API搜索的消息进行整合
        self.agent = create_react_agent(self.chat_llm, ALL_TOOLS, checkpointer=self.checkpointer)

        # 对大模型响应的内容进行结构化
        self.struct_response_llm = self.chat_llm.with_structured_output(TravelPlanResponse)

        # 定义工作流的应用程序
        self.app = self._build_graph()

        # 定义会话线程id
        self.config = {'configurable': {'thread_id': self.user + '_' + self.session}}

    def _build_system_prompt(self) -> str:
        return '''
        你是一名专业的行程规划师，请根据用户需求规划3套不同风格的旅行行程方案。每套方案需包含以下详细信息：

        # 方案要求
        1. 每种方案应有鲜明的主题特色（如：文化探索/美食之旅/自然休闲/亲子欢乐等）
        2. 每个方案必须包含：
           - 清晰的每日时间安排（精确到小时）
           - 每个时段（如上午/下午/晚上）需细分为多个具体时间段（如8:00-9:00、9:00-11:00等），每个时间段安排一个具体活动
           - 每个活动的详细地址和交通方式
           - 每个景点/活动都要有一句简短的介绍（如“宏村：中国最美的古村落之一，徽派建筑代表”）
           - 交通部分要非常详细，需包含：交通方式、出发地、目的地、预计时长、费用、路线描述、换乘信息（如有），如“打车（从酒店到宏村），约30分钟，费用约50元”或“公交K1路（从屯溪老街到西递），约40分钟，票价2元，需在XX站换乘”
           - 餐饮推荐（包含餐厅评分和人均价格）
           - 住宿推荐（包含酒店评分和价格区间）
           - 天气适应性建议
           - 费用预估明细
        3. 活动安排应考虑：
           - 合理的交通时间和景点开放时间
           - 天气状况对户外活动的影响
           - 不同年龄人群的需求

        # 规划原则
        1. 每个方案必须完整独立，不能简单修改
        2. 活动安排要符合当地实际情况
        3. 推荐内容需基于真实数据和用户偏好
        4. 提供专业实用的旅行建议

        # 输出格式要求
        请严格按照以下Markdown格式输出，包含所有指定部分：

        # [方案X名称]之旅
        ## 1. 方案特色
        [简要说明本方案的特色和适合人群]

        ## 2. 每日详细安排
        - **第N天：YYYY-MM-DD**
          - **上午/中午/下午/晚上**（每个时段都需包含，且每个时段细分为多个时间段，每个时间段安排一个具体活动）
            - **8:00-9:00**：活动描述
              - 备注：如有特殊注意事项请在此处补充（如“建议提前预订门票”或“注意防晒和补水”）
            - **9:00-11:00**：活动描述
              - 备注：如有特殊注意事项请在此处补充
            ...

        ## 3. 餐饮推荐
        - 早餐/午餐/晚餐：
          - 餐厅名称（评分X/X，人均XX元）
          - 推荐菜品
          - 地址和交通

        ## 4. 住宿推荐
        - 酒店名称（评分X/X）
        - 地址
        - 价格区间
        - 特色描述

        ## 5. 天气信息
        - 每日天气状况和穿衣建议

        ## 6. 费用预估
        - 分类明细（餐饮/门票/交通/住宿）
        - 总预算范围

        ## 7. 注意事项
        - 安全提醒
        - 特殊提示
        - 预订建议

        输出的内容一定要准确、详细，尤其是交通和景点介绍部分。可参考如下示例：
        - 交通：打车（从酒店到宏村），约30分钟，费用约50元
        - 交通：公交K1路（从屯溪老街到西递），约40分钟，票价2元，需在XX站换乘
        - 景点介绍：宏村，中国最美的古村落之一，徽派建筑代表
        - 备注：建议提前预订门票，注意防晒和补水等
'''

    def _build_user_prompt(self, request: TravelPlanRequest) -> str:
        """构建用户提示词"""
        return f"""
        ### 用户旅行需求
        - 目的地: {request.destination}
        - 出行时间: {request.start_date} 至 {request.end_date}（共 {request.duration} 天）
        - 出行人数: {request.travelers} 人（{self._parse_age_groups(request)}）
        - 旅行类型: {request.trip_type}
        - 兴趣偏好: {request.interests or "无特别偏好"}
        - 预算范围: {request.budget or "无限制"}
        - 特殊要求: {request.special_requests or "无"}

        ### 规划要求
        请提供3套不同风格的{request.duration}天行程方案，要求：
        1. 每套方案必须有鲜明主题和特色
        2. 包含所有必要的实用信息（地址、交通、价格等）
        3. 考虑天气因素调整户外活动
        4. 提供专业贴心的旅行建议
        """ + self._build_weather_prompt(request)

    def _parse_age_groups(self, request: TravelPlanRequest) -> str:
        """解析年龄构成"""
        # 这里可以添加从request中解析年龄构成的逻辑
        return "年龄构成未指定"

    def _parse_natural_date(self, text: str) -> str:
        """将自然语言日期（如‘下周四’）解析为YYYY-MM-DD"""
        dt = dateparser.parse(text, languages=['zh'])
        if dt:
            return dt.strftime("%Y-%m-%d")
        return text  # fallback

    def _build_weather_prompt(self, request: TravelPlanRequest) -> str:
        """构建详细的天气提示词"""
        weather_api = QWeatherAPI()
        try:
            import time
            time.sleep(1)  # 增加1秒延迟，避免QPS超限
            weather_data = weather_api.get_city_weather_summary(request.destination)

            if "error" in weather_data:
                return "\n\n⚠️ 天气服务暂时不可用，请根据季节准备常规衣物"

            # 计算行程天数
            try:
                start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
                end_date = datetime.strptime(request.end_date, "%Y-%m-%d")
                days = (end_date - start_date).days + 1
            except:
                days = min(7, request.duration or 7)

            prompt_lines = [
                "\n\n### 目的地天气综合分析",
                "以下天气预报数据可用于调整行程安排："
            ]

            # 当前天气
            if weather_data.get("current"):
                current = weather_data["current"]
                prompt_lines.extend([
                    f"- 当前天气: {current['weather']}，气温 {current['temperature']}°C",
                    f"- 风力: {current['wind_dir']}风 {current['wind_speed']}",
                    f"- 湿度: {current.get('humidity', 'N/A')}%"
                ])

            # 天气预报
            if weather_data.get("daily_forecast"):
                prompt_lines.append("\n### 行程期间每日天气预报")
                for idx, forecast in enumerate(weather_data["daily_forecast"][:days]):
                    day_num = idx + 1
                    date = forecast['datetime']
                    temp = forecast['temperature']
                    weather = forecast['weather']

                    # 生成穿衣建议
                    if "~" in temp:
                        max_temp = int(temp.split("~")[1])
                    else:
                        max_temp = int(temp)

                    clothing = self._get_clothing_suggestion(max_temp, weather)

                    prompt_lines.append(
                        f"**第{day_num}天（{date}）**: "
                        f"{weather}，气温 {temp} | "
                        f"建议穿搭: {clothing}"
                    )

            # 特别提醒
            prompt_lines.append("\n### 天气特别提醒")
            if weather_data.get("daily_forecast"):
                has_rain = any("雨" in f["weather"] for f in weather_data["daily_forecast"][:days])
                has_extreme = any(
                    "雷" in f["weather"] or "暴" in f["weather"] for f in weather_data["daily_forecast"][:days])

                if has_rain:
                    prompt_lines.append("- 部分日期有降雨，建议：")
                    prompt_lines.append("  ✓ 携带折叠伞/雨衣")
                    prompt_lines.append("  ✓ 为户外活动准备备用方案")
                    prompt_lines.append("  ✓ 选择防滑舒适的鞋子")

                if has_extreme:
                    prompt_lines.append("- 部分日期有恶劣天气，建议：")
                    prompt_lines.append("  ✓ 关注当地天气预警")
                    prompt_lines.append("  ✓ 调整户外活动时间")
                    prompt_lines.append("  ✓ 准备应急物品")

            return "\n".join(prompt_lines)
        except Exception as e:
            # 检查是否是高德API的QPS超限错误
            if "CUQPS_HAS_EXCEEDED_THE_LIMIT" in str(e):
                logger.error(f"天气API调用超限: 请稍后再试（{str(e)}）")
                return "\n\n⚠️ 天气查询过于频繁，请1分钟后重试"
            else:
                logger.error(f"天气信息获取失败: {str(e)}")
                return "\n\n⚠️ 天气服务暂时不可用，请根据季节准备常规衣物"

    def _get_clothing_suggestion(self, max_temp: int, weather: str) -> str:
        """根据温度生成穿衣建议"""
        if max_temp > 30:
            return "轻薄夏装、防晒衣、帽子、太阳镜"
        elif max_temp > 25:
            return "短袖+薄外套、舒适便鞋"
        elif max_temp > 15:
            return "长袖衣物、轻便外套"
        elif max_temp > 5:
            return "毛衣/卫衣、防风外套"
        else:
            return "羽绒服、保暖内衣、围巾手套"

    def _build_structured_prompt(self, plan_text: str) -> str:
        return f"""
           请将以下行程计划转换为结构化JSON格式：

           ### 原始行程计划
           {plan_text}

           ### 结构化要求
           请转换为以下JSON格式：
           {{
             "destination": "目的地",
             "start_date": "开始日期",
             "end_date": "结束日期",
             "summary": "行程概述",
             "days": [
               {{
                 "date": "YYYY-MM-DD",
                 "weather": "天气信息",
                 "activities": [
                   {{
                     "time": "时间段",
                     "name": "活动名称",
                     "location": "地点名称",
                     "type": "活动类型",
                     "description": "活动描述"
                   }}
                 ],
                 "hotel": {{"name": "酒店名称", "address": "酒店地址"}}
               }}
             ],
             "notes": ["建议1", "建议2"]
           }}

           请只输出JSON格式的内容，不要包含任何其他文本。
           """

    def handle_request(self, state: State):
        """将用户消息结构化为TravelPlanRequest，并添加到状态中"""
        # 只处理最后一条消息作为用户输入
        last_message = state['messages'][-1].content if state['messages'] else ""

        # 使用结构化模型生成请求对象
        request = self.struct_request_llm.invoke(last_message, config=self.config)

        # 新增：解析自然语言日期
        if request.start_date and not request.start_date.strip().isdigit() and not request.start_date.strip().startswith("20"):
            parsed = self._parse_natural_date(request.start_date.strip())
            if parsed and parsed != request.start_date:
                request.start_date = parsed

        # 返回包含请求的状态更新（不添加额外消息）
        return {
            'request': request,
            'messages': []  # 这里返回空列表，不会添加无效消息类型
        }

    def call_agent(self, state: State):
        """处理请求并使用agent生成响应"""
        request = state.get('request')
        if not request:
            logger.error("调用代理时请求对象不存在")
            return {"messages": [AIMessage(content="无法处理请求，缺少必要参数")]}

        try:
            # 1. 构建天气提示词
            weather_prompt = self._build_weather_prompt(request)

            # 2. 构建系统提示和用户提示
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(request) + weather_prompt

            # 3. 创建完整提示模板（保持不变）
            full_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=system_prompt),
                MessagesPlaceholder(variable_name="messages"),
                HumanMessage(content=user_prompt)
            ])

            # 4. 使用新的管道语法替代LLMChain
            chain = full_prompt | self.chat_llm  # 核心修改：prompt | llm

            # 5. 调用链（传入messages变量）
            agent_output = chain.invoke(
                {"messages": state['messages']},  # 传入状态中的历史消息
                config=self.config
            )

            # 6. 处理输出（保持不变）
            if isinstance(agent_output, BaseMessage):
                response_message = agent_output
            else:
                response_message = AIMessage(content=str(agent_output))

            return {
                "messages": [response_message],
                "request": request
            }

        except Exception as e:
            logger.error(f"Agent调用失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "messages": [AIMessage(content=f"行程规划出错: {str(e)}")],
                "request": request
            }

    def _build_graph(self):
        workflow = StateGraph(state_schema=State)

        workflow.add_edge(START, 'struct_request_llm')
        workflow.add_edge('struct_request_llm', 'agent')
        workflow.add_edge('agent', END)

        workflow.add_node('struct_request_llm', self.handle_request)
        workflow.add_node('agent', self.call_agent)

        app = workflow.compile(checkpointer=self.checkpointer)
        return app

    def generate_plan(self, user_input: str):
        """生成旅行计划（流式输出，模仿指定代码风格）"""
        try:
            # 准备初始状态
            initial_state = {"messages": [HumanMessage(content=user_input)], "request": None}

            # 流式调用工作流，指定stream_mode="messages"
            # 迭代获取每个消息片段和元数据
            for chunk, metadata in self.app.stream(
                    initial_state,
                    self.config,  # 使用已定义的会话配置
                    stream_mode="messages"  # 关键：按消息片段流式输出
            ):
                # 过滤并处理模型生成的AIMessage
                if isinstance(chunk, AIMessage):
                    # 实时输出当前token（不换行，强制刷新）
                    print(chunk.content, end="", flush=True)

            print()  # 所有片段输出完毕后换行
            # 返回最后一条完整消息（供历史记录使用）
            return AIMessage(content=chunk.content)  # chunk此时为最后一个片段

        except Exception as e:
            logger.error(f"行程规划失败: {str(e)}")
            print("\n助手: 抱歉，行程规划失败，请重试")
            raise

    def generate_plan_stream(self, user_input: str):
        """流式生成旅行计划，每次yield一段内容"""
        try:
            initial_state = {"messages": [HumanMessage(content=user_input)], "request": None}
            for chunk, metadata in self.app.stream(
                    initial_state,
                    self.config,
                    stream_mode="messages"
            ):
                if isinstance(chunk, AIMessage):
                    yield chunk.content
        except Exception as e:
            yield f"抱歉，行程规划失败: {str(e)}"

    def generate_struct_plan(self, plan_text: str):
        """生成结构化json消息"""
        try:
            # 确保输入是字符串
            if not isinstance(plan_text, str):
                plan_text = str(plan_text)

            prompt = self._build_structured_prompt(plan_text)
            response = self.struct_response_llm.invoke(
                [HumanMessage(content=prompt)],  # 改为直接传入消息列表
                config=self.config
            )
            return response.model_dump_json()
        except Exception as e:
            logger.exception(f"结构化输出失败: {str(e)}")
            return self._fallback_parse_plan(plan_text)  # 确保返回回退结果

    def _fallback_parse_plan(self, plan_text: str) -> TravelPlanResponse:
        """回退解析方法（当结构化解析失败时使用）"""
        # 尝试从文本中提取JSON
        try:
            json_start = plan_text.find('{')
            json_end = plan_text.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_str = plan_text[json_start:json_end]
                return TravelPlanResponse.model_validate(json_str)
        except Exception:
            pass

        # 如果无法解析JSON，创建默认响应
        return TravelPlanResponse(
            destination="目的地",
            start_date="开始日期",
            end_date="结束日期",
            days=[]
        )

    def get_conversation_history(self) -> List[Dict]:
        """获取会话历史"""
        try:
            # 从检查点获取状态
            checkpoint = self.checkpointer.get(self.config)
            if checkpoint:
                messages = checkpoint.get('messages', [])
                return [
                    {"role": msg.type, "content": msg.content}
                    for msg in messages
                ]
            return []
        except Exception as e:
            logger.error(f"获取消息历史失败: {str(e)}")
            return []

    def clear_conversation_history(self):
        """清除当前用户的会话历史"""
        try:
            self.checkpointer.delete_thread(self.config['configurable']['thread_id'])
            self.reset()
        except Exception as e:
            logger.error(f"清除会话历史失败: {str(e)}")

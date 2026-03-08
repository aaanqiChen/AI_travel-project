import datetime
from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Dict

class Activity(BaseModel):
    """每日活动项"""
    time: str = Field(..., description="时间点或时间段，如 '10:00-12:00'")
    name: str = Field(..., description="活动名称，如 '北京故宫'")
    location: str = Field(..., description="地点名称")
    description: Optional[str] = Field(default=None, description="活动说明，可选")
    type: Optional[str] = Field(..., description="活动类型, 比如有'景点', '餐饮', '交通', '酒店', '其他'")
    metadata: Optional[Dict] = Field(default=None, description="附加信息，如地图坐标、价格、门票等")
    weather_icon: Optional[str] = Field(default=None, description="对应天气图标URL或标识符")

class DayPlan(BaseModel):
    """单日行程计划"""
    date: str = Field(..., description="日期（YYYY-MM-DD）")
    weather: Optional[str] = Field(default=None, description="天气预报，例如 '晴 32°C'")
    activities: List[Activity] = Field(..., description="当日所有活动")
    hotel: Optional[Dict] = Field(default=None, description="当晚住宿酒店信息，结构化字典")
    transportation: Optional[str] = Field(default=None, description="当日主要交通方式，如 '高铁', '自驾'")
    notes: Optional[str] = Field(default=None, description="其他注意事项")

class TravelPlanResponse(BaseModel):
    """旅行规划响应模型"""
    destination: str = Field(..., description="目的地")
    start_date: str = Field(..., description="开始日期（YYYY-MM-DD）")
    end_date: str = Field(..., description="结束日期（YYYY-MM-DD）")
    summary: Optional[str] = Field(default=None, description="行程整体摘要，如总览、推荐语等")
    days: List[DayPlan] = Field(..., description="每日行程详细列表")
    total_cost_estimate: Optional[float] = Field(default=None, description="总费用预估（元）")
    notes: Optional[str] = Field(default=None, description="整体注意事项，例如天气、交通高峰等")
    map_url: Optional[str] = Field(default=None, description="可视化地图URL，如前端展示路线图所用")


from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Literal, List
import datetime

now = datetime.datetime.now()
class TravelPlanRequest(BaseModel):
    """AI 出行计划生成请求模型"""

    destination: str = Field(description="旅行目的地")
    departure_city: Optional[str] = Field(default=None, description="出发城市，如不填则使用当前位置")

    start_date: str = Field(default=now.strftime("%Y-%m-%d"), description="出发日期")
    duration: int = Field(default=1, description="旅行天数，若填入则优先使用")
    end_date: Optional[str] = Field(default=None, description="结束日期")
    travelers: int = Field(default=1, description="出行人数")
    trip_type: Optional[str] = Field(default="旅游", description="旅行类型：旅游或出差")

    interests: Optional[str] = Field(default=None, description="兴趣偏好，支持多个, 比如有这些：['古代建筑', '美食', '自然景色', '现代建筑', '人文艺术', '民俗文化', '历史底蕴', '购物休闲', '博物馆', '宗教文化']")
    budget: Optional[str] = Field(default='中等', description="预算范围, 比如有这些：['充裕', '中等', '偏低']")
    preferred_transport: Optional[str] = Field(default=None, description="偏好的交通方式， 比如有这些：['飞机', '高铁', '自驾', '公共交通', '步行']")
    special_requests: Optional[str] = Field(default=None, description="其他特殊要求，如无障碍通道、宠物友好等")

    @model_validator(mode="after")
    def set_end_date_if_missing(self):
        if not self.end_date:
            start_dt = datetime.datetime.strptime(self.start_date, "%Y-%m-%d")
            end_dt = start_dt + datetime.timedelta(days=self.duration)
            self.end_date = end_dt.strftime("%Y-%m-%d")
        return self


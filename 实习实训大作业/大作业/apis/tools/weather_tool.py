from typing import List, Any

from langchain.tools import tool
from apis.weather import QWeatherAPI

weather_api = QWeatherAPI()

@tool
def get_current_weather_tool(city: str) -> dict:
    """获取城市的实时天气信息。输入：城市名称（如'上海'）"""
    return weather_api.get_current_weather(city)

@tool
def get_weather_forecast_tool(city: str, days: int = 3) -> list[Any]:
    """获取城市的多天天气预报。输入：城市名称（如'广州'），可选天数（默认3天）"""
    return weather_api.get_daily_forecast(city, days)

@tool
def get_hourly_forecast_tool(city: str, hours: int = 24) -> list:
    """获取城市的逐小时天气预报。输入：城市名称（如'深圳'），可选小时数（默认24小时）"""
    return weather_api.get_hourly_forecast(city, hours)

@tool
def get_weather_alerts_tool(city: str) -> list:
    """获取城市的天气预警信息。输入：城市名称（如'成都'）"""
    return weather_api.get_weather_alerts(city)
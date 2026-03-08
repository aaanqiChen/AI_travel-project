"""
LangChain工具集整合
"""
from .amap_tool import (
    geocode_tool,
    reverse_geocode_tool,
    get_static_map_tool
)

from .weather_tool import (
    get_current_weather_tool,
    get_weather_forecast_tool,
    get_hourly_forecast_tool,
    get_weather_alerts_tool
)

from .amadeus_tool import (
    search_hotels_tool,
    search_attractions_tool,
    search_restaurants_tool,
    get_driving_route_tool,
    get_city_info_tool,
    get_transit_route_tool,
    get_walking_route_tool
)

# 导出所有工具
AMAP_TOOLS = [
    geocode_tool,
    reverse_geocode_tool,
    get_static_map_tool
]

WEATHER_TOOLS = [
    get_current_weather_tool,
    get_weather_forecast_tool,
    get_hourly_forecast_tool,
    get_weather_alerts_tool
]

TRAVEL_TOOLS = [
    search_hotels_tool,
    search_attractions_tool,
    search_restaurants_tool,
    get_driving_route_tool,
    get_city_info_tool,
    get_transit_route_tool,
    get_walking_route_tool
]

ALL_TOOLS = AMAP_TOOLS + WEATHER_TOOLS + TRAVEL_TOOLS

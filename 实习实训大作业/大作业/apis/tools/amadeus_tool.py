from langchain.tools import tool
from apis.amadeus import TravelServiceAPI
from typing import Optional

travel_api = TravelServiceAPI()

@tool
def search_hotels_tool(city: str, location: Optional[str] = None,
                        price_range: Optional[str] = None,
                        rating: Optional[float] = None) -> list:
    """
    搜索指定城市的酒店。输入：
    - city: 城市名称（如'北京'）
    - location: 可选，中心点坐标（如'116.397428,39.90923'）
    - price_range: 可选，价格范围（如'200-500'）
    - rating: 可选，最低评分（如4.0）
    """
    return travel_api.search_hotels(city, location, price_range, rating)

@tool
def search_attractions_tool(city: str, keyword: Optional[str] = "景点",
                            rating: Optional[float] = None) -> list:
    """
    搜索指定城市的旅游景点。输入：
    - city: 城市名称（如'杭州'）
    - keyword: 可选，搜索关键词（默认'景点'）
    - rating: 可选，最低评分（如4.5）
    """
    return travel_api.search_attractions(city, keyword, rating)

@tool
def search_restaurants_tool(city: str, cuisine: Optional[str] = None,
                            rating: Optional[float] = None) -> list:
    """
    搜索指定城市的餐厅。输入：
    - city: 城市名称（如'广州'）
    - cuisine: 可选，菜系（如'粤菜'）
    - rating: 可选，最低评分（如4.0）
    """
    return travel_api.search_restaurants(city, cuisine, rating)

@tool
def get_transit_route_tool(origin: str, destination: str, city: str) -> dict:
    """
    获取地铁/公交路线规划。输入：
    - origin: 起点位置
    - destination: 终点位置
    - city: 城市名称（如'广州'）
    """
    return travel_api.get_transits_route(origin, destination, city)

@tool
def get_walking_route_tool(origin: str, destination: str) -> dict:
    """
    获取地步行路线规划。输入：
    - origin: 起点位置
    - destination: 终点位置
    """
    return travel_api.get_walking_route(origin, destination)

@tool
def get_driving_route_tool(origin: str, destination: str,
                           waypoints: Optional[str] = None) -> dict:
    """
    获取驾车路线规划。输入：
    - origin: 起点坐位置
    - destination: 终点位置
    - waypoints: 可选，途经点（多个点用'|'分隔，如'116.402,39.907|116.405,39.902'）
    """
    waypoints_list = waypoints.split("|") if waypoints else None
    return travel_api.get_driving_route(origin, destination, waypoints_list)


@tool
def get_city_info_tool(city: str) -> dict:
    """获取城市的基本信息。输入：城市名称（如'武汉'）"""
    return travel_api.get_city_info(city)
from langchain.tools import tool
from apis.amap import AMapAPI
from typing import Optional

amap_api = AMapAPI()

@tool
def geocode_tool(address: str) -> dict:
    """将地址转换为地理坐标（经纬度）。输入：详细地址（如'北京市海淀区中关村'）"""
    return amap_api.geocode(address)

@tool
def reverse_geocode_tool(lng: float, lat: float) -> dict:
    """将地理坐标转换为详细地址。输入：经度和纬度（如116.397428,39.90923）"""
    return amap_api.regeocode(lng, lat)

@tool
def get_static_map_tool(locations: str) -> str:
    """
    生成包含多个地点的静态地图URL。输入：
    - locations: 多个坐标点，用分号分隔（如'116.397428,39.90923;116.407396,39.904179'）
    """
    locations_list = locations.split(";")
    return amap_api.get_static_map_url(locations_list)




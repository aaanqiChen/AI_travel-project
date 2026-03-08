import requests
from typing import Dict, List, Optional
from config import Config
from utils.format_helpers import format_hotel, format_attraction, format_route


class TravelServiceAPI:
    """高德地图旅行服务封装（使用amadeus.py文件名）"""

    def __init__(self):
        self.base_url = "https://restapi.amap.com/v3"
        self.api_key = Config.AMAP_API_KEY

    def _request(self, endpoint: str, params: dict) -> dict:
        """统一高德API请求方法"""
        params = params.copy()
        params["key"] = self.api_key
        try:
            response = requests.get(f"{self.base_url}/{endpoint}", params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "1":
                raise Exception(f"API错误: {data.get('info', '未知错误')}")
            return data
        except requests.exceptions.RequestException as e:
            raise Exception(f"API请求失败: {str(e)}")

    def search_hotels(
            self,
            city: str,
            location: str = None,
            price_range: str = None,
            rating: float = None
    ) -> List[Dict]:
        """搜索酒店信息"""
        params = {
            "keywords": "酒店",
            "city": city,
            "types": "060000",  # 住宿服务分类码
            "offset": Config.MAX_RESULTS
        }

        # 添加可选参数
        if location:
            params["location"] = location
            params["radius"] = 5000  # 5公里半径

        if price_range:
            params["price_range"] = price_range

        if rating:
            params["rating"] = str(rating)

        data = self._request("place/text", params)
        return [format_hotel(poi) for poi in data.get("pois", [])]

    def search_attractions(
            self,
            city: str,
            keyword: str = "景点",
            rating: float = None
    ) -> List[Dict]:
        """搜索旅游景点"""
        params = {
            "keywords": keyword,
            "city": city,
            "types": "110000",  # 景点分类码
            "offset": Config.MAX_RESULTS
        }

        if rating:
            params["rating"] = str(rating)

        data = self._request("place/text", params)
        return [format_attraction(poi) for poi in data.get("pois", [])]

    def search_restaurants(
            self,
            city: str,
            cuisine: str = None,
            rating: float = None
    ) -> List[Dict]:
        """搜索餐厅"""
        params = {
            "keywords": "餐厅",
            "city": city,
            "types": "050000",  # 餐饮服务分类码
            "offset": Config.MAX_RESULTS
        }

        if cuisine:
            params["keywords"] = f"{cuisine}餐厅"

        if rating:
            params["rating"] = str(rating)

        data = self._request("place/text", params)
        return data.get("pois", [])

    def get_driving_route(
            self,
            origin: str,
            destination: str,
            waypoints: List[str] = None
    ) -> Optional[Dict]:
        """获取驾车路线"""
        params = {
            "origin": origin,
            "destination": destination,
            "strategy": "10",  # 避免拥堵
            "extensions": "all"
        }

        if waypoints:
            params["waypoints"] = "|".join(waypoints)

        data = self._request("direction/driving", params)
        if not data.get("route") or not data["route"].get("paths"):
            return None

        return format_route(data["route"]["paths"][0])


    def get_transits_route(self, origin: str, destination: str, city: str) -> Optional[Dict]:
        """获取地铁\公交路线"""
        params = {
            "origin": origin,
            "destination": destination,
            "extension": 'all',
            'city': city,
            'strategy': 1
        }

        data = self._request('direction/transit/integrated', params)
        if not data.get("route") or not data['route'].get('transits'):
            return None

        return format_route(data['route']['transits'][0])

    def get_walking_route(
            self,
            origin: str,
            destination: str
    ) -> Optional[Dict]:
        """获取步行路线"""
        params = {
            "origin": origin,
            "destination": destination,
            "extensions": "all",
        }

        data = self._request("direction/walking", params)
        if not data.get("route") or not data["route"].get("paths"):
            return None

        return format_route(data["route"]["paths"][0])

    def get_city_info(self, city: str) -> Optional[Dict]:
        """获取城市基本信息"""
        geocode_data = self._request("geocode/geo", {"address": city})
        if not geocode_data.get("geocodes"):
            return None

        city_data = geocode_data["geocodes"][0]
        location = city_data.get("location", "")
        lng, lat = location.split(",") if location else ("", "")

        return {
            "name": city_data.get("formatted_address", city),
            "adcode": city_data.get("adcode", ""),
            "province": city_data.get("province", ""),
            "city": city_data.get("city", ""),
            "district": city_data.get("district", ""),
            "longitude": float(lng) if lng else None,
            "latitude": float(lat) if lat else None
        }

    def get_city_info_by_location(self, location: str) -> Optional[Dict]:
        """根据经纬度获取城市信息"""
        data = self._request("geocode/regeo", {"location": location})
        if not data.get("regeocode"):
            return None
        address = data["regeocode"].get("addressComponent", {})
        formatted_address = data["regeocode"].get("formatted_address") or data["regeocode"].get("formattedAddress") or ""
        return {
            "city": address.get("city") or address.get("province") or "",
            "adcode": address.get("adcode", ""),
            "formatted_address": formatted_address
        }
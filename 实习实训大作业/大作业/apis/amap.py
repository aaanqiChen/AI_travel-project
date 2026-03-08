import requests
from typing import Dict, List, Optional
from config import Config
from utils.format_helpers import parse_location

class AMapAPI:
    """高德地图API封装类"""
    def __init__(self):
        self.base_url = r"https://restapi.amap.com/v3"
        self.api_key = Config.AMAP_API_KEY

    def _request(self, endpoint: str, params: dict) -> dict:
        """统一高德API请求方法"""
        params = params.copy()
        params["key"] = self.api_key
        try:
            response = requests.get(f"{self.base_url}/{endpoint}", params=params)
            response.raise_for_status()
            data = response.json()

            # 处理高德API返回状态
            if data.get("status") != "1":
                raise Exception(f"高德API错误: {data.get('info', '未知错误')}")
            return data
        except requests.exceptions.RequestException as e:
            raise Exception(f"API请求失败: {str(e)}")

    def geocode(self, address: str) -> Optional[Dict]:
        """地理编码：地址转坐标"""
        data = self._request("geocode/geo", {"address": address})
        geocodes = data.get('geocodes', [])
        if not geocodes:
            return None

        return parse_location(geocodes[0])

    def regeocode(self, lng: float, lat: float) -> Optional[Dict]:
        """逆地理编码：坐标转地址"""
        location = f'{lng},{lat}'
        data = self._request("geocode/regeo", {'location': location, "extensions": "all"})

        return {
            "address": data.get("regeocode", {}).get("formatted_address", ""),
            "country": data.get("regeocode", {}).get("addressComponent", {}).get("country", ""),
            "province": data.get("regeocode", {}).get("addressComponent", {}).get("province", ""),
            "city": data.get("regeocode", {}).get("addressComponent", {}).get("city", ""),
            "district": data.get("regeocode", {}).get("addressComponent", {}).get("district", ""),
        }

    def get_static_map_url(self, markers: List[str], size: str = "1024*768") -> str:
        """生成静态地图URL"""
        if not markers:
            return ""

        encoded_markers = "|".join([f"mid,0xFF0000,0:{marker}" for marker in markers])
        return f"{self.base_url}/staticmap?key={self.api_key}&size={size}&markers={encoded_markers}"




import requests
from typing import Dict, List, Optional, Any
from config import Config
from datetime import datetime

def format_weather(data: Dict, period: str) -> Dict:
    """格式化天气数据，适配高德地图API"""
    if period == "实时":
        return {
            "period": period,
            "datetime": data.get("reporttime"),
            "temperature": data.get("temperature"),
            "feels_like": None,  # 高德地图没有体感温度
            "weather": data.get("weather"),
            "wind_dir": data.get("winddirection"),
            "wind_speed": data.get("windpower"),
            "wind_scale": None,  # 高德地图没有风力等级
            "humidity": data.get("humidity"),
            "precip": None,  # 高德地图没有降水量
            "aqi": None,  # 需要额外API获取
            "visibility": None  # 高德地图没有能见度
        }
    else:  # 预报数据
        return {
            "period": period,
            "datetime": data.get("date"),
            "temperature": f"{data.get('daytemp')}~{data.get('nighttemp')}",
            "feels_like": None,
            "weather": data.get("dayweather"),
            "wind_dir": data.get("daywind"),
            "wind_speed": data.get("daypower"),
            "wind_scale": None,
            "humidity": None,
            "precip": None,
            "aqi": None,
            "visibility": None
        }

class QWeatherAPI:
    """高德地图天气API封装类"""

    def __init__(self):
        self.base_url = 'https://restapi.amap.com/v3'  # 高德地图API基础URL
        self.api_key = Config.AMAP_API_KEY  # 假设配置中已改为高德地图的API KEY

    def _request(self, endpoint: str, params: dict) -> dict:
        """统一高德地图API请求方法"""
        params = params.copy()
        params['key'] = self.api_key
        try:
            response = requests.get(f'{self.base_url}/{endpoint}', params=params)
            response.raise_for_status()
            data = response.json()
            if data.get("status") != "1":
                raise Exception(f"高德地图API错误: {data.get('info', '未知错误')} (status={data.get('status')})")
            return data
        except requests.exceptions.RequestException as e:
            raise Exception(f"API请求失败: {str(e)}")

    def get_city_id(self, city_name: str) -> Optional[str]:
        """获取城市ID的简便方法"""
        city_data = self.search_city(city_name)
        if city_data is None:
            return None
        return city_data["adcode"]

    def search_city(self, city: str) -> Optional[Dict]:
        """城市搜索"""
        data = self._request(
            "config/district",
            {'keywords': city, 'subdistrict': '0'}
        )
        districts = data.get('districts', [])
        if not districts:
            return None
        return {
            "id": districts[0]["adcode"],
            "adcode": districts[0]["adcode"],
            "name": districts[0]["name"],
            "center": districts[0]["center"],
            "level": districts[0]["level"]
        }

    def get_current_weather(self, location_id: str) -> Optional[Dict]:
        """获取实时天气"""
        data = self._request(
            "weather/weatherInfo",
            {'city': location_id, 'extensions': 'base'}
        )
        lives = data.get('lives', [])
        if not lives:
            return None
        return format_weather(lives[0], "实时")

    def get_daily_forecast(self, location_id: str, days: int = 3) -> list[Any]:
        """获取未来天气预报（3天）"""
        data = self._request(
            "weather/weatherInfo",
            {'city': location_id, 'extensions': 'all'}
        )
        forecasts = data.get('forecasts', [])
        if not forecasts:
            return []
        daily = forecasts[0].get('casts', [])[:days]
        return [format_weather(day, f"未来{idx + 1}天") for idx, day in enumerate(daily)]

    def get_hourly_forecast(self, location_id: str, hours: int = 24) -> List[Dict]:
        """获取逐小时天气预报"""
        # 高德地图API没有直接提供小时级预报，这里返回空列表保持接口一致
        return []

    def get_weather_alerts(self, location_id: str) -> List[Dict]:
        """获取天气预警信息"""
        # 高德地图API没有直接提供天气预警信息，这里返回空列表保持接口一致
        return []

    def get_city_weather_summary(self, city: str) -> Dict:
        """获取城市天气综合报告（实时+预报）"""
        city_data = self.search_city(city)
        if not city_data:
            return {"error": "找不到城市信息"}

        return {
            "current": self.get_current_weather(city_data["adcode"]),
            "daily_forecast": self.get_daily_forecast(city_data["adcode"]),
            "hourly_forecast": self.get_hourly_forecast(city_data["adcode"]),
            "alerts": self.get_weather_alerts(city_data["adcode"])
        }

#if __name__ == '__main__':
#    amap_api = QWeatherAPI()
#    res = amap_api.search_city('广州')
#    id = amap_api.get_city_id('广州')
#    res2 = amap_api.get_current_weather(id)
#    res3 = amap_api.get_daily_forecast(id)
#    print("城市信息:", res)
#    print("实时天气:", res2)
#    print("天气预报:", res3)
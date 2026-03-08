import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List


def format_hotel(poi: dict) -> Dict:
    """格式化酒店信息（旅行专用）"""
    location = poi.get("location", "")
    lng, lat = location.split(",") if location else ("", "")

    return {
        "id": poi["id"],
        "name": poi["name"],
        "type": poi["type"],
        "address": poi["address"],
        "tel": poi.get("tel", ""),
        "photos": [{"url": p["url"]} for p in poi.get("photos", [])],
        "longitude": float(lng) if lng else None,
        "latitude": float(lat) if lat else None,
        "rating": poi.get("biz_ext", {}).get("rating", ""),
        "price": poi.get("biz_ext", {}).get("cost", "")
    }


def parse_location(location_data: dict) -> Dict:
    """解析高德地图的位置数据"""
    location_str = location_data.get("location", "")
    lng, lat = location_str.split(",") if location_str else ("", "")

    return {
        "formatted_address": location_data.get("formatted_address", "") or location_data.get("formattedAddress", ""),
        "country": location_data.get("country", ""),
        "province": location_data.get("province", ""),
        "city": location_data.get("city", ""),
        "district": location_data.get("district", ""),
        "adcode": location_data.get("adcode", ""),
        "longitude": float(lng) if lng else None,
        "latitude": float(lat) if lat else None
    }
def format_attraction(poi: dict) -> Dict:
    """格式化景点信息（旅行专用）"""
    location = poi.get("location", "")
    lng, lat = location.split(",") if location else ("", "")

    return {
        "id": poi["id"],
        "name": poi["name"],
        "type": poi["type"],
        "address": poi["address"],
        "tel": poi.get("tel", ""),
        "photos": [{"url": p["url"]} for p in poi.get("photos", [])],
        "longitude": float(lng) if lng else None,
        "latitude": float(lat) if lat else None,
        "rating": poi.get("biz_ext", {}).get("rating", ""),
        "price": poi.get("biz_ext", {}).get("cost", ""),
        "opening_hours": poi.get("biz_ext", {}).get("opentime", "")
    }

def format_weather(data: dict, period: str) -> Dict:
    """格式化和风天气数据"""
    return {
        "period": period,
        "datetime": data.get("fxTime") or data.get("fxDate"),
        "temperature": data.get("temp") or data.get("tempMin"),
        "feels_like": data.get("feelsLike"),
        "weather": data.get("text"),
        "wind_dir": data.get("windDir"),
        "wind_speed": data.get("windSpeed"),
        "wind_scale": data.get("windScale"),
        "humidity": data.get("humidity"),
        "precip": data.get("precip"),
        "aqi": data.get("aqi"),
        "visibility": data.get("vis")
    }
def format_route(route: dict) -> Dict:
    """格式化路线信息（旅行专用）"""
    return {
        "distance": int(route.get("distance", 0)),
        "duration": int(route.get("duration", 0)),
        "strategy": route.get("strategy", ""),
        "steps": [
            {
                "instruction": step.get("instruction", ""),
                "distance": int(step.get("distance", 0)),
                "duration": int(step.get("duration", 0)),
                "polyline": step.get("polyline", "")
            }
            for step in route.get("steps", [])
        ]
    }


def parse_date_range(start_date: str, end_date: str) -> List[str]:
    """解析日期范围"""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        date_list = []
        current = start
        while current <= end:
            date_list.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)

        return date_list
    except ValueError:
        return []


def extract_json_from_text(text: str) -> Optional[dict]:
    """从文本中提取JSON内容"""
    try:
        # 尝试直接解析
        return json.loads(text)
    except json.JSONDecodeError:
        # 尝试提取JSON部分
        start_idx = text.find('{')
        end_idx = text.rfind('}')

        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = text[start_idx:end_idx + 1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
    return None


def format_weather_info(weather_data: dict) -> str:
    """格式化天气信息"""
    if not weather_data:
        return ""

    return f"{weather_data.get('condition', '')} {weather_data.get('temperature', '')}°C"
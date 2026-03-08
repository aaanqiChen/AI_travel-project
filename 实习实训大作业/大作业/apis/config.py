import os
from dotenv import load_dotenv

load_dotenv()
class Config:

    # 高德地图配置
    AMAP_API_KEY = os.getenv("AMAP_API_KEY")

    # 和风天气配置（替换 OpenWeather）
    QWEATHER_API_KEY = os.getenv("QWEATHER_API_KEY")

    # 阿里云 qwen-max 配置
    DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
    QWEN_ENDPOINT = "dashscope.aliyuncs.com"

    # 模型设置
    MODEL_NAME = "qwen-max"

    # 系统设置
    MAX_RECOMMENDATIONS = int(os.getenv("MAX_RECOMMENDATIONS", 5))
    MAX_RESULTS = int(os.getenv("MAX_RESULTS", 5))  # 默认返回5条结果
    # 超时设置
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", 10))  # 默认10秒超时

    # Flask配置
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
    SESSION_TYPE = "filesystem"
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"
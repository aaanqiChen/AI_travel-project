#!/usr/bin/env python3
"""
行之有途 - AI旅行助手启动脚本
"""

import os
import sys
from app import app

if __name__ == '__main__':
    # 设置环境变量
    os.environ.setdefault('FLASK_APP', 'app.py')
    os.environ.setdefault('FLASK_ENV', 'development')
    
    # 启动Flask应用
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    ) 
#!/usr/bin/env python3
"""
简单的Flask测试脚本
"""

import os
import json
from dotenv import load_dotenv

# 设置环境变量
os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_PORT', '3306')
os.environ.setdefault('DB_USER', 'root')
os.environ.setdefault('DB_PASSWORD', '')
os.environ.setdefault('DB_DATABASE', 'travel_planner')
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-development')

def test_flask_app_direct():
    """直接测试Flask应用"""
    try:
        from app import app
        
        print("测试Flask应用...")
        
        with app.test_client() as client:
            # 测试注册页面
            response = client.get('/register')
            print(f"GET /register: {response.status_code}")
            
            # 测试注册POST请求
            test_data = {
                'username': 'simple_test_user',
                'email': 'simple_test@example.com',
                'password': 'test123',
                'confirmPassword': 'test123'
            }
            
            response = client.post('/register', 
                                data=json.dumps(test_data),
                                content_type='application/json')
            print(f"POST /register: {response.status_code}")
            print(f"Response: {response.get_data(as_text=True)}")
            
            # 测试登录POST请求
            login_data = {
                'email': 'simple_test@example.com',
                'password': 'test123'
            }
            
            response = client.post('/login', 
                                data=json.dumps(login_data),
                                content_type='application/json')
            print(f"POST /login: {response.status_code}")
            print(f"Response: {response.get_data(as_text=True)}")
            
        return True
    except Exception as e:
        print(f"❌ Flask测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("开始简单测试...")
    print("=" * 40)
    
    test_flask_app_direct()
    
    print("=" * 40)
    print("测试完成！") 
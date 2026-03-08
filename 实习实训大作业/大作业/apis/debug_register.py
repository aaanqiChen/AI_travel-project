#!/usr/bin/env python3
"""
注册功能调试脚本
"""

import os
import sys
from dotenv import load_dotenv

# 设置环境变量
os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_PORT', '3306')
os.environ.setdefault('DB_USER', 'root')
os.environ.setdefault('DB_PASSWORD', '')
os.environ.setdefault('DB_DATABASE', 'travel_planner')
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-development')

def test_database_tables():
    """测试数据库表是否存在"""
    try:
        from db.database import db
        
        tables = ['users', 'conversations', 'conversation_messages']
        for table in tables:
            result = db.fetchone(f"SHOW TABLES LIKE '{table}'")
            if result:
                print(f"✅ 表 {table} 存在")
            else:
                print(f"❌ 表 {table} 不存在")
                return False
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        return False

def test_user_creation():
    """测试用户创建功能"""
    try:
        from db.user_dao import user_dao
        import bcrypt
        
        # 测试数据
        test_username = "test_user"
        test_email = "test@example.com"
        test_password = "test123"
        
        # 检查用户是否已存在
        existing_user = user_dao.get_user_by_email(test_email)
        if existing_user:
            print(f"⚠️ 测试用户已存在: {test_email}")
            return True
        
        # 加密密码
        hashed_password = bcrypt.hashpw(test_password.encode('utf-8'), bcrypt.gensalt())
        
        # 创建用户
        user_id = user_dao.create_user(
            username=test_username,
            email=test_email,
            password=hashed_password.decode('utf-8')
        )
        
        if user_id:
            print(f"✅ 用户创建成功，ID: {user_id}")
            return True
        else:
            print("❌ 用户创建失败")
            return False
            
    except Exception as e:
        print(f"❌ 用户创建测试失败: {str(e)}")
        return False

def test_flask_app():
    """测试Flask应用"""
    try:
        from app import app
        print("✅ Flask应用导入成功")
        
        # 测试路由
        with app.test_client() as client:
            # 测试注册页面
            response = client.get('/register')
            print(f"注册页面状态码: {response.status_code}")
            
            # 测试登录页面
            response = client.get('/login')
            print(f"登录页面状态码: {response.status_code}")
            
        return True
    except Exception as e:
        print(f"❌ Flask应用测试失败: {str(e)}")
        return False

if __name__ == '__main__':
    print("开始调试注册功能...")
    print("=" * 50)
    
    # 测试数据库表
    print("1. 测试数据库表...")
    test_database_tables()
    print()
    
    # 测试用户创建
    print("2. 测试用户创建...")
    test_user_creation()
    print()
    
    # 测试Flask应用
    print("3. 测试Flask应用...")
    test_flask_app()
    print()
    
    print("=" * 50)
    print("调试完成！") 
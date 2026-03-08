#!/usr/bin/env python3
"""
详细的注册功能调试脚本
"""

import os
import sys
import json
from dotenv import load_dotenv

# 设置环境变量
os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_PORT', '3306')
os.environ.setdefault('DB_USER', 'root')
os.environ.setdefault('DB_PASSWORD', '')
os.environ.setdefault('DB_DATABASE', 'travel_planner')
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-development')

def test_database_structure():
    """测试数据库结构"""
    try:
        from db.database import db
        
        print("检查users表结构...")
        result = db.fetchall("DESCRIBE users")
        for row in result:
            print(f"  {row}")
        
        print("\n检查users表数据...")
        result = db.fetchall("SELECT COUNT(*) as count FROM users")
        print(f"  用户数量: {result[0]['count']}")
        
        return True
    except Exception as e:
        print(f"❌ 数据库结构检查失败: {str(e)}")
        return False

def test_user_dao_methods():
    """测试用户DAO方法"""
    try:
        from db.user_dao import user_dao
        
        print("\n测试用户DAO方法...")
        
        # 测试邮箱检查
        test_email = "test@example.com"
        exists = user_dao.check_email_exists(test_email)
        print(f"  邮箱 {test_email} 存在: {exists}")
        
        # 测试用户名检查
        test_username = "test_user"
        user = user_dao.get_user_by_username(test_username)
        print(f"  用户名 {test_username} 存在: {user is not None}")
        
        return True
    except Exception as e:
        print(f"❌ 用户DAO测试失败: {str(e)}")
        return False

def test_flask_register_endpoint():
    """测试Flask注册端点"""
    try:
        from app import app
        
        print("\n测试Flask注册端点...")
        
        with app.test_client() as client:
            # 测试GET请求
            response = client.get('/register')
            print(f"  GET /register 状态码: {response.status_code}")
            
            # 测试POST请求
            test_data = {
                'username': 'test_user_2',
                'email': 'test2@example.com',
                'password': 'test123',
                'confirmPassword': 'test123'
            }
            
            response = client.post('/register', 
                                data=json.dumps(test_data),
                                content_type='application/json')
            print(f"  POST /register 状态码: {response.status_code}")
            
            if response.status_code != 200:
                print(f"  响应内容: {response.get_data(as_text=True)}")
            
        return True
    except Exception as e:
        print(f"❌ Flask注册端点测试失败: {str(e)}")
        return False

def test_user_creation_direct():
    """直接测试用户创建"""
    try:
        from db.user_dao import user_dao
        import bcrypt
        
        print("\n直接测试用户创建...")
        
        # 测试数据
        test_username = "direct_test_user"
        test_email = "direct_test@example.com"
        test_password = "test123"
        
        # 检查用户是否已存在
        existing_user = user_dao.get_user_by_email(test_email)
        if existing_user:
            print(f"  ⚠️ 测试用户已存在: {test_email}")
            return True
        
        # 加密密码
        hashed_password = bcrypt.hashpw(test_password.encode('utf-8'), bcrypt.gensalt())
        
        print(f"  创建用户: {test_username} ({test_email})")
        
        # 创建用户
        user_id = user_dao.create_user(
            username=test_username,
            email=test_email,
            password=hashed_password.decode('utf-8')
        )
        
        if user_id:
            print(f"  ✅ 用户创建成功，ID: {user_id}")
            return True
        else:
            print("  ❌ 用户创建失败")
            return False
            
    except Exception as e:
        print(f"  ❌ 直接用户创建测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("开始详细调试注册功能...")
    print("=" * 60)
    
    # 测试数据库结构
    print("1. 测试数据库结构...")
    test_database_structure()
    
    # 测试用户DAO方法
    print("\n2. 测试用户DAO方法...")
    test_user_dao_methods()
    
    # 测试Flask注册端点
    print("\n3. 测试Flask注册端点...")
    test_flask_register_endpoint()
    
    # 直接测试用户创建
    print("\n4. 直接测试用户创建...")
    test_user_creation_direct()
    
    print("\n" + "=" * 60)
    print("详细调试完成！") 
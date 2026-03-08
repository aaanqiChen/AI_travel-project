from typing import Optional, Dict, List
from datetime import datetime
from db.database import db

class UserDAO:
    """用户数据访问对象，封装用户相关数据库操作"""

    @staticmethod
    def create_user(
            username: str,
            email: str,
            password: str,
            avatar_url: Optional[str] = None,
            user_type: int = 0
    ) -> Optional[int]:
        """
        注册新用户
        """
        if avatar_url is None:
            avatar_url = '/static/avatars/生成网页头像.png'
            sql = """
            INSERT INTO users (
                username, email, password, avatar_url, user_type
            ) VALUES (%s, %s, %s, %s, %s)
            """
            params = (username, email, password, avatar_url, user_type)
        try:
            db.execute(sql, params)
            result = db.fetchone("SELECT LAST_INSERT_ID() AS user_id")
            if result is not None:
                print(f"用户创建成功，ID: {result['user_id']}")
                return result['user_id']
            else:
                print("用户创建失败：无法获取用户ID")
                return None
        except Exception as e:
            print(f"创建用户失败: {str(e)}")
            return None

    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict]:
        sql = """
        SELECT 
            user_id, username, email, password, 
            status, user_type, avatar_url, created_at, last_login_at
        FROM users 
        WHERE email = %s
        """
        try:
            return db.fetchone(sql, (email,))
        except Exception as e:
            print(f"查询用户失败（邮箱）: {str(e)}")
            return None

    @staticmethod
    def get_user_by_username(username: str) -> Optional[Dict]:
        sql = """
        SELECT user_id, username, email, status 
        FROM users 
        WHERE username = %s
        """
        try:
            return db.fetchone(sql, (username,))
        except Exception as e:
            print(f"查询用户失败（用户名）: {str(e)}")
            return None

    @staticmethod
    def update_last_login(user_id: int, login_ip: str) -> bool:
        sql = """
        UPDATE users 
        SET last_login_at = %s, login_ip = %s, updated_at = %s
        WHERE user_id = %s
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            rows_affected = db.execute(sql, (current_time, login_ip, current_time, user_id))
            return rows_affected > 0
        except Exception as e:
            print(f"更新登录信息失败: {str(e)}")
            return False

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[Dict]:
        sql = """
        SELECT 
            user_id, username, email, avatar_url, user_type, 
            status, created_at, last_login_at
        FROM users 
        WHERE user_id = %s
        """
        try:
            return db.fetchone(sql, (user_id,))
        except Exception as e:
            print(f"查询用户失败（ID）: {str(e)}")
            return None

    @staticmethod
    def update_user_info(
            user_id: int,
            username: Optional[str] = None,
            avatar_url: Optional[str] = None,
            user_type: Optional[int] = None
    ) -> bool:
        update_fields = []
        params = []
        if username:
            update_fields.append("username = %s")
            params.append(username)
        if avatar_url is not None:
            update_fields.append("avatar_url = %s")
            params.append(avatar_url)
        if user_type is not None:
            update_fields.append("user_type = %s")
            params.append(user_type)
        if not update_fields:
            return True
        sql = f"UPDATE users SET {', '.join(update_fields)}, updated_at = %s WHERE user_id = %s"
        params.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        params.append(user_id)
        try:
            rows_affected = db.execute(sql, tuple(params))
            return rows_affected > 0
        except Exception as e:
            print(f"更新用户信息失败: {str(e)}")
            return False

    @staticmethod
    def check_email_exists(email: str) -> bool:
        sql = "SELECT 1 FROM users WHERE email = %s LIMIT 1"
        try:
            result = db.fetchone(sql, (email,))
            return result is not None
        except Exception as e:
            print(f"检查邮箱存在性失败: {str(e)}")
            return False

    @staticmethod
    def update_avatar(user_id: int, avatar_url: str) -> bool:
        sql = "UPDATE users SET avatar_url = %s, updated_at = %s WHERE user_id = %s"
        from datetime import datetime
        params = (avatar_url, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id)
        try:
            rows_affected = db.execute(sql, params)
            return rows_affected > 0
        except Exception as e:
            print(f"更新头像失败: {str(e)}")
            return False

user_dao = UserDAO()

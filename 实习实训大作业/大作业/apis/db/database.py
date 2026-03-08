import pymysql
from dbutils.pooled_db import PooledDB
from pymysql.cursors import DictCursor
from contextlib import contextmanager
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
import os

# 加载.env文件中的环境变量
load_dotenv()
# 获取数据库连接信息
host = os.environ.get("DB_HOST", "localhost")
port = int(os.environ.get("DB_PORT", 3306))
user = os.environ.get("DB_USER")
password = os.environ.get("DB_PASSWORD")
database = os.environ.get("DB_DATABASE")

class Database:
    def __init__(self, config: dict):
        """初始化数据库连接池"""
        self.pool = PooledDB(
            creator=pymysql,  # 使用pymysql作为数据库驱动
            host=config["host"],  # 数据库主机地址
            port=config["port"],  # 数据库端口
            user=config["user"],  # 数据库用户名
            password=config["password"],  # 数据库密码
            database=config["database"],  # 数据库名
            charset=config.get("charset", "utf8mb4"),  # 字符集
            cursorclass=DictCursor,  # 游标返回字典格式
            autocommit=config.get("autocommit", True),  # 是否自动提交

            # 连接池参数
            mincached=config.get("mincached", 2),  # 初始空闲连接数
            maxcached=config.get("maxcached", 5),  # 最大空闲连接数
            maxconnections=config.get("maxconnections", 10),  # 最大连接数
            blocking=config.get("blocking", False),  # 连接满时是否阻塞
            maxusage=config.get("maxusage", 1000),  # 单个连接的最大复用次数
            ping=config.get("ping", 1)  # 连接前是否检查连接有效性
        )

    @contextmanager
    def connection(self):
        """获取数据库连接的上下文管理器"""
        conn = self.pool.connection()
        try:
            yield conn
        finally:
            conn.close()  # 放回连接池而非关闭

    @contextmanager
    def cursor(self, commit: bool = False):
        """获取数据库游标的上下文管理器，支持自动提交"""
        with self.connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                if commit:
                    conn.commit()  # 手动提交事务
            except Exception as e:
                conn.rollback()  # 发生异常时回滚
                raise e
            finally:
                cursor.close()

    def execute(self, query: str, params: Optional[tuple] = None) -> int:
        """执行SQL语句（增删改操作）"""
        with self.cursor(commit=True) as cursor:
            return cursor.execute(query, params)

    def fetchone(self, query: str, params: Optional[tuple] = None) -> Optional[Dict]:
        """查询单条记录"""
        with self.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()

    def fetchall(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """查询多条记录"""
        with self.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def fetchmany(self, query: str, size: int, params: Optional[tuple] = None) -> List[Dict]:
        """查询指定数量的记录"""
        with self.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchmany(size)


# 从环境变量或配置文件加载数据库配置
db_config = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", 3306)),
    "user": os.environ.get("DB_USER"),
    "password": os.environ.get("DB_PASSWORD"),
    "database": os.environ.get("DB_DATABASE"),
    "charset": "utf8mb4",
    "autocommit": True,

    # 连接池参数（根据实际情况调整）
    "mincached": 2,  # 最小空闲连接数
    "maxcached": 5,  # 最大空闲连接数
    "maxconnections": 20,  # 最大连接数
    "blocking": False,  # 连接满时是否阻塞
    "maxusage": 1000,  # 单个连接的最大复用次数
    "ping": 1  # 连接前检查有效性
}

# 创建单例数据库实例
db = Database(db_config)
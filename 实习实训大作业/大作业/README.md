# 行之有途 - AI旅行助手

一个基于Flask的智能旅行规划助手，提供用户认证、会话管理和AI对话功能。

## 功能特性

### 1. 用户认证系统
- 用户注册和登录
- 密码加密存储
- 会话管理
- 用户信息管理

### 2. 会话管理
- 创建新对话
- 会话历史记录
- 消息持久化存储
- 会话切换

### 3. AI对话功能
- 智能对话回复
- 消息暂停功能
- 消息复制和重新生成
- 流式消息显示

### 4. 数据库支持
- MySQL数据库
- 用户表管理
- 会话表管理
- 消息表管理

## 技术栈

- **后端**: Flask, Python
- **数据库**: MySQL
- **前端**: HTML, CSS, JavaScript
- **UI框架**: Tailwind CSS
- **图标**: Font Awesome

## 安装和运行

### 1. 环境要求
- Python 3.8+
- MySQL 5.7+

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 数据库配置
确保MySQL服务正在运行，并创建数据库表：

```sql
CREATE TABLE `users` (
  `user_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '用户ID，自增主键',
  `username` VARCHAR(50) NOT NULL COMMENT '用户名',
  `email` VARCHAR(100) NOT NULL COMMENT '邮箱，用于登录',
  `password` VARCHAR(255) NOT NULL COMMENT '密码',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态：0-禁用，1-正常',
  `user_type` TINYINT NOT NULL DEFAULT 0 COMMENT '用户类型：0-普通用户，1-会员用户',
  `avatar_url` VARCHAR(255) DEFAULT NULL COMMENT '头像URL',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `last_login_at` TIMESTAMP NULL DEFAULT NULL COMMENT '最后登录时间',
  `login_ip` VARCHAR(45) DEFAULT NULL COMMENT '最后登录IP',
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `idx_email` (`email`),
  UNIQUE KEY `idx_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户信息表';

CREATE TABLE `conversations` (
  `conversation_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '会话ID',
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT '关联的用户ID',
  `title` VARCHAR(255) NOT NULL DEFAULT '新对话' COMMENT '对话标题',
  `model_name` VARCHAR(50) NOT NULL COMMENT '使用的模型名称',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_active` TINYINT NOT NULL DEFAULT 1 COMMENT '是否活跃：0-历史对话，1-当前对话',
  `metadata` JSON DEFAULT NULL COMMENT '附加元数据(JSON格式)',
  PRIMARY KEY (`conversation_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_user_active` (`user_id`, `is_active`),
  CONSTRAINT `fk_conversations_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户对话会话表';

CREATE TABLE `conversation_messages` (
  `message_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '消息ID',
  `conversation_id` BIGINT UNSIGNED NOT NULL COMMENT '关联的会话ID',
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT '关联的用户ID',
  `message_type` ENUM('user', 'assistant', 'system') NOT NULL COMMENT '消息类型',
  `content` LONGTEXT NOT NULL COMMENT '消息内容',
  `langgraph_state` JSON DEFAULT NULL COMMENT 'LangGraph持久化状态',
  `tokens` INT DEFAULT NULL COMMENT '消息消耗的token数量',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `sequence` INT NOT NULL COMMENT '消息顺序号',
  `metadata` JSON DEFAULT NULL COMMENT '附加元数据(JSON格式)',
  PRIMARY KEY (`message_id`),
  KEY `idx_conversation_id` (`conversation_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_conversation_sequence` (`conversation_id`, `sequence`),
  CONSTRAINT `fk_messages_conversation` FOREIGN KEY (`conversation_id`) REFERENCES `conversations` (`conversation_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_messages_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对话消息表';
```

### 4. 环境变量配置
创建 `.env` 文件并配置以下变量：

```env
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_DATABASE=your_database_name

# Flask配置
SECRET_KEY=your-secret-key-here
FLASK_DEBUG=True

# API密钥（可选）
AMAP_API_KEY=your_amap_api_key
QWEATHER_API_KEY=your_qweather_api_key
DASHSCOPE_API_KEY=your_dashscope_api_key
```

### 5. 运行应用
```bash
python run.py
```

或者使用Flask命令：
```bash
flask run
```

应用将在 `http://localhost:5000` 启动。

## 使用说明

### 1. 注册和登录
- 访问 `http://localhost:5000/register` 注册新用户
- 访问 `http://localhost:5000/login` 登录

### 2. 开始对话
- 登录后自动跳转到聊天界面
- 点击"新对话"创建新的会话
- 在左侧可以看到会话历史列表

### 3. 功能操作
- **发送消息**: 在输入框中输入消息，按回车或点击发送按钮
- **暂停生成**: 在AI回复过程中点击"暂停生成"按钮
- **复制消息**: 鼠标悬停在AI消息上，点击复制按钮
- **重新生成**: 鼠标悬停在AI消息上，点击重新生成按钮

## 项目结构

```
大作业/
├── app.py                 # Flask主应用
├── run.py                 # 启动脚本
├── config.py              # 配置文件
├── requirements.txt        # 依赖包列表
├── README.md              # 项目说明
├── db/                    # 数据库相关
│   ├── database.py        # 数据库连接
│   ├── user_dao.py        # 用户数据访问
│   ├── conversation_dao.py # 会话数据访问
│   └── message_dao.py     # 消息数据访问
├── models/                # 数据模型
│   ├── chat_model.py      # 聊天模型
│   ├── request_model.py   # 请求模型
│   └── trip_plan_model.py # 旅行计划模型
├── apis/                  # API接口
├── tools/                 # 工具类
├── utils/                 # 工具函数
└── node-site/            # 前端文件
    └── static/
        ├── index.html     # 主页面
        ├── login.html     # 登录页面
        └── register.html  # 注册页面
```

## API接口

### 用户认证
- `POST /login` - 用户登录
- `POST /register` - 用户注册
- `GET /logout` - 退出登录

### 会话管理
- `GET /api/conversations` - 获取会话列表
- `POST /api/conversations` - 创建新会话
- `GET /api/conversations/<id>/messages` - 获取会话消息

### 消息处理
- `POST /api/conversations/<id>/messages` - 发送消息
- `POST /api/conversations/<id>/assistant` - 获取AI回复

### 用户信息
- `GET /api/user/profile` - 获取用户信息

## 注意事项

1. 确保MySQL服务正在运行
2. 正确配置数据库连接信息
3. 设置合适的SECRET_KEY
4. 在生产环境中关闭DEBUG模式

## 许可证

MIT License 
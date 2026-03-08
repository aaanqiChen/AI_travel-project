from flask import Flask, request, jsonify
import json
import sqlite3
from datetime import datetime

app = Flask(__name__)

# 数据库文件路径
DATABASE = 'services.db'


# 初始化数据库
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_services (
            user_id TEXT PRIMARY KEY,
            service1 TEXT,
            service2 TEXT,
            service3 TEXT
        )
    ''')
    conn.commit()
    conn.close()


# 更新数据库记录
def update_database(data):
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        # 检查用户ID是否已存在
        c.execute("SELECT user_id FROM user_services WHERE user_id = ?", (data['用户id'],))
        exists = c.fetchone() is not None

        # 如果存在则删除
        if exists:
            c.execute("DELETE FROM user_services WHERE user_id = ?", (data['用户id'],))

        # 插入新记录
        c.execute(
            "INSERT INTO user_services (user_id, service1, service2, service3) VALUES (?, ?, ?, ?)",
            (data['用户id'], data['服务1'], data['服务2'], data['服务3'])
        )

        conn.commit()
        return True, "更新成功"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


# 保存JSON文件
def save_json(data):
    filename = f"user_{data['用户id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True, filename
    except Exception as e:
        return False, str(e)


# 主页路由
@app.route('/')
def index():
    with open('index.html', 'r', encoding='utf-8') as f:
        return f.read()


# 提交表单处理
@app.route('/submit', methods=['POST'])
def submit():
    try:
        data = request.get_json()

        # 保存JSON文件
        json_success, json_message = save_json(data)

        # 更新数据库
        db_success, db_message = update_database(data)

        if db_success and json_success:
            return jsonify({
                'status': 'success',
                'message': '操作成功',
                'json_file': json_message
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'JSON保存: {json_message}; 数据库更新: {db_message}'
            }), 500

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
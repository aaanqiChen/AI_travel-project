from flask import Flask, request, jsonify, session, redirect, url_for, render_template_string, Response, stream_with_context, send_from_directory
from flask_session import Session
import bcrypt
import os
from datetime import datetime, timedelta
from functools import wraps
from db.user_dao import user_dao
from db.conversation_dao import conversation_dao
from db.message_dao import message_dao
from config import Config
import json
from werkzeug.utils import secure_filename
from apis.amadeus import TravelServiceAPI
from PIL import Image, ImageDraw, ImageFont
import uuid
import re
from utils.poster_struct import extract_travel_handbook_struct
import textwrap

app = Flask(__name__)
app.config.from_object(Config)

# 配置Flask-Session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
Session(app)

def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': '请先登录'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """首页"""
    if 'user_id' in session:
        return redirect('/chat')
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录处理"""
    if request.method == 'GET':
        # 如果已登录，重定向到聊天页面
        if 'user_id' in session:
            return redirect('/chat')
        
        # 返回登录页面HTML
        with open('node-site/static/login.html', 'r', encoding='utf-8') as f:
            return f.read()
    
    elif request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': '邮箱和密码不能为空'}), 400
        
        # 查询用户
        user = user_dao.get_user_by_email(email)
        if not user:
            return jsonify({'error': '用户不存在'}), 401
        
        # 验证密码
        if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return jsonify({'error': '密码错误'}), 401
        
        # 检查用户状态
        if user['status'] != 1:
            return jsonify({'error': '账户已被禁用'}), 403
        
        # 创建会话
        session['user_id'] = user['user_id']
        session['username'] = user['username']
        session['email'] = user['email']
        
        # 更新最后登录时间
        user_dao.update_last_login(user['user_id'], request.remote_addr)
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'user': {
                'user_id': user['user_id'],
                'username': user['username'],
                'email': user['email']
            }
        })

@app.route('/register', methods=['GET', 'POST'])
def register():
    """注册处理"""
    if request.method == 'GET':
        # 如果已登录，重定向到聊天页面
        if 'user_id' in session:
            return redirect('/chat')
        
        # 返回注册页面HTML
        with open('node-site/static/register.html', 'r', encoding='utf-8') as f:
            return f.read()
    
    elif request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirmPassword')
        
        # 验证输入
        if not username or not email or not password:
            return jsonify({'error': '所有字段都是必填的'}), 400
        
        if password != confirm_password:
            return jsonify({'error': '两次输入的密码不一致'}), 400
        
        if len(password) < 6:
            return jsonify({'error': '密码长度至少6位'}), 400
        
        # 检查用户名是否已存在
        if user_dao.get_user_by_username(username):
            return jsonify({'error': '用户名已存在'}), 409
        
        # 检查邮箱是否已存在
        if user_dao.check_email_exists(email):
            return jsonify({'error': '邮箱已被注册'}), 409
        
        # 加密密码
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        try:
            # 创建用户
            user_id = user_dao.create_user(
                username=username,
                email=email,
                password=hashed_password.decode('utf-8')
            )
            
            if user_id is not None:
                return jsonify({
                    'success': True,
                    'message': '注册成功，请登录'
                })
            else:
                print(f"用户创建失败: username={username}, email={email}")
                return jsonify({'error': '注册失败，请重试'}), 500
                
        except Exception as e:
            print(f"注册异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': '注册失败，请重试'}), 500

@app.route('/logout')
def logout():
    """退出登录"""
    session.clear()
    return jsonify({'success': True, 'message': '已退出登录'})

@app.route('/chat')
@login_required
def chat():
    """聊天页面"""
    with open('node-site/static/index.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/api/conversations', methods=['GET'])
@login_required
def get_conversations():
    """获取用户的会话列表"""
    user_id = session['user_id']
    conversations = conversation_dao.get_user_conversations(user_id)
    return jsonify({'conversations': conversations})

@app.route('/api/conversations', methods=['POST'])
@login_required
def create_conversation():
    """创建新会话"""
    user_id = session['user_id']
    data = request.get_json()
    model_name = data.get('model_name', 'qwen-max')

    # 自动生成当天的对话名“对话1”、“对话2”...
    import datetime
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    conversations = conversation_dao.get_user_conversations(user_id) or []
    today_count = sum(1 for c in conversations if c.get('created_at', '') and str(c.get('created_at', '')).startswith(today))
    title = f'对话{today_count + 1}'
    
    conversation_id = conversation_dao.create_conversation(
        user_id=user_id,
        model_name=model_name,
        title=title
    )
    
    if conversation_id:
        return jsonify({
            'success': True,
            'conversation_id': conversation_id,
            'message': '会话创建成功',
            'title': title
        })
    else:
        return jsonify({'error': '创建会话失败'}), 500

@app.route('/api/conversations/<int:conversation_id>/title', methods=['PUT'])
@login_required
def rename_conversation(conversation_id):
    """重命名会话"""
    user_id = session['user_id']
    data = request.get_json()
    new_title = data.get('title')
    if not new_title or not new_title.strip():
        return jsonify({'error': '新标题不能为空'}), 400
    success = conversation_dao.update_conversation_title(conversation_id, user_id, new_title.strip())
    if success:
        return jsonify({'success': True, 'message': '重命名成功'})
    else:
        return jsonify({'error': '重命名失败'}), 500

@app.route('/api/conversations/<int:conversation_id>/messages', methods=['GET'])
@login_required
def get_messages(conversation_id):
    """获取会话的消息历史"""
    user_id = session['user_id']
    
    # 验证会话归属
    conversation = conversation_dao.get_conversation_by_id(conversation_id, user_id)
    if not conversation:
        return jsonify({'error': '会话不存在或无权限访问'}), 404
    
    # 获取消息历史
    messages = message_dao.get_conversation_messages(conversation_id)
    return jsonify({'messages': messages})

@app.route('/api/conversations/<int:conversation_id>/messages', methods=['POST'])
@login_required
def send_message(conversation_id):
    """发送消息"""
    user_id = session['user_id']
    data = request.get_json()
    content = data.get('content')
    message_type = data.get('type', 'user')
    
    if not content:
        return jsonify({'error': '消息内容不能为空'}), 400
    
    # 验证会话归属
    conversation = conversation_dao.get_conversation_by_id(conversation_id, user_id)
    if not conversation:
        return jsonify({'error': '会话不存在或无权限访问'}), 404
    
    # 获取当前消息序号
    latest_message = message_dao.get_latest_message(conversation_id)
    sequence = 1 if not latest_message else latest_message['sequence'] + 1
    
    # 保存用户消息
    message_id = message_dao.save_message(
        conversation_id=conversation_id,
        user_id=user_id,
        message_type=message_type,
        content=content,
        sequence=sequence
    )
    
    if message_id:
        return jsonify({
            'success': True,
            'message_id': message_id,
            'sequence': sequence
        })
    else:
        return jsonify({'error': '保存消息失败'}), 500

@app.route('/api/conversations/<int:conversation_id>/assistant', methods=['POST'])
@login_required
def get_assistant_response(conversation_id):
    """获取AI助手流式回复"""
    user_id = session['user_id']
    data = request.get_json()
    content = data.get('content')
    if not content:
        return jsonify({'error': '消息内容不能为空'}), 400
    
    # 验证会话归属
    conversation = conversation_dao.get_conversation_by_id(conversation_id, user_id)
    if not conversation:
        return jsonify({'error': '会话不存在或无权限访问'}), 404
    
    # 获取当前消息序号
    latest_message = message_dao.get_latest_message(conversation_id)
    sequence = 1 if not latest_message else latest_message['sequence'] + 1
    
    def generate():
        buffer = ""
        message_id = None
        try:
            from ai_assistant import ai_manager
            travel_assistant = ai_manager.get_travel_assistant(user_id, conversation_id)
            for chunk in travel_assistant.smart_reply_stream(content):
                buffer += chunk
                yield chunk
        except Exception as e:
            print(f"AI流式回复生成失败: {str(e)}")
            yield "抱歉，AI回复异常，请稍后再试。"
        finally:
            if buffer.strip():
                try:
                    message_id = message_dao.save_message(
        conversation_id=conversation_id,
        user_id=user_id,
                        message_type='assistant',
                        content=buffer,
                        sequence=sequence + 1
                    )
                    # 在流式最后返回特殊标记和消息ID
                    yield f'[[[AI_MSG_ID:{message_id}]]]'
                except Exception as e:
                    print(f'保存AI消息失败: {e}')

    return Response(stream_with_context(generate()), mimetype='text/plain')

@app.route('/api/conversations/<int:conversation_id>/save_partial_ai', methods=['POST'])
@login_required
def save_partial_ai(conversation_id):
    user_id = session['user_id']
    data = request.get_json()
    content = data.get('content')
    if not content or not content.strip():
        return jsonify({'error': '内容为空'}), 400
    # 获取最新sequence
    latest_message = message_dao.get_latest_message(conversation_id)
    sequence = 1 if not latest_message else latest_message['sequence'] + 1
    message_dao.save_message(
        conversation_id=conversation_id,
        user_id=user_id,
        message_type='assistant',
        content=content,
        sequence=sequence
    )
    return jsonify({'success': True})

@app.route('/api/user/profile', methods=['GET'])
@login_required
def get_user_profile():
    """获取用户信息"""
    user_id = session['user_id']
    user = user_dao.get_user_by_id(user_id)
    
    if user:
        return jsonify({
            'user_id': user['user_id'],
            'username': user['username'],
            'email': user['email'],
            'avatar_url': user.get('avatar_url'),
            'user_type': user['user_type'],
            'created_at': user['created_at'].isoformat() if user['created_at'] else None,
            'last_login_at': user['last_login_at'].isoformat() if user['last_login_at'] else None
        })
    else:
        return jsonify({'error': '用户不存在'}), 404

@app.route('/static/avatars/<filename>')
def custom_avatar_static(filename):
    # 指定 node-site/static/avatars 作为头像静态目录
    return send_from_directory(os.path.join('node-site', 'static', 'avatars'), filename)

@app.route('/api/user/avatar', methods=['POST'])
@login_required
def upload_avatar():
    user_id = session['user_id']
    if 'avatar' not in request.files:
        return jsonify({'error': '未选择文件'}), 400
    file = request.files['avatar']
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    filename = secure_filename(f'user_{user_id}_avatar.png')
    avatar_dir = os.path.join(os.path.dirname(__file__), 'node-site', 'static', 'avatars')
    os.makedirs(avatar_dir, exist_ok=True)
    filepath = os.path.join(avatar_dir, filename)
    file.save(filepath)
    avatar_url = f'/static/avatars/{filename}'
    user_dao.update_avatar(user_id, avatar_url)
    return jsonify({'success': True, 'avatar_url': avatar_url})

@app.route('/api/conversations/<int:conversation_id>', methods=['DELETE'])
@login_required
def delete_conversation(conversation_id):
    """删除会话及其所有消息"""
    user_id = session['user_id']
    # 先检查会话归属
    conversation = conversation_dao.get_conversation_by_id(conversation_id, user_id)
    if not conversation:
        return jsonify({'error': '会话不存在或无权限访问'}), 404
    # 删除会话及消息
    try:
        conversation_dao.delete_conversation(conversation_id, user_id)
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        print(f"删除会话失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': '删除失败'}), 500

@app.route('/api/route', methods=['POST'])
@login_required
def get_route():
    data = request.get_json()
    origin = data.get('origin')
    destination = data.get('destination')
    city = data.get('city', '')
    if not origin or not destination:
        return jsonify({'error': '起点和终点不能为空'}), 400
    api = TravelServiceAPI()
    result = {
        'driving': api.get_driving_route(origin, destination),
        'walking': api.get_walking_route(origin, destination),
        'transit': api.get_transits_route(origin, destination, city) if city else None
    }
    return jsonify(result)

@app.route('/api/geo_city', methods=['POST'])
@login_required
def geo_city():
    data = request.get_json()
    location = data.get('location')
    if not location:
        return jsonify({'error': '缺少经纬度'}), 400
    api = TravelServiceAPI()
    city_info = api.get_city_info_by_location(location)
    if not city_info or not city_info.get('city'):
        return jsonify({'error': '无法识别城市'}), 400
    return jsonify({'city': city_info['city'], 'address': city_info.get('formatted_address', '')})

def filter_sensitive_content(text):
    import re
    # 替换评分格式 4.5/5 -> 4.5分
    text = re.sub(r'(评分|评分：|评分:)?([0-9]\.[0-9])/5', r'评分\2分', text)
    # 替换人均xx元 -> 人均消费xx元
    text = re.sub(r'人均([0-9]+)元', r'人均消费\1元', text)
    # 替换品牌词（可扩展）
    brand_map = {
        '狗不理包子': '知名包子店',
        '庆丰包子铺': '知名早餐店',
        '耳朵眼炸糕店': '特色小吃店',
        '桂发祥十八街麻花': '特色麻花店',
        '大福来锅巴菜': '锅巴菜馆',
        '正阳春鸭子楼': '烤鸭餐厅',
    }
    for k, v in brand_map.items():
        text = text.replace(k, v)
    # 替换“出错”字样
    text = re.sub(r'行程规划出错', '参观景点', text)
    # 替换“测试”“调试”等
    text = re.sub(r'(测试|调试)', '', text)
    return text

def markdown_to_plaintext(md: str) -> str:
    """
    将Markdown文本转为纯文本，保留换行、分区、标题缩进等结构，不保留*、#、-等符号。
    """
    import re
    # 去除标题符号
    text = re.sub(r'^#+\s*', '', md, flags=re.MULTILINE)
    # 去除无序列表符号
    text = re.sub(r'^\s*[-*+]\s*', '', text, flags=re.MULTILINE)
    # 去除加粗/斜体
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    # 去除行内代码
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # 去除多余空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def find_best_font_size(draw, text, font_path, max_width, max_height, min_size=18, max_size=32):
    """
    动态查找最佳字号，使内容刚好填满max_height且不溢出。
    """
    for size in range(max_size, min_size-1, -1):
        font = ImageFont.truetype(font_path, size)
        y = 0
        for para in text.split('\n'):
            if not para.strip():
                y += size
                continue
            current = ''
            for char in para:
                if draw.textlength(current+char, font=font) > max_width:
                    y += size
                    current = char
                else:
                    current += char
            if current:
                y += size
        if y <= max_height:
            return font
    return ImageFont.truetype(font_path, min_size)

def draw_multiline_text(draw, text, font, x, y, max_width, max_height, line_spacing=6, fill=(40,40,40,255)):
    """
    自动换行绘制多行文本，超出max_height时返回下一个起始y和剩余文本。
    """
    import textwrap
    lines = []
    for para in text.split('\n'):
        if not para.strip():
            lines.append('')
            continue
        # 动态分行，保证每行宽度不超max_width
        current = ''
        for char in para:
            if draw.textlength(current+char, font=font) > max_width:
                lines.append(current)
                current = char
            else:
                current += char
        if current:
            lines.append(current)
    y0 = y
    for line in lines:
        if y + font.size > y0 + max_height:
            # 超出最大高度，返回剩余内容
            rest = '\n'.join(lines[lines.index(line):])
            return y, rest
        draw.text((x, y), line, font=font, fill=fill)
        y += font.size + line_spacing
    return y, None

def render_sections_paged(draw, sections, font_path, x, y, max_width, max_height, min_size=18, max_size=32, sub_font=None):
    """
    分区自适应字号与分页渲染。返回每页内容列表，每页为[(title, content_lines, font)]。
    """
    pages = []
    cur_page = []
    y0 = y
    remain_height = max_height
    for sec_title, sec_content in sections:
        # 餐饮推荐和住宿推荐内容字号统一为sub_font
        if sec_title in ['餐饮推荐', '住宿推荐'] and sub_font is not None:
            best_font = sub_font
        else:
            best_font = find_best_font_size(draw, sec_content, font_path, max_width-40, remain_height-40, min_size, max_size)
        # 分行
        lines = []
        for para in sec_content.split('\n'):
            if not para.strip():
                lines.append('')
                continue
            current = ''
            for char in para:
                if draw.textlength(current+char, font=best_font) > max_width-40:
                    lines.append(current)
                    current = char
                else:
                    current += char
            if current:
                lines.append(current)
        # 计算分区高度
        block_height = (len(lines)+1)*(best_font.size+6) + (sub_font.size if sub_font else 32)
        if block_height > remain_height and cur_page:
            # 当前页放不下，分页
            pages.append(cur_page)
            cur_page = []
            remain_height = max_height
        cur_page.append((sec_title, lines, best_font))
        remain_height -= block_height
    if cur_page:
        pages.append(cur_page)
    return pages

def generate_handbook_posters_from_markdown(plan_text, out_dir='node-site/static/avatars'):
    """
    结构化AI Markdown内容，生成多方案旅行手册式海报（封面+每日行程+尾页），蓝色调极简/手绘/emoji风。
    """
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    posters = []
    plans = extract_travel_handbook_struct(plan_text)
    from PIL import Image, ImageDraw, ImageFont
    import random
    font_path = None
    for fp in ["C:/Windows/Fonts/msyh.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"]:
        if os.path.exists(fp):
            font_path = fp
            break
    title_font = ImageFont.truetype(font_path, 54) if font_path else ImageFont.load_default()
    sub_font = ImageFont.truetype(font_path, 36) if font_path else ImageFont.load_default()
    content_font = ImageFont.truetype(font_path, 28) if font_path else ImageFont.load_default()
    small_font = ImageFont.truetype(font_path, 22) if font_path else ImageFont.load_default()
    # 主题icon/emoji（已禁用）
    icons = []
    # 优先尝试更飘逸大气的封面标题字体
    fancy_title_font_path = None
    for fp in [
        "C:/Windows/Fonts/FZSTK.TTF",  # 方正舒体
        "C:/Windows/Fonts/FZYTK.TTF",  # 方正姚体
        "C:/Windows/Fonts/STXINGKA.TTF",  # 华文行楷
        "C:/Windows/Fonts/STLITI.TTF",  # 华文隶书
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    ]:
        if os.path.exists(fp):
            fancy_title_font_path = fp
            break
    blue_bg = (227, 240, 255)
    blue_card = (179, 216, 255, 240)
    for plan in plans:
        plan_name = plan['name']
        # 1. 封面
        width, height = 950, 1400
        # 使用自定义封面背景图
        cover_bg_path = os.path.join('node-site', 'static', 'avatars', 'cover_bg.png')
        if os.path.exists(cover_bg_path):
            from PIL import Image
            bg_img = Image.open(cover_bg_path).convert('RGBA').resize((width, height))
            img = Image.new('RGBA', (width, height))
            img.paste(bg_img, (0, 0))
        else:
            img = Image.new('RGBA', (width, height), color=blue_bg)
        # 加大加粗封面标题字号，优先用飘逸字体
        try:
            if fancy_title_font_path:
                cover_title_font = ImageFont.truetype(fancy_title_font_path, 92)
            else:
                cover_title_font = title_font
        except Exception:
            cover_title_font = title_font
        draw = ImageDraw.Draw(img)
        draw.text((60, 120), plan_name, font=cover_title_font, fill=(30,80,180,255))
        # 主题icon（仅icons非空时绘制）
        if icons:
            draw.text((width-180, 100), random.choice(icons), font=title_font, fill=(255,180,80,255))
        # slogan
        draw.text((60, 220), '自由·随意·发现世界', font=sub_font, fill=(80,120,200,255))
        # 卡片区
        # 方案特色文本框无边框无背景（不绘制圆角矩形）
        # 方案特色
        feat = plan['sections'].get('方案特色','')
        feat = markdown_to_plaintext(feat)
        draw.text((80, 360), '方案特色', font=title_font, fill=(60,120,220,255))
        y = 360 + title_font.size + 40  # 标题下方加大间距
        best_font = sub_font
        y, rest = draw_multiline_text(draw, feat, best_font, 100, y, width-200, height-500)
        while rest:
            img2 = Image.new('RGBA', (width, height), color=blue_bg)
            draw2 = ImageDraw.Draw(img2)
            draw2.text((60, 120), plan_name+"(续)", font=title_font, fill=(30,80,180,255))
            draw2.rounded_rectangle([(40, 320), (width-40, height-80)], radius=60, fill=blue_card, outline=(120,180,240,255), width=4)
            y2 = 360 + title_font.size + 40
            best_font2 = sub_font
            y2, rest = draw_multiline_text(draw2, rest, best_font2, 100, y2, width-200, height-500)
            filename2 = f"poster_{uuid.uuid4().hex[:8]}_cover.png"
            img2.save(os.path.join(out_dir, filename2))
            posters.append(f"/static/avatars/{filename2}")
        filename = f"poster_{uuid.uuid4().hex[:8]}_cover.png"
        img.save(os.path.join(out_dir, filename))
        posters.append(f"/static/avatars/{filename}")
        # 2. 每日行程
        page_bg_path = os.path.join('node-site', 'static', 'avatars', 'page_bg.png')
        for day in plan['days']:
            # 使用自定义内页背景图
            if os.path.exists(page_bg_path):
                from PIL import Image
                bg_img = Image.open(page_bg_path).convert('RGBA').resize((width, height))
                img = Image.new('RGBA', (width, height))
                img.paste(bg_img, (0, 0))
            else:
                img = Image.new('RGBA', (width, height), color=blue_bg)
            draw = ImageDraw.Draw(img)
            draw.text((60, 60), f"{plan_name}·DAY{day['day_num']}", font=title_font, fill=(30,80,180,255))
            draw.rounded_rectangle([(40, 160), (width-40, height-80)], radius=60, fill=blue_card, outline=(120,180,240,255), width=4)
            y = 200
            day_content_lines = [line for line in markdown_to_plaintext(day['content']).split('\n') if not line.strip().startswith('景点介绍：')]
            day_content = '\n'.join(day_content_lines)
            for seg in re.split(r'(?=上午|中午|下午|晚上)', day_content):
                seg = seg.strip()
                if not seg: continue
                m = re.match(r'^(上午|中午|下午|晚上)', seg)
                if m:
                    draw.text((80, y), m.group(1), font=sub_font, fill=(80,120,200,255))
                    y += 40
                    seg = seg[len(m.group(1)):].lstrip()
                if not seg: continue
                time_detail_match = re.match(r'^(\*\*?\d{1,2}:\d{2}-\d{1,2}:\d{2}\*\*?：?[^\n]*)', seg)
                if time_detail_match:
                    time_line = time_detail_match.group(1)
                    draw.text((120, y), time_line, font=sub_font, fill=(40,40,40,255))
                    y += sub_font.size + 8
                    rest_content = seg[len(time_line):].lstrip('\n:：')
                    if rest_content:
                        best_font = small_font
                        y, rest = draw_multiline_text(draw, rest_content, best_font, 160, y, width-240, height-320)
                        while rest:
                            img2 = Image.new('RGBA', (width, height), color=blue_bg)
                            draw2 = ImageDraw.Draw(img2)
                            draw2.text((60, 60), f"{plan_name}·DAY{day['day_num']}(续)", font=title_font, fill=(30,80,180,255))
                            draw2.rounded_rectangle([(40, 160), (width-40, height-80)], radius=60, fill=blue_card, outline=(120,180,240,255), width=4)
                            y2 = 200
                            best_font2 = small_font
                            y2, rest = draw_multiline_text(draw2, rest, best_font2, 160, y2, width-240, height-320)
                            filename2 = f"poster_{uuid.uuid4().hex[:8]}.png"
                            img2.save(os.path.join(out_dir, filename2))
                            posters.append(f"/static/avatars/{filename2}")
                else:
                    best_font = small_font
                    y, rest = draw_multiline_text(draw, seg, best_font, 120, y, width-200, height-320)
                    while rest:
                        img2 = Image.new('RGBA', (width, height), color=blue_bg)
                        draw2 = ImageDraw.Draw(img2)
                        draw2.text((60, 60), f"{plan_name}·DAY{day['day_num']}(续)", font=title_font, fill=(30,80,180,255))
                        draw2.rounded_rectangle([(40, 160), (width-40, height-80)], radius=60, fill=blue_card, outline=(120,180,240,255), width=4)
                        y2 = 200
                        best_font2 = small_font
                        y2, rest = draw_multiline_text(draw2, rest, best_font2, 120, y2, width-200, height-320)
                        filename2 = f"poster_{uuid.uuid4().hex[:8]}.png"
                        img2.save(os.path.join(out_dir, filename2))
                        posters.append(f"/static/avatars/{filename2}")
            filename = f"poster_{uuid.uuid4().hex[:8]}.png"
            img.save(os.path.join(out_dir, filename))
            posters.append(f"/static/avatars/{filename}")

        # 3. 尾页分区自适应分页
        sections = []
        for sec in ['天气信息','费用预估','注意事项','餐饮推荐','住宿推荐']:
            content = plan['sections'].get(sec,'')
            content = markdown_to_plaintext(content)
            if not content: continue
            sections.append((sec, content))
        if not sections:
            continue
        pages = render_sections_paged(draw, sections, font_path, 120, 240, width-200, height-320, 18, 32, sub_font=sub_font)
        for pi, page_blocks in enumerate(pages):
            if os.path.exists(page_bg_path):
                from PIL import Image
                bg_img = Image.open(page_bg_path).convert('RGBA').resize((width, height))
                img = Image.new('RGBA', (width, height))
                img.paste(bg_img, (0, 0))
            else:
                img = Image.new('RGBA', (width, height), color=blue_bg)
            draw = ImageDraw.Draw(img)
            draw.text((60, 100), f"{plan_name}·旅行Tips"+('' if pi==0 else f'(续{pi})'), font=title_font, fill=(30,80,180,255))
            draw.rounded_rectangle([(40, 200), (width-40, height-80)], radius=60, fill=blue_card, outline=(120,180,240,255), width=4)
            y = 240
            for sec_title, lines, font in page_blocks:
                draw.text((80, y), sec_title, font=sub_font, fill=(80,120,200,255))
                y += sub_font.size + 8
                for line in lines:
                    draw.text((120, y), line, font=font, fill=(40,40,40,255))
                    y += font.size + 6
                y += 10
            filename = f"poster_{uuid.uuid4().hex[:8]}_tail.png"
            img.save(os.path.join(out_dir, filename))
            posters.append(f"/static/avatars/{filename}")
    return posters

# 修改generate_posters接口，调用新版手册式生成
@app.route('/api/conversations/<int:conversation_id>/messages/<int:message_id>/generate_posters', methods=['POST'])
@login_required
def generate_posters(conversation_id, message_id):
    """为指定消息生成旅行手册式海报"""
    user_id = session['user_id']
    conversation = conversation_dao.get_conversation_by_id(conversation_id, user_id)
    if not conversation:
        return jsonify({'error': '会话不存在或无权限访问'}), 404
    message = message_dao.get_message_by_id(message_id)
    if not message or message['conversation_id'] != conversation_id:
        return jsonify({'error': '消息不存在'}), 404
    plan_text = filter_sensitive_content(message['content'])
    try:
        posters = generate_handbook_posters_from_markdown(plan_text)
        if not posters:
            return jsonify({'error': '未能识别到有效的旅行方案，请确保AI回复内容包含“# [方案X名称]之旅”等分段标题'}), 400
        message_dao.update_message_posters(message_id, json.dumps(posters, ensure_ascii=False))
        return jsonify({'success': True, 'posters': posters})
    except Exception as e:
        import traceback
        return jsonify({'error': f'生成海报失败: {str(e)}\n{traceback.format_exc()}'})

@app.route('/api/conversations/<int:conversation_id>/posters', methods=['GET'])
@login_required
def get_conversation_posters(conversation_id):
    user_id = session['user_id']
    conversation = conversation_dao.get_conversation_by_id(conversation_id, user_id)
    if not conversation:
        return jsonify({'error': '会话不存在或无权限访问'}), 404
    posters = message_dao.get_conversation_posters(conversation_id)
    if not posters:
        return jsonify({'success': True, 'posters': [], 'msg': '当前对话中没有生成海报'})
    return jsonify({'success': True, 'posters': posters})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 
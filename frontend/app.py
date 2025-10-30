# -*- coding: utf-8 -*-
"""
CALENDAR TOOLS WEB APPLICATION
=============================

Mô tả: Flask web application cho Calendar Tools
Cách hoạt động:
1. Cung cấp giao diện web cho người dùng
2. Tích hợp với backend modules
3. Xử lý HTTP requests và responses
4. Render HTML templates

Thuật toán chính:
- Route handling
- Request processing
- Template rendering
- Error handling

Hướng dẫn sử dụng:
1. Chạy: python3 frontend/app.py
2. Truy cập: http://localhost:5000
3. Sử dụng giao diện web

Ví dụ:
    python3 frontend/app.py
    # Mở browser: http://localhost:5000
"""

import os
import sys
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import datetime, timedelta
import json
import secrets
import requests
import sqlite3


# Add backend directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_dir = os.path.join(os.path.dirname(current_dir), 'backend')
sys.path.append(project_root)
sys.path.append(backend_dir)

# Import backend modules
from core.database_manager import DatabaseManager
from task_management.simple_task_manager import SimpleTaskManager
from notifications.telegram_notifier import TelegramNotifier
from notifications.notification_scheduler import NotificationScheduler
from utils.config_loader import ConfigLoader

# Import Firebase Auth (sau khi thêm module)
from auth.firebase_auth import FirebaseAuth

from shared.middleware.auth_middleware import require_login, require_tool_access, require_permission
from shared.database.user_settings_manager import UserSettingsManager

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'calendar_tools_secret_key_2024'

# Load configuration
try:
    config = ConfigLoader("config/config.json")
    print("✅ Config loaded successfully")

    def get_bot_token() -> str:
        print(f"🔍 Debug: get_bot_token() called")
        print(f"🔍 Debug: config object: {config}")
        try:
            if config:
                print(f"🔍 Debug: config exists, getting telegram section")
                tg = config.get_section('notifications.telegram')
                print(f"🔍 Debug: telegram section: {tg}")
                token = tg.get('bot_token')
                print(f"🔍 Debug: bot_token: {token}")
                if token:
                    return token
            else:
                print(f"🔍 Debug: config is None")
        except Exception as e:
            print(f"🔍 Debug: Exception in get_bot_token: {e}")
            pass
        print(f"🔍 Debug: Returning fallback token")
        return "<FALLBACK_TOKEN>"

except:
    # Fallback config
    config = None
    print("⚠️  Using fallback config")

# Initialize database
if config:
    db_path = config.get_value('database.path', 'database/calendar_tools.db')
else:
    db_path = 'database/calendar_tools.db'

db = DatabaseManager(db_path)

app.config["DB_PATH"] = db_path

# Initialize task manager
task_manager = SimpleTaskManager(db)

# Initialize Telegram notifier
try:
    if config:
        telegram_config = config.get_section('notifications.telegram')
        if telegram_config and telegram_config.get('enabled', False):
            bot_token = telegram_config.get('bot_token', '')
            if bot_token:
                telegram_notifier = TelegramNotifier(bot_token)
                print("✅ Telegram notifier initialized from config")
            else:
                raise ValueError("No bot token in config")
        else:
            raise ValueError("Telegram not enabled in config")
    else:
        raise ValueError("No config available")
except:
    # Fallback: sử dụng token trực tiếp
    bot_token = "8338680403:AAFZPZM2tllQgFNQcVdM2CzZlMRXYsCJxpw"
    telegram_notifier = TelegramNotifier(bot_token)
    print("✅ Telegram notifier initialized with fallback token")

# Initialize notification scheduler
notification_scheduler = NotificationScheduler(db, telegram_notifier)

print("🚀 Starting Calendar Tools Web Application...")
print("📱 Open your browser and go to: http://localhost:5000")

# Initialize Firebase Auth (thêm sau dòng 93)
firebase_auth = None
try:
    if config:
        firebase_config = config.get_section('firebase')
        if firebase_config:
            firebase_auth = FirebaseAuth(firebase_config)
            print("✅ Firebase Auth initialized")
        else:
            print("⚠️  Firebase config not found")
    else:
        print("⚠️  No config available for Firebase")
except Exception as e:
    print(f"⚠️  Firebase init error: {e}")

# Thêm decorator để bảo vệ routes (thêm trước phần Routes)
def require_login(f):
    """Decorator yêu cầu đăng nhập"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Vui lòng đăng nhập để tiếp tục', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

from shared.auth.permission_checker import PermissionChecker
@app.context_processor
def inject_perms():
    uid = session.get('user_id')
    if not uid:
        return dict(can=lambda p: False, is_admin=lambda: False)
    pc = PermissionChecker(app.config.get("DB_PATH", "database/calendar_tools.db"))
    def can(p): return pc.has_permission(uid, p)
    def is_admin():
        groups = pc.get_user_groups(uid)
        return any(g in ('super_admin', 'admin') for g in groups)
    return dict(can=can, is_admin=is_admin)

# Routes
@app.route('/')
def index():
    """Trang chủ"""
    return render_template('index.html')

# Thêm routes authentication (thêm sau route '/' hoặc trước route '/create_simple_task')
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Trang đăng nhập"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not firebase_auth:
            flash('Firebase Auth chưa được cấu hình', 'error')
            return render_template('login.html')
        
        # Đăng nhập
        user = firebase_auth.sign_in_with_email_and_password(email, password)
        
        if user:
            # Lưu thông tin vào session
            session['user_id'] = user['uid']
            session['user_email'] = user['email']
            session['id_token'] = user['id_token']
            
            flash('Đăng nhập thành công!', 'success')
            next_url = request.args.get('next') or url_for('index')
            return redirect(next_url)
        else:
            flash('Email hoặc mật khẩu không đúng', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Trang đăng ký"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Mật khẩu xác nhận không khớp', 'error')
            return render_template('register.html')
        
        if not firebase_auth:
            flash('Firebase Auth chưa được cấu hình', 'error')
            return render_template('register.html')
        
        # Đăng ký
        user = firebase_auth.create_user_with_email_and_password(email, password)
        
        if user:
            # Tự động đăng nhập sau khi đăng ký
            session['user_id'] = user['uid']
            session['user_email'] = user['email']
            session['id_token'] = user['id_token']

            
            db_path = app.config.get("DB_PATH", "database/calendar_tools.db")
            uid = user['localId']  # Firebase UID

            with sqlite3.connect(db_path) as conn:
                # Nhóm mặc định 'member'
                conn.execute(
                    "INSERT OR IGNORE INTO user_groups (group_id, group_name) VALUES (?,?)",
                    ('member','Member')
                )
                conn.execute(
                    "INSERT OR IGNORE INTO user_group_memberships (user_id, group_id) VALUES (?,?)",
                    (uid,'member')
                )
                # Tool calendar-tools + cấp access
                conn.execute(
                    "INSERT OR IGNORE INTO tools (tool_id, tool_name) VALUES (?,?)",
                    ('calendar-tools','Calendar Tools')
                )
                conn.execute(
                    "INSERT OR IGNORE INTO user_tool_access (user_id, tool_id) VALUES (?,?)",
                    (uid,'calendar-tools')
                )
                conn.commit()
            
            flash('Đăng ký thành công!', 'success')
            for pid in ['calendar-tools:task.view','calendar-tools:task.create','calendar-tools:notification.send']:
                conn.execute("INSERT OR IGNORE INTO user_permissions (user_id, permission_id) VALUES (?,?)", (uid, pid))
            conn.commit()
            return redirect(url_for('index'))
        else:
            flash('Lỗi đăng ký. Email có thể đã được sử dụng', 'error')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Đăng xuất"""
    session.clear()
    flash('Đã đăng xuất thành công', 'info')
    return redirect(url_for('index'))

@app.route('/create_simple_task', methods=['GET', 'POST'])
@require_login
@require_tool_access('calendar-tools')
@require_permission('calendar-tools:task.create')
def create_simple_task():
    """Tạo task đơn giản"""
    if request.method == 'POST':
        try:
            # Lấy dữ liệu từ form
            task_data = {
                'title': request.form['title'],
                'description': request.form.get('description', ''),
                'start_date': request.form['start_date'],
                'end_date': request.form['end_date'],
                'deadline': request.form['deadline'],
                'notification_time': request.form.get('notification_time', ''),
                'category': request.form.get('category', 'general'),
                'priority': request.form.get('priority', 'medium'),
                'user_id': session.get('user_id')
            }
            
            # Tạo task
            task_id = task_manager.create_task(task_data)
            
            flash(f'Tác vụ đã được tạo thành công! ID: {task_id}', 'success')
            return redirect(url_for('view_tasks'))
            
        except Exception as e:
            flash(f'Lỗi tạo tác vụ: {str(e)}', 'error')
            return redirect(url_for('create_simple_task'))
    
    return render_template('create_simple_task.html')

@app.route('/profile/settings', methods=['GET', 'POST'])
@require_login
def profile_settings():
    user_id = session.get('user_id')
    settings_mgr = UserSettingsManager(app.config.get("DB_PATH", "database/calendar_tools.db"))

    # Các key global
    global_keys = [
        "display_name", "avatar_url", "phone_number",
        "company", "department", "role_title",
        "email_alt", "telegram_username", "telegram_user_id",
        "zalo_phone", "zalo_user_id", "facebook_profile_url",
        "timezone", "language", "date_format", "time_format", "week_start",
        "notification_channel_priority",
        "notify_via_telegram", "notify_via_zalo", "notify_via_email",
        "quiet_hours_enabled", "quiet_hours_range",
        "daily_digest_enabled", "daily_digest_time",
        "crm_api_key", "crm_endpoint", "ga_property_id", "webhook_url",
        "2fa_enabled", "backup_email", "allowed_ips"
    ]

    # Các key theo tool (calendar-tools)
    calendar_tool_id = "calendar-tools"
    calendar_keys = [
        "default_event_duration", "default_category",
        "notification_lead_time", "auto_add_telegram_reminder"
    ]

    if request.method == 'POST':
        print(f"🔍 Debug: POST request received")
        print(f"🔍 Debug: user_id = {user_id}")
        print(f"🔍 Debug: form data = {dict(request.form)}")
        # Lưu global settings
        for key in global_keys:
            val = request.form.get(key)
            # xử lý checkbox: nếu không có trong form -> off
            if key in ["notify_via_telegram","notify_via_zalo","notify_via_email",
                       "quiet_hours_enabled","daily_digest_enabled","2fa_enabled"]:
                val = "1" if request.form.get(key) == "on" else "0"
            settings_mgr.set_setting(user_id, key, val, tool_id=None)

        # Lưu calendar-tools settings
        for key in calendar_keys:
            val = request.form.get(key)
            if key in ["auto_add_telegram_reminder"]:
                val = "1" if request.form.get(key) == "on" else "0"
            settings_mgr.set_setting(user_id, key, val, tool_id=calendar_tool_id)

        print(f"🔍 Debug: Settings saved successfully")
        flash('Đã lưu cài đặt cá nhân', 'success')
        return redirect(url_for('profile_settings'))

    # GET: load settings hiện tại
    def get_val(key, tool_id=None, default=""):
        val = settings_mgr.get_setting(user_id, key, tool_id=tool_id, default=default) or ""
        print(f"🔍 Debug: get_val({key}, {tool_id}) = {val}")
        return val

    current = {
        # Global
        "display_name": get_val("display_name"),
        "avatar_url": get_val("avatar_url"),
        "phone_number": get_val("phone_number"),
        "company": get_val("company"),
        "department": get_val("department"),
        "role_title": get_val("role_title"),
        "email_alt": get_val("email_alt"),
        "telegram_username": get_val("telegram_username"),
        "telegram_user_id": get_val("telegram_user_id"),
        "zalo_phone": get_val("zalo_phone"),
        "zalo_user_id": get_val("zalo_user_id"),
        "facebook_profile_url": get_val("facebook_profile_url"),

        "timezone": get_val("timezone", default="Asia/Ho_Chi_Minh"),
        "language": get_val("language", default="vi"),
        "date_format": get_val("date_format", default="YYYY-MM-DD"),
        "time_format": get_val("time_format", default="24h"),
        "week_start": get_val("week_start", default="Mon"),
        "notification_channel_priority": get_val("notification_channel_priority", default='["telegram","email","zalo"]'),
        "notify_via_telegram": get_val("notify_via_telegram", default="1"),
        "notify_via_zalo": get_val("notify_via_zalo", default="0"),
        "notify_via_email": get_val("notify_via_email", default="0"),
        "quiet_hours_enabled": get_val("quiet_hours_enabled", default="0"),
        "quiet_hours_range": get_val("quiet_hours_range", default="22:00-07:00"),
        "daily_digest_enabled": get_val("daily_digest_enabled", default="0"),
        "daily_digest_time": get_val("daily_digest_time", default="08:30"),

        "crm_api_key": get_val("crm_api_key"),
        "crm_endpoint": get_val("crm_endpoint"),
        "ga_property_id": get_val("ga_property_id"),
        "webhook_url": get_val("webhook_url"),
        "2fa_enabled": get_val("2fa_enabled","", "0"),
        "backup_email": get_val("backup_email"),
        "allowed_ips": get_val("allowed_ips","", "[]"),
        # Calendar Tools
        "default_event_duration": get_val("default_event_duration", calendar_tool_id, "60"),
        "default_category": get_val("default_category", calendar_tool_id, "work"),
        "notification_lead_time": get_val("notification_lead_time", calendar_tool_id, "30"),
        "auto_add_telegram_reminder": get_val("auto_add_telegram_reminder", calendar_tool_id, "1"),
    }

    return render_template('profile_settings.html', current=current)    

@app.route('/tasks')
@require_login
@require_tool_access('calendar-tools')
@require_permission('calendar-tools:task.view')
def view_tasks():
    """Xem danh sách tasks"""
    try:
        user_id = session.get('user_id')  # Lấy user_id từ session
        tasks = task_manager.get_tasks(user_id=user_id)  # Filter theo user
        return render_template('tasks_list.html', tasks=tasks)
    except Exception as e:
        print(f"❌ Error getting tasks: {e}")
        flash(f'Lỗi lấy danh sách tasks: {str(e)}', 'error')
        return render_template('tasks_list.html', tasks=[])

@app.route('/task/<task_id>')
def view_task_detail(task_id):
    """Xem chi tiết task"""
    try:
        tasks = task_manager.get_tasks()
        task = next((t for t in tasks if t['task_id'] == task_id), None)
        
        if not task:
            flash('Không tìm thấy task', 'error')
            return redirect(url_for('view_tasks'))
        
        return render_template('task_detail.html', task=task)
    except Exception as e:
        flash(f'Lỗi xem chi tiết task: {str(e)}', 'error')
        return redirect(url_for('view_tasks'))

@app.route('/task/<task_id>/update_status', methods=['POST'])
def update_task_status(task_id):
    """Cập nhật trạng thái task"""
    try:
        new_status = request.form.get('status')
        if new_status:
            success = task_manager.update_task_status(task_id, new_status)
            if success:
                flash(f'Trạng thái task đã được cập nhật thành {new_status}', 'success')
            else:
                flash('Lỗi cập nhật trạng thái task', 'error')
    except Exception as e:
        flash(f'Lỗi cập nhật trạng thái: {str(e)}', 'error')
    
    return redirect(url_for('view_task_detail', task_id=task_id))

@app.route('/process_notifications')
def process_notifications():
    """Xử lý notifications đang chờ"""
    try:
        result = notification_scheduler.process_pending_notifications()
        
        if result['status'] == 'success':
            flash(f"Đã xử lý {result['processed']} thông báo, {result['sent']} gửi thành công", 'success')
        else:
            flash(f"Không có thông báo cần xử lý", 'info')
            
    except Exception as e:
        flash(f'Lỗi xử lý thông báo: {str(e)}', 'error')
    
    return redirect(url_for('view_tasks'))

@app.route('/test_notification/<task_id>')
def test_notification(task_id):
    """Test gửi thông báo cho task cụ thể"""
    try:
        # Lấy thông tin task
        tasks = task_manager.get_tasks()
        task = next((t for t in tasks if t['task_id'] == task_id), None)
        
        if not task:
            flash('Không tìm thấy task', 'error')
            return redirect(url_for('view_tasks'))
        
        # Tạo notification test
        notification = {
            'notification_id': f"test_{task_id}_{int(datetime.now().timestamp())}",
            'task_id': task_id,
            'title': task['title'],
            'description': task['description'],
            'deadline': task['deadline'],
            'priority': task['priority']
        }
        
        # Gửi thông báo
        if telegram_notifier:
            # Đảm bảo notification có user_id (ưu tiên từ task, fallback session)
            notification['user_id'] = task.get('user_id') or session.get('user_id')
            sent = notification_scheduler._send_notification(notification)
            if sent:
                flash('Thông báo test đã được gửi qua Telegram!', 'success')
            else:
                flash('Lỗi gửi thông báo test', 'error')
        else:
            flash('Telegram notifier chưa được cấu hình', 'error')
            
    except Exception as e:
        flash(f'Lỗi test thông báo: {str(e)}', 'error')
    
    return redirect(url_for('view_tasks'))

@app.route('/test_telegram')
@require_login
@require_tool_access('calendar-tools')
@require_permission('calendar-tools:notification.send')
def test_telegram():
    """Test gửi tin nhắn Telegram"""
    if not telegram_notifier:
        flash('Telegram notifier chưa được cấu hình', 'error')
        return redirect(url_for('index'))
    
    try:
        # Lấy chat_id từ setting của user hiện tại
        settings_mgr = UserSettingsManager(app.config.get("DB_PATH", "database/calendar_tools.db"))
        current_user = session.get('user_id')
        chat_id = None
        if current_user:
            chat_id = settings_mgr.get_setting(current_user, 'telegram_user_id', tool_id=None)

        if not chat_id:
            flash('Chưa có Telegram User ID trong cài đặt của bạn.', 'warning')
            return redirect(url_for('profile_settings'))

        message = """
    🎉 **TEST TELEGRAM BOT**

    ✅ Bot đang hoạt động bình thường!
    📅 Hệ thống Calendar Tools đã sẵn sàng

    🚀 Truy cập: http://localhost:5000
        """
        success = telegram_notifier.send_message(int(str(chat_id).strip()), message)
        
        if success:
            flash('Tin nhắn Telegram đã được gửi thành công!', 'success')
        else:
            flash('Lỗi gửi tin nhắn Telegram', 'error')
            
    except Exception as e:
        flash(f'Lỗi test Telegram: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/api/tasks')
def api_tasks():
    """API lấy danh sách tasks"""
    try:
        tasks = task_manager.get_tasks()
        return jsonify({
            'status': 'success',
            'data': tasks,
            'count': len(tasks)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/task/<task_id>')
def api_task_detail(task_id):
    """API lấy chi tiết task"""
    try:
        tasks = task_manager.get_tasks()
        task = next((t for t in tasks if t['task_id'] == task_id), None)
        
        if not task:
            return jsonify({
                'status': 'error',
                'error': 'Task not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': task
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/calendar-tools')
@require_login
@require_tool_access('calendar-tools')
def calendar_tools_home():
    """Trang chủ của Calendar Tools"""
    try:
        # Lấy thống kê từ database
        tasks = task_manager.get_tasks()
        
        stats = {
            'total_tasks': len(tasks),
            'completed_tasks': len([t for t in tasks if t.get('status') == 'completed']),
            'pending_tasks': len([t for t in tasks if t.get('status') == 'pending']),
            'overdue_tasks': len([t for t in tasks if t.get('status') == 'overdue'])
        }
        
        return render_template('calendar_tools_home.html', stats=stats)
    except Exception as e:
        print(f"❌ Error loading calendar tools home: {e}")
        return render_template('calendar_tools_home.html', stats={})

@app.route('/admin/users')
@require_login
@require_permission('calendar-tools:task.view')  # hoặc quyền quản trị thực nếu có
def admin_list_users():
    db_path = app.config.get("DB_PATH", "database/calendar_tools.db")
    conn = sqlite3.connect(db_path); conn.row_factory = sqlite3.Row
    users = conn.execute("SELECT * FROM users").fetchall()
    user_infos = []
    for u in users:
        uid = u['user_id']
        uname = u.get('display_name','') or u.get('email','')
        # lấy quyền
        perms = [r[0] for r in conn.execute("SELECT permission_id FROM user_permissions WHERE user_id=?", (uid,))]
        user_infos.append({'user_id': uid, 'name': uname, 'perms': perms})
    conn.close()
    return render_template('admin_users.html', users=user_infos)

@app.route('/admin/groups')
@require_login
@require_permission('calendar-tools:task.view')
def admin_list_groups():
    db_path = app.config.get("DB_PATH", "database/calendar_tools.db")
    conn = sqlite3.connect(db_path); conn.row_factory = sqlite3.Row
    groups = conn.execute("SELECT * FROM user_groups").fetchall()
    group_infos = []
    for g in groups:
        users = conn.execute("SELECT user_id FROM user_group_memberships WHERE group_id=?", (g['group_id'],)).fetchall()
        group_infos.append({
          'group_id': g['group_id'],
          'group_name': g['group_name'],
          'users': [u['user_id'] for u in users]
        })
    conn.close()
    return render_template('admin_groups.html', groups=group_infos)

@app.route('/admin/group_tool_access')
@require_login
@require_permission('calendar-tools:task.view')
def admin_group_tool_access():
    db_path = app.config.get("DB_PATH", "database/calendar_tools.db")
    conn = sqlite3.connect(db_path); conn.row_factory = sqlite3.Row
    groups = conn.execute("SELECT * FROM user_groups").fetchall()
    tools = conn.execute("SELECT * FROM tools").fetchall()
    access = conn.execute("SELECT * FROM group_tool_access").fetchall()
    map_access = {}
    for a in access:
        map_access.setdefault(a['group_id'], set()).add(a['tool_id'])
    conn.close()
    return render_template('admin_group_tools.html', groups=groups, tools=tools, map_access=map_access)

@app.route('/admin/group_permissions')
@require_login
@require_permission('calendar-tools:task.view')  # hoặc 1 quyền hide dành cho admin
def admin_group_permissions():
    db_path = app.config.get("DB_PATH", "database/calendar_tools.db")
    conn = sqlite3.connect(db_path); conn.row_factory = sqlite3.Row

    groups = conn.execute("SELECT * FROM user_groups").fetchall()
    permissions = conn.execute("SELECT * FROM permissions").fetchall()
    perm_map = {}
    for row in conn.execute("SELECT group_id, permission_id FROM group_permissions"):
        perm_map.setdefault(row['group_id'], set()).add(row['permission_id'])
    conn.close()
    return render_template('admin_group_permissions.html', groups=groups, permissions=permissions, perm_map=perm_map)

@app.route('/admin/user/<user_id>/rights', methods=['GET', 'POST'])
@require_login
@require_permission('calendar-tools:task.view')  # hoặc quyền admin
def admin_edit_user_rights(user_id):
    db_path = app.config.get("DB_PATH", "database/calendar_tools.db")
    conn = sqlite3.connect(db_path); conn.row_factory = sqlite3.Row
    # lấy danh sách tool
    tools = conn.execute("SELECT * FROM tools").fetchall()
    # lấy danh sách quyền
    permissions = conn.execute("SELECT * FROM permissions").fetchall()
    # quyền hiện tại user có (trực tiếp)
    has_perms = set([r[0] for r in conn.execute("SELECT permission_id FROM user_permissions WHERE user_id=?", (user_id,))])
    if request.method == "POST":
        ticked = set(request.form.getlist("perms"))
        all_perm_ids = set([p["permission_id"] for p in permissions])
        # Xoá hết quyền cũ
        conn.execute("DELETE FROM user_permissions WHERE user_id=?", (user_id,))
        # Thêm lại quyền theo tick
        for pid in ticked:
            if pid in all_perm_ids:
                conn.execute("INSERT OR IGNORE INTO user_permissions (user_id, permission_id) VALUES (?,?)", (user_id, pid))
        conn.commit()
        return redirect(url_for('admin_list_users'))
    conn.close()
    # group by tool
    tools_by_id = {t['tool_id']: t for t in tools}
    permissions_by_tool = {}
    for p in permissions:
        permissions_by_tool.setdefault(p["tool_id"], []).append(p)
    return render_template('admin_user_matrix.html', user_id=user_id, tools=tools, permissions=permissions, has_perms=has_perms, permissions_by_tool=permissions_by_tool)

@app.route('/admin/user/<user_id>/tools', methods=['GET', 'POST'])
@require_login
@require_permission('calendar-tools:task.view')  # hoặc quyền admin
def admin_edit_user_tools(user_id):
    db_path = app.config.get("DB_PATH", "database/calendar_tools.db")
    conn = sqlite3.connect(db_path); conn.row_factory = sqlite3.Row
    tools = conn.execute("SELECT * FROM tools").fetchall()
    has_tools = set([r[0] for r in conn.execute("SELECT tool_id FROM user_tool_access WHERE user_id=?", (user_id,))])
    if request.method == "POST":
        ticked = set(request.form.getlist("tools"))
        all_tool_ids = set([t["tool_id"] for t in tools])
        # Xoá cũ
        conn.execute("DELETE FROM user_tool_access WHERE user_id=?", (user_id,))
        for tid in ticked:
            if tid in all_tool_ids:
                conn.execute("INSERT OR IGNORE INTO user_tool_access (user_id, tool_id) VALUES (?,?)", (user_id, tid))
        conn.commit()
        return redirect(url_for('admin_list_users'))
    conn.close()
    return render_template('admin_user_tools_matrix.html', user_id=user_id, tools=tools, has_tools=has_tools)

@app.route('/admin/group/<group_id>/tools', methods=['GET', 'POST'])
@require_login
@require_permission('calendar-tools:task.view')
def admin_edit_group_tools(group_id):
    db_path = app.config.get("DB_PATH", "database/calendar_tools.db")
    conn = sqlite3.connect(db_path); conn.row_factory = sqlite3.Row
    tools = conn.execute("SELECT * FROM tools").fetchall()
    has_tools = set([r[0] for r in conn.execute("SELECT tool_id FROM group_tool_access WHERE group_id=?", (group_id,))])
    if request.method == "POST":
        ticked = set(request.form.getlist("tools"))
        all_tool_ids = set([t["tool_id"] for t in tools])
        conn.execute("DELETE FROM group_tool_access WHERE group_id=?", (group_id,))
        for tid in ticked:
            if tid in all_tool_ids:
                conn.execute("INSERT OR IGNORE INTO group_tool_access (group_id, tool_id) VALUES (?,?)", (group_id, tid))
        conn.commit()
        return redirect(url_for('admin_list_groups'))
    conn.close()
    return render_template('admin_group_tools_matrix.html', group_id=group_id, tools=tools, has_tools=has_tools)

@app.route('/admin/group/<group_id>/rights', methods=['GET', 'POST'])
@require_login
@require_permission('calendar-tools:task.view')  # hoặc quyền admin
def admin_edit_group_rights(group_id):
    db_path = app.config.get("DB_PATH", "database/calendar_tools.db")
    conn = sqlite3.connect(db_path); conn.row_factory = sqlite3.Row
    # Lấy danh sách tool và perm
    tools = conn.execute("SELECT * FROM tools").fetchall()
    permissions = conn.execute("SELECT * FROM permissions").fetchall()
    # Quyền hiện tại group đang có
    has_perms = set([r[0] for r in conn.execute("SELECT permission_id FROM group_permissions WHERE group_id=?", (group_id,))])
    if request.method == "POST":
        ticked = set(request.form.getlist("perms"))
        all_perm_ids = set([p["permission_id"] for p in permissions])
        # Xóa quyền cũ
        conn.execute("DELETE FROM group_permissions WHERE group_id=?", (group_id,))
        # Thêm lại quyền theo tick
        for pid in ticked:
            if pid in all_perm_ids:
                conn.execute("INSERT OR IGNORE INTO group_permissions (group_id, permission_id) VALUES (?,?)", (group_id, pid))
        conn.commit()
        return redirect(url_for('admin_list_groups'))
    conn.close()
    permissions_by_tool = {}
    for p in permissions:
        permissions_by_tool.setdefault(p["tool_id"], []).append(p)
    return render_template('admin_group_matrix.html', group_id=group_id, tools=tools, permissions=permissions, has_perms=has_perms, permissions_by_tool=permissions_by_tool)

@app.route('/admin/group/<group_id>/members', methods=['GET', 'POST'])
@require_login
@require_permission('calendar-tools:task.view')
def admin_edit_group_members(group_id):
    db_path = app.config.get("DB_PATH", "database/calendar_tools.db")
    conn = sqlite3.connect(db_path); conn.row_factory = sqlite3.Row
    users = conn.execute("SELECT * FROM users").fetchall()
    has_users = set([r[0] for r in conn.execute("SELECT user_id FROM user_group_memberships WHERE group_id=?", (group_id,))])
    if request.method == "POST":
        ticked = set(request.form.getlist("users"))
        all_user_ids = set([u["user_id"] for u in users])
        conn.execute("DELETE FROM user_group_memberships WHERE group_id=?", (group_id,))
        for uid in ticked:
            if uid in all_user_ids:
                conn.execute("INSERT OR IGNORE INTO user_group_memberships (user_id, group_id) VALUES (?,?)", (uid, group_id))
        conn.commit()
        return redirect(url_for('admin_list_groups'))
    conn.close()
    return render_template('admin_group_members_matrix.html', group_id=group_id, users=users, has_users=has_users)

@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

if __name__ == '__main__':
    if config:
        app.run(
            host=config.get_value('app.host', '0.0.0.0'),
            port=config.get_value('app.port', 5000),
            debug=config.get_value('app.debug', True)
        )
    else:
        app.run(host='0.0.0.0', port=5000, debug=True)
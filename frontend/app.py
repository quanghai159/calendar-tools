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
    return render_template('index_adminlte.html')

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
        
        if user and (user.get('uid') or user.get('localId')):
            session['user_id'] = user.get('uid') or user.get('localId')
            session['user_email'] = user.get('email')
            session['id_token'] = user.get('idToken') or user.get('id_token') or None

            # Upsert hồ sơ user vào bảng users
            db_path = app.config.get("DB_PATH", "database/calendar_tools.db")
            uid = user.get('uid') or user.get('localId')
            email_val = user.get('email', '')
            display_name = (email_val.split('@')[0] if email_val else uid)

            with sqlite3.connect(db_path) as conn:
                conn.execute("""
                    INSERT INTO users (user_id, display_name, email, phone_number, created_at, updated_at)
                    VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
                    ON CONFLICT(user_id) DO UPDATE SET
                        display_name = excluded.display_name,
                        email        = excluded.email,
                        phone_number = COALESCE(excluded.phone_number, phone_number),
                        updated_at   = datetime('now')
                """, (uid, display_name, email_val, None))
                conn.commit()
            
            flash('Đăng nhập thành công!', 'success')
            next_url = request.args.get('next') or url_for('index')
            return redirect(next_url)
        else:
            flash('Email hoặc mật khẩu không đúng', 'error')
            return render_template('login.html')
    
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

        # **Nếu user trả về lỗi hoặc thiếu trường, return luôn**
        if not user or not ('localId' in user or 'uid' in user):
            flash('Lỗi đăng ký. Email có thể đã được sử dụng', 'error')
            return render_template('register.html')
        # Đảm bảo không truy cập user['id_token'], dùng get
        session['user_id'] = user.get('uid') or user.get('localId')
        session['user_email'] = user.get('email')
        session['id_token'] = user.get('idToken') or user.get('id_token') or None

        # Upsert hồ sơ user vào bảng users sau đăng ký
        db_path = app.config.get("DB_PATH", "database/calendar_tools.db")
        uid = user.get('localId') or user.get('uid')
        email_val = user.get('email', '')
        display_name = (email_val.split('@')[0] if email_val else uid)
        with sqlite3.connect(db_path) as conn:
            conn.execute("""
                INSERT INTO users (user_id, display_name, email, phone_number, created_at, updated_at)
                VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
                ON CONFLICT(user_id) DO UPDATE SET
                    display_name = excluded.display_name,
                    email        = excluded.email,
                    phone_number = COALESCE(excluded.phone_number, phone_number),
                    updated_at   = datetime('now')
            """, (uid, display_name, email_val, None))
            # Gán nhóm user/tool/quyền mặc định
            conn.execute(
                "INSERT OR IGNORE INTO user_group_memberships (user_id, group_id) VALUES (?,?)",
                (uid,'user')  # Dùng 'user' thay vì 'member'
            )
            conn.execute(
                "INSERT OR IGNORE INTO tools (tool_id, tool_name) VALUES (?,?)",
                ('calendar-tools','Calendar Tools')
            )
            conn.execute(
                "INSERT OR IGNORE INTO user_tool_access (user_id, tool_id) VALUES (?,?)",
                (uid,'calendar-tools')
            )
            for pid in ['calendar-tools:task.view','calendar-tools:task.create','calendar-tools:notification.send']:
                conn.execute("INSERT OR IGNORE INTO user_permissions (user_id, permission_id) VALUES (?,?)", (uid, pid))
            conn.commit()
        flash('Đăng ký thành công!', 'success')
        return redirect(url_for('index'))
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
        "2fa_enabled", "backup_email", "allowed_ips",
        "notif_label_1","notif_label_2","notif_label_3","notif_label_4",
        "notif_label_5","notif_label_6","notif_label_7","notif_label_8"
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
        
        # Đồng bộ display_name, phone_number vào bảng users (luôn sync)
        db_path = app.config.get("DB_PATH", "database/calendar_tools.db")
        display_name_val = request.form.get('display_name', '').strip()
        phone_number_val = request.form.get('phone_number', '').strip()

        # Luôn sync với users table (kể cả empty)
        with sqlite3.connect(db_path) as conn:
            conn.execute("""
                UPDATE users 
                SET display_name = ?,
                    phone_number = ?,
                    updated_at = datetime('now')
                WHERE user_id = ?
            """, (
                display_name_val if display_name_val else None,
                phone_number_val if phone_number_val else None,
                user_id
            ))
            conn.commit()
        
        if display_name_val or phone_number_val:
            with sqlite3.connect(db_path) as conn:
                # Lấy giá trị hiện tại từ users table
                user_row = conn.execute("SELECT display_name, phone_number FROM users WHERE user_id = ?", (user_id,)).fetchone()
                current_display_name = user_row[0] if user_row and user_row[0] else None
                current_phone = user_row[1] if user_row and user_row[1] else None
                
                # Chỉ update nếu có thay đổi
                if display_name_val or phone_number_val:
                    conn.execute("""
                        UPDATE users 
                        SET display_name = COALESCE(?, display_name),
                            phone_number = COALESCE(?, phone_number),
                            updated_at = datetime('now')
                        WHERE user_id = ?
                    """, (
                        display_name_val if display_name_val else None,
                        phone_number_val if phone_number_val else None,
                        user_id
                    ))
                    conn.commit()

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

        # Notification column labels (per-user)
        "notif_label_1": get_val("notif_label_1", default="Thông báo 1"),
        "notif_label_2": get_val("notif_label_2", default="Thông báo 2"),
        "notif_label_3": get_val("notif_label_3", default="Thông báo 3"),
        "notif_label_4": get_val("notif_label_4", default="Thông báo 4"),
        "notif_label_5": get_val("notif_label_5", default="Thông báo 5"),
        "notif_label_6": get_val("notif_label_6", default="Thông báo 6"),
        "notif_label_7": get_val("notif_label_7", default="Thông báo 7"),
        "notif_label_8": get_val("notif_label_8", default="Thông báo 8"),
    }

    return render_template('profile_settings.html', current=current)    

@app.route('/tasks')
@require_login
@require_tool_access('calendar-tools')
@require_permission('calendar-tools:task.view')
def view_tasks():
    """Xem danh sách tasks"""
    try:
        user_id = session.get('user_id')
        settings_mgr = UserSettingsManager(app.config.get("DB_PATH","database/calendar_tools.db"))
        notif_labels = []
        for i in range(1,9):
            notif_labels.append(settings_mgr.get_setting(user_id, f'notif_label_{i}', tool_id=None, default=f'Thông báo {i}') or f'Thông báo {i}')  # Lấy user_id từ session
        tasks = task_manager.get_tasks(user_id=user_id)  # Filter theo user
        return render_template('tasks_list.html', tasks=tasks, notif_labels=notif_labels)
    except Exception as e:
        print(f"❌ Error getting tasks: {e}")
        flash(f'Lỗi lấy danh sách tasks: {str(e)}', 'error')
        return render_template('tasks_list.html', tasks=[],notif_labels=notif_labels)

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

@app.route('/reports/tasks')
@require_login
@require_tool_access('calendar-tools')
@require_permission('calendar-tools:task.view')
def report_tasks():
    from datetime import datetime, timedelta
    import sqlite3

    user_id = session.get('user_id')
    db_path = app.config.get("DB_PATH","database/calendar_tools.db")

    # Lấy tham số lọc
    days = int(request.args.get('days', 7))  # mặc định 7 ngày tới
    status = request.args.get('status', '').strip()
    keyword = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()

    now = datetime.now()
    end = now + timedelta(days=days)

    # Các cột thời điểm thông báo cần xét
    time_cols = ["notification_time","notif1","notif2","notif3","notif4","notif5","notif6","notif7","notif8"]

    # Điều kiện: cột có giá trị, >= now, <= end
    win_cond = " OR ".join([
        f"({c} IS NOT NULL AND {c} != '' AND datetime(replace({c}, 'T',' ')) >= ? AND datetime(replace({c}, 'T',' ')) <= ?)"
        for c in time_cols
    ])

    where = ["user_id = ?"]
    params = [user_id]

    # Bổ sung lọc tùy chọn (đặt trước)
    if status:
        where.append("status = ?")
        params.append(status)
    if category:
        where.append("category = ?")
        params.append(category)
    if keyword:
        where.append("(title LIKE ? OR description LIKE ?)")
        params.extend([f"%{keyword}%", f"%{keyword}%"])

    # Tham số cho các cột notification/time
    now_s = now.strftime('%Y-%m-%d %H:%M:%S')
    end_s = end.strftime('%Y-%m-%d %H:%M:%S')
    for _ in time_cols:
        params.extend([now_s, end_s])

    sql = f"""
    SELECT *
    FROM tasks
    WHERE {" AND ".join(where)} AND ({win_cond})
    ORDER BY datetime(replace(COALESCE(notification_time, notif1, notif2, notif3, notif4, notif5, notif6, notif7, notif8), 'T',' ')) ASC
    LIMIT 500
    """

    # Lấy nhãn 8 cột từ settings (dùng lại như /tasks)
    settings_mgr = UserSettingsManager(app.config.get("DB_PATH","database/calendar_tools.db"))
    notif_labels = []
    for i in range(1,9):
        lbl = settings_mgr.get_setting(user_id, f'notif_label_{i}', tool_id=None, default=f'Thông báo {i}') or f'Thông báo {i}'
        notif_labels.append(lbl)

    # Query
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, tuple(params)).fetchall()
            tasks = [dict(r) for r in rows]
    except Exception as e:
        print(f"❌ Report query error: {e}")
        tasks = []

    from datetime import datetime

    def parse_dt(s):
        if not s:
            return None
        s = str(s).strip().replace('T', ' ')
        # thử nhiều format phổ biến
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(s, fmt)
            except:
                pass
        return None

    hit_cols = ["notification_time","notif1","notif2","notif3","notif4","notif5","notif6","notif7","notif8"]
    now_dt = now
    end_dt = end
    urgent_dt = now + timedelta(days=3)

    for t in tasks:
        t["_hits"] = set()
        t["_urgent"] = set()
        for col in hit_cols:
            dt = parse_dt(t.get(col))
            if dt and now_dt <= dt <= end_dt:
                t["_hits"].add(col)
                if dt <= urgent_dt:
                    t["_urgent"].add(col)    

    return render_template('report_tasks.html',
                           tasks=tasks,
                           notif_labels=notif_labels,
                           days=days,
                           q=keyword,
                           status=status,
                           category=category)

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

@app.route('/api/task', methods=['POST'])
def api_create_task():
    try:
        data = request.get_json() or {}
        task_id = task_manager.create_task({
            'title': data.get('title','').strip(),
            'description': data.get('description',''),
            'start_date': data.get('start_date',''),
            'end_date': data.get('end_date',''),
            'deadline': data.get('deadline',''),
            'notification_time': data.get('notification_time',''),
            'notif1': data.get('notif1',''), 'notif2': data.get('notif2',''),
            'notif3': data.get('notif3',''), 'notif4': data.get('notif4',''),
            'notif5': data.get('notif5',''), 'notif6': data.get('notif6',''),
            'notif7': data.get('notif7',''), 'notif8': data.get('notif8',''),
            'user_id': session.get('user_id'),
            'category': 'general',
            'priority': 'medium'
        })
        return jsonify(status='success', message='Tạo tác vụ thành công!', task_id=task_id)
    except Exception as e:
        return jsonify(status='error', message=str(e)), 400

@app.route('/api/task/<task_id>/test_notification', methods=['POST'])
def api_test_notification(task_id):
    try:
        # copy toàn bộ logic từ test_notification ở trên
        # nhưng thay vì flash + redirect, trả về JSON trạng thái
        tasks = task_manager.get_tasks()
        task = next((t for t in tasks if t['task_id'] == task_id), None)
        if not task:
            return jsonify(status='error', message='Không tìm thấy task'), 404
        notification = {
            'notification_id': f"test_{task_id}_{int(datetime.now().timestamp())}",
            'task_id': task_id,
            'title': task['title'],
            'description': task['description'],
            'deadline': task['deadline'],
            'priority': task['priority'],
        }
        if telegram_notifier:
            notification['user_id'] = task.get('user_id') or session.get('user_id')
            sent = notification_scheduler._send_notification(notification)
            if sent:
                return jsonify(status='success', message='Thông báo test đã được gửi qua Telegram!')
            else:
                return jsonify(status='error', message='Lỗi gửi thông báo test')
        else:
            return jsonify(status='error', message='Telegram notifier chưa được cấu hình')
    except Exception as e:
        return jsonify(status='error', message=f'Lỗi test thông báo: {str(e)}'), 500

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

@app.route('/api/task/<task_id>', methods=['POST'])
def api_update_task(task_id):
    try:
        data = request.get_json() or {}
        ok = task_manager.update_task(task_id, data)
        if ok:
            return jsonify(status='success', message='Đã lưu tác vụ!')
        return jsonify(status='error', message='Không có thay đổi hoặc không tìm thấy bản ghi')
    except Exception as e:
        return jsonify(status='error', message=str(e)), 500

@app.route('/api/task/<task_id>', methods=['DELETE'])
def api_delete_task(task_id):
    try:
        import sqlite3
        db_path = app.config.get("DB_PATH","database/calendar_tools.db")
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
            conn.commit()
            if cur.rowcount > 0:
                return jsonify(status='success', message='Đã xóa tác vụ!')
            return jsonify(status='error', message='Không tìm thấy tác vụ')
    except Exception as e:
        return jsonify(status='error', message=str(e)), 500

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
@require_permission('calendar-tools:task.view')
def admin_list_users():
    db_path = app.config.get("DB_PATH", "database/calendar_tools.db")
    conn = sqlite3.connect(db_path); conn.row_factory = sqlite3.Row
    users = conn.execute("SELECT * FROM users").fetchall()
    user_infos = []
    for u in users:
        # Kiểm tra trả về name/email/sdt hoặc user_id
        uname = u['display_name'] or u['email'] or u['phone_number'] or u['user_id']
        perms = [r[0] for r in conn.execute("SELECT permission_id FROM user_permissions WHERE user_id=?", (u['user_id'],))]
        user_infos.append({'user_id': u['user_id'], 'name': uname, 'perms': perms})
    conn.close()
    return render_template('admin_users.html', users=user_infos)

@app.route('/admin/groups')
@require_login
@require_permission('calendar-tools:task.view')
def admin_list_groups():
    import sqlite3
    db_path = app.config.get("DB_PATH", "database/calendar_tools.db")
    conn = sqlite3.connect(db_path); conn.row_factory = sqlite3.Row

    groups = conn.execute("SELECT group_id, group_name FROM user_groups ORDER BY group_id").fetchall()
    group_infos = []
    for g in groups:
        members = conn.execute("""
            SELECT m.user_id,
                    COALESCE(u.display_name, u.email, u.phone_number, m.user_id) AS label,
                    u.email, u.phone_number
            FROM user_group_memberships m
            LEFT JOIN users u ON u.user_id = m.user_id
            WHERE m.group_id=?
            ORDER BY label
        """, (g['group_id'],)).fetchall()
        member_labels = [
            (
                (m['label'] if m['label'] else m['user_id'])
                + (f" ({m['email']})" if m['email'] else '')
                + (f" [{m['phone_number']}]" if m['phone_number'] else '')
            ).strip()
            for m in members
            ]
        group_infos.append({
            'group_id': g['group_id'],
            'group_name': g['group_name'],
            'users': member_labels
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
    import sqlite3
    db_path = app.config.get("DB_PATH", "database/calendar_tools.db")
    conn = sqlite3.connect(db_path); conn.row_factory = sqlite3.Row

    # Lấy danh sách users (id, display_name, email, phone_number)
    users = conn.execute("""
        SELECT user_id, 
               COALESCE(display_name, '') AS display_name,
               COALESCE(email, '') AS email,
               COALESCE(phone_number, '') AS phone_number
        FROM users
        ORDER BY COALESCE(display_name, email, phone_number, user_id)
    """).fetchall()

    # Thành viên hiện có trong nhóm
    has_users = set(r[0] for r in conn.execute(
        "SELECT user_id FROM user_group_memberships WHERE group_id=?", (group_id,)
    ).fetchall())

    if request.method == "POST":
        ticked = set(request.form.getlist("users"))  # danh sách user_id được tick
        all_user_ids = set(u["user_id"] for u in users)
        conn.execute("DELETE FROM user_group_memberships WHERE group_id=?", (group_id,))
        for uid in ticked:
            if uid in all_user_ids:
                conn.execute(
                    "INSERT OR IGNORE INTO user_group_memberships (user_id, group_id) VALUES (?,?)",
                    (uid, group_id)
                )
        conn.commit()
        conn.close()
        return redirect(url_for('admin_list_groups'))

    conn.close()
    return render_template('admin_group_members_matrix.html',
                           group_id=group_id, users=users, has_users=has_users)

@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

if __name__ == '__main__':
    if config:
        app.run(
            host=config.get_value('app.host', '0.0.0.0'),
            port=config.get_value('app.port', 5001),
            debug=config.get_value('app.debug', True)
        )
    else:
        app.run(host='0.0.0.0', port=5001, debug=True)
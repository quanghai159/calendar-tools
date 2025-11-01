🚀 CHẠY HỆ THỐNG TỰ ĐỘNG
Bây giờ hãy chạy hệ thống tự động để nhận thông báo theo lịch:

cd "/Users/AmyNguyen/Desktop/Cursor AI MKT/calendar-tools"

Terminal 1 - Web App:
python3 frontend/app.py

Terminal 2 - Auto Notification Runner:
python3 auto_notification_runner.py

🧪 CHẠY TEST 30 GIÂY
python3 test_30_second_notification.py

http://localhost:5000/


# Hunonic Marketing Tools - Calendar Tools

## 📋 Mô tả
Hệ thống quản lý lịch và tác vụ với thông báo tự động qua Telegram/Zalo/Email, tích hợp với Firebase Authentication và hệ thống phân quyền chi tiết.

---

## 📁 Cấu trúc thư mục
calendar-tools/
├── backend/ # Backend modules
│ ├── auth/ # Firebase Authentication
│ ├── core/ # Core modules (database, calendar)
│ ├── notifications/ # Notification handlers
│ ├── task_management/ # Task management
│ └── utils/ # Utilities
├── frontend/ # Flask web app
│ ├── app.py # Main Flask application
│ ├── templates/ # Jinja2 templates
│ └── static/ # CSS, JS, images
├── shared/ # Shared modules
│ ├── auth/ # Permission checking
│ ├── database/ # Database managers
│ └── middleware/ # Flask middleware
├── migrations/ # Database migrations
├── config/ # Configuration files
├── database/ # SQLite database files
└── logs/ # Log files


---

## 🚀 Hướng dẫn Setup

### 1. Cài đặt dependencies

```bash
# Tạo virtual environment (nếu chưa có)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate  # Windows

# Cài đặt packages
pip install -r requirements.txt
```

### 2. Cấu hình

Chỉnh sửa `config/config.json`:
- Database path
- Firebase credentials
- Telegram bot token
- SMTP settings (nếu dùng email)

### 3. Chạy migrations

```bash
# Chạy tất cả migrations
python3 migrations/run_all_migrations.py
```

### 4. Chạy ứng dụng

#### Local Development:

**Terminal 1 - Web App:**
```bash
python3 frontend/app.py
```

**Terminal 2 - Auto Notification Runner:**
```bash
python3 auto_notification_runner.py
```

#### Production với PM2:

```bash
# Start tất cả services
pm2 start ecosystem.config.js

# Hoặc start từng service
pm2 start ecosystem.config.js --only calendar-tools
pm2 start ecosystem.config.js --only auto-notification-runner
```

---

## 🔧 Các lệnh thường dùng

### Git Commands

```bash
# Kiểm tra status
git status

# Add tất cả thay đổi
git add .

# Commit
git commit -m "Update mới nhất"

# Push lên GitHub
git push origin main

# Pull trên VPS
git pull origin main
```

### PM2 Commands

```bash
# Xem danh sách processes
pm2 list

# Xem logs
pm2 logs
pm2 logs calendar-tools
pm2 logs auto-notification-runner
pm2 logs --lines 100  # Last 100 lines

# Restart services
pm2 restart calendar-tools
pm2 restart auto-notification-runner
pm2 restart all

# Reload (zero-downtime)
pm2 reload calendar-tools
pm2 reload all

# Stop/Start
pm2 stop calendar-tools
pm2 start calendar-tools

# Delete process
pm2 delete calendar-tools

# Monitor realtime
pm2 monit

# Thông tin chi tiết
pm2 info calendar-tools

# Lưu cấu hình
pm2 save

# Setup startup (chạy khi server reboot)
pm2 startup
# Copy command được hiển thị và chạy với sudo
```

### Database Commands

```bash
# Backup database
cp database/calendar_tools.db database/calendar_tools.db.backup.$(date +%Y%m%d_%H%M%S)

# Kiểm tra database
sqlite3 database/calendar_tools.db ".tables"
sqlite3 database/calendar_tools.db "SELECT COUNT(*) FROM tasks;"

# Restore từ backup
cp database/calendar_tools.db.backup.XXXXXX database/calendar_tools.db
```

---

## 🔍 Scripts kiểm tra và fix bug

### Database Integrity Scripts

#### 1. `check_database_integrity.py`
Kiểm tra tính toàn vẹn database (users, groups, permissions, settings)

```bash
python3 check_database_integrity.py
```

**Kiểm tra:**
- Users table (display_name, email, phone_number)
- User groups và memberships
- User permissions và group permissions
- User tool access và group tool access
- User settings (trùng lặp)

---

#### 2. `check_tasks_integrity.py`
Kiểm tra tính toàn vẹn tasks, events, notifications

```bash
python3 check_tasks_integrity.py
```

**Kiểm tra:**
- Tasks không có user_id
- Tasks có user_id không tồn tại
- Calendar events orphaned (không có task)
- Notifications orphaned (không có task)
- Thống kê theo user

---

### Fix Scripts

#### 3. `cleanup_user_settings.py`
Xóa duplicates trong user_settings table

```bash
python3 cleanup_user_settings.py
```

**Làm gì:**
- Tìm các bản ghi trùng lặp (cùng user_id, tool_id, setting_key)
- Giữ lại bản ghi có `updated_at` mới nhất
- Xóa các bản ghi cũ

---

#### 4. `fix_database_sync.py`
Sync users table với user_settings và migrate group 'member'

```bash
python3 fix_database_sync.py
```

**Làm gì:**
- Migrate users từ group 'member' → 'user'
- Sync display_name, phone_number từ user_settings vào users table
- Xóa group memberships với group 'member'

---

#### 5. `fix_tasks_integrity.py`
Fix tasks không có user_id và orphaned notifications

```bash
python3 fix_tasks_integrity.py
```

**Làm gì:**
- Hỏi cách xử lý tasks không có user_id:
  - A) Xóa tất cả
  - B) Gán user (chọn user)
  - C) Bỏ qua
- Xóa orphaned notifications (không có task)
- Sync user_id cho calendar_events từ tasks

---

### Permission Scripts

#### 6. `inspect_permissions.py`
Kiểm tra permissions của một user

```bash
python3 inspect_permissions.py <user_id>
```

**Ví dụ:**
```bash
python3 inspect_permissions.py CL54mVGb6HVjKwDFtnOZquuF8ax2
```

**Hiển thị:**
- User info
- Groups user thuộc
- Tool access
- Permissions (từ groups và direct)

---

#### 7. `grant_revoke.py`
Grant/Revoke permissions cho user

```bash
python3 grant_revoke.py <user_id> <action> <target> <id>
```

**Ví dụ:**
```bash
# Grant permission
python3 grant_revoke.py CL54mVGb6HVjKwDFtnOZquuF8ax2 grant permission calendar-tools:task.view

# Revoke permission
python3 grant_revoke.py CL54mVGb6HVjKwDFtnOZquuF8ax2 revoke permission calendar-tools:task.view
```

---

### Migration Scripts

#### 8. `migrations/run_all_migrations.py`
Chạy tất cả migrations

```bash
python3 migrations/run_all_migrations.py
```

**Chạy theo thứ tự:**
1. `001_run_all.py` - Tạo các bảng
2. `002_seed_default_data.py` - Seed default data

---

## 🐛 Troubleshooting

### Lỗi thường gặp

#### 1. "ModuleNotFoundError"
```bash
# Kiểm tra virtual environment
which python3
python3 --version

# Reinstall dependencies
pip install -r requirements.txt
```

#### 2. "Database is locked"
```bash
# Kiểm tra xem có process nào đang dùng database không
lsof database/calendar_tools.db

# Hoặc restart services
pm2 restart all
```

#### 3. "Notification không được gửi"
```bash
# Kiểm tra logs
pm2 logs auto-notification-runner --lines 100

# Kiểm tra Telegram bot token
grep "bot_token" config/config.json

# Test Telegram bot
python3 test_telegram_bot.py

# Kiểm tra user có telegram_user_id trong settings không
sqlite3 database/calendar_tools.db "SELECT user_id, setting_value FROM user_settings WHERE setting_key='telegram_user_id' AND tool_id IS NULL;"
```

#### 4. "Permission denied"
```bash
# Kiểm tra quyền user
python3 inspect_permissions.py <user_id>

# Kiểm tra user có trong group nào
sqlite3 database/calendar_tools.db "SELECT * FROM user_group_memberships WHERE user_id='<user_id>';"
```

#### 5. "Tasks không hiển thị"
```bash
# Kiểm tra tasks có user_id không
python3 check_tasks_integrity.py

# Fix nếu cần
python3 fix_tasks_integrity.py
```

#### 6. "Thông báo hiển thị sai tên cột"
```bash
# Kiểm tra user settings có notif_label_X không
sqlite3 database/calendar_tools.db "SELECT * FROM user_settings WHERE setting_key LIKE 'notif_label_%' AND user_id='<user_id>';"

# Kiểm tra notification_id format
sqlite3 database/calendar_tools.db "SELECT notification_id FROM notifications LIMIT 5;"
```

---

## 📊 Kiểm tra hệ thống

### Quick Health Check

```bash
# Check PM2 processes
pm2 list

# Check database exists
ls -lh database/calendar_tools.db

# Check pending notifications
python3 -c "import sqlite3; conn = sqlite3.connect('database/calendar_tools.db'); print('Pending:', conn.execute('SELECT COUNT(*) FROM notifications WHERE status=\"pending\"').fetchone()[0]); conn.close()"

# Check recent errors
tail -20 logs/pm2-error.log
```

### Full Health Check Script

```bash
#!/bin/bash
echo "🔍 Health Check - Calendar Tools"
echo "================================"

echo -e "\n📊 PM2 Processes:"
pm2 list

echo -e "\n💾 Database:"
if [ -f "database/calendar_tools.db" ]; then
    echo "✅ Database exists"
    DB_SIZE=$(du -h database/calendar_tools.db | cut -f1)
    echo "   Size: $DB_SIZE"
else
    echo "❌ Database not found!"
fi

echo -e "\n🔔 Pending Notifications:"
python3 -c "
import sqlite3
conn = sqlite3.connect('database/calendar_tools.db')
count = conn.execute('SELECT COUNT(*) FROM notifications WHERE status=\"pending\"').fetchone()[0]
print(f'   Pending: {count}')
conn.close()
"

echo -e "\n📝 Recent Errors (last 3):"
tail -3 logs/pm2-error.log 2>/dev/null || echo "   No errors"

echo -e "\n✅ Health check complete!"
```

Lưu thành `health_check.sh` và chạy: `chmod +x health_check.sh && ./health_check.sh`

---

## 🔄 Quy trình Update lên VPS

### 1. Local - Commit và Push

```bash
cd "/Users/AmyNguyen/Desktop/Cursor AI MKT/calendar-tools"

# Kiểm tra status
git status

# Add và commit
git add .
git commit -m "Mô tả thay đổi"

# Push lên GitHub
git push origin main
```

### 2. VPS - Pull và Restart

```bash
cd ~/calendar-tools  # hoặc /root/calendar-tools

# Backup database (QUAN TRỌNG!)
cp database/calendar_tools.db database/calendar_tools.db.backup.$(date +%Y%m%d_%H%M%S)

# Pull code
git pull origin main

# Restart services
pm2 reload ecosystem.config.js

# Hoặc restart từng service
pm2 reload calendar-tools
pm2 reload auto-notification-runner

# Kiểm tra logs
pm2 logs --lines 50
```

---

## 📝 File thường dùng

### Configuration
- `config/config.json` - Main configuration
- `ecosystem.config.js` - PM2 configuration

### Database
- `database/calendar_tools.db` - SQLite database
- `migrations/` - Database migration scripts

### Check Scripts
- `check_database_integrity.py` - Check database integrity
- `check_tasks_integrity.py` - Check tasks integrity

### Fix Scripts
- `cleanup_user_settings.py` - Cleanup duplicates in user_settings
- `fix_database_sync.py` - Fix database sync issues
- `fix_tasks_integrity.py` - Fix tasks without user_id

### Permission Scripts
- `inspect_permissions.py` - Inspect user permissions
- `grant_revoke.py` - Grant/revoke permissions

### Logs
- `logs/pm2-error.log` - PM2 error logs
- `logs/pm2-out.log` - PM2 output logs
- `logs/pm2-notification-error.log` - Notification errors
- `logs/pm2-notification-out.log` - Notification output

---

## 🎯 Workflow thường dùng

### Khi có bug database

```bash
# 1. Check database integrity
python3 check_database_integrity.py

# 2. Check tasks integrity
python3 check_tasks_integrity.py

# 3. Fix nếu cần
python3 cleanup_user_settings.py
python3 fix_database_sync.py
python3 fix_tasks_integrity.py

# 4. Check lại
python3 check_database_integrity.py
python3 check_tasks_integrity.py
```

### Khi notification không hoạt động

```bash
# 1. Check PM2 processes
pm2 list
pm2 logs auto-notification-runner --lines 100

# 2. Check pending notifications
python3 -c "import sqlite3; conn = sqlite3.connect('database/calendar_tools.db'); print('Pending:', conn.execute('SELECT COUNT(*) FROM notifications WHERE status=\"pending\"').fetchone()[0]); conn.close()"

# 3. Test Telegram bot
python3 test_telegram_bot.py

# 4. Check user telegram_id
sqlite3 database/calendar_tools.db "SELECT user_id, setting_value FROM user_settings WHERE setting_key='telegram_user_id' AND tool_id IS NULL;"
```

### Khi cần update code lên VPS

```bash
# Local
git add .
git commit -m "Mô tả"
git push origin main

# VPS
cd ~/calendar-tools
cp database/calendar_tools.db database/calendar_tools.db.backup.$(date +%Y%m%d_%H%M%S)
git pull origin main
pm2 reload ecosystem.config.js
pm2 logs --lines 50
```

---

## 🔐 Security Notes

1. **Không commit credentials**: Kiểm tra `.gitignore` có ignore `config/config.json` nếu có credentials nhạy cảm
2. **Backup trước khi fix**: Luôn backup database trước khi chạy fix scripts
3. **Kiểm tra permissions**: Dùng `inspect_permissions.py` trước khi cấp quyền cho user mới
4. **Secret key**: Đặt strong secret key cho Flask session trong production

---

## 📞 Support

Nếu gặp vấn đề:

1. **Kiểm tra logs**: `pm2 logs --lines 100`
2. **Chạy health check**: `./health_check.sh`
3. **Chạy integrity scripts**: `check_database_integrity.py`, `check_tasks_integrity.py`
4. **Xem troubleshooting section**: Phía trên

---

## 📅 Changelog

### Version 1.0
- ✅ Firebase Authentication
- ✅ Task management với notif1-8
- ✅ Auto notifications qua Telegram (với scheduled_time)
- ✅ Hiển thị tên cột từ user settings trong notifications
- ✅ Permission system (RBAC)
- ✅ User settings management
- ✅ Database integrity scripts
- ✅ PM2 deployment support
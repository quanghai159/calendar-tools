# check_tasks_integrity.py
# -*- coding: utf-8 -*-
"""
Script kiểm tra dữ liệu tasks trong database và so sánh với frontend
"""
import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime

# Lấy đường dẫn database từ config
config_path = Path(__file__).parent / "config" / "config.json"
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

db_path = config['database']['path']
if not os.path.isabs(db_path):
    db_path = Path(__file__).parent / db_path

print(f"📂 Database path: {db_path}")
print(f"📂 Database exists: {os.path.exists(db_path)}\n")

if not os.path.exists(db_path):
    print("❌ Database không tồn tại!")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# Helper function để lấy giá trị từ sqlite3.Row
def get_row_value(row, key, default=None):
    """Lấy giá trị từ sqlite3.Row với default value"""
    if key in row.keys():
        value = row[key]
        return value if value is not None and value != '' else default
    return default

print("=" * 80)
print("📊 KIỂM TRA TASKS DATABASE")
print("=" * 80)

# 1. Kiểm tra schema bảng tasks
print("\n📋 1. CẤU TRÚC BẢNG TASKS:")
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(tasks)")
columns_info = cursor.fetchall()
columns = [col[1] for col in columns_info]

print(f"   Tổng số cột: {len(columns)}")
print(f"   Danh sách cột:")
for col in columns_info:
    col_name = col[1]
    col_type = col[2]
    not_null = "NOT NULL" if col[3] else "NULL"
    default = f"DEFAULT {col[4]}" if col[4] is not None else ""
    print(f"      - {col_name}: {col_type} {not_null} {default}")

# 2. Kiểm tra dữ liệu tasks
print("\n📋 2. DỮ LIỆU TASKS:")
tasks_count = cursor.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
print(f"   Tổng số tasks: {tasks_count}")

if tasks_count > 0:
    # Lấy tất cả tasks
    tasks = cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
    
    # Phân tích theo user_id
    tasks_by_user = {}
    tasks_no_user = []
    tasks_invalid_user = []
    
    for task in tasks:
        user_id = task['user_id'] if 'user_id' in task.keys() and task['user_id'] else None
        if not user_id:
            tasks_no_user.append(task)
        else:
            # Kiểm tra user có tồn tại không
            user_check = conn.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if not user_check:
                tasks_invalid_user.append(task)
            
            if user_id not in tasks_by_user:
                tasks_by_user[user_id] = []
            tasks_by_user[user_id].append(task)
    
    print(f"\n   📊 PHÂN TÍCH:")
    print(f"      - Tasks có user_id hợp lệ: {tasks_count - len(tasks_no_user) - len(tasks_invalid_user)}")
    print(f"      - Tasks KHÔNG có user_id: {len(tasks_no_user)}")
    print(f"      - Tasks có user_id KHÔNG tồn tại: {len(tasks_invalid_user)}")
    print(f"      - Số users có tasks: {len(tasks_by_user)}")
    
    # Chi tiết tasks không có user
    if tasks_no_user:
        print(f"\n   ⚠️  TASKS KHÔNG CÓ USER_ID ({len(tasks_no_user)}):")
        for task in tasks_no_user[:5]:  # Hiển thị 5 đầu tiên
            print(f"      - {task['task_id']}: '{get_row_value(task, 'title', 'N/A')}' (created: {get_row_value(task, 'created_at', 'N/A')})")
        if len(tasks_no_user) > 5:
            print(f"      ... và {len(tasks_no_user) - 5} tasks khác")
    
    # Chi tiết tasks có user_id không hợp lệ
    if tasks_invalid_user:
        print(f"\n   ❌ TASKS CÓ USER_ID KHÔNG TỒN TẠI ({len(tasks_invalid_user)}):")
        for task in tasks_invalid_user[:5]:
            print(f"      - {task['task_id']}: user_id='{get_row_value(task, 'user_id')}', title='{get_row_value(task, 'title', 'N/A')}'")
        if len(tasks_invalid_user) > 5:
            print(f"      ... và {len(tasks_invalid_user) - 5} tasks khác")

    # Thống kê notif1-8
    print(f"\n   📊 THỐNG KÊ NOTIFICATIONS (notif1-8):")
    notif_stats = {}
    for i in range(1, 9):
        notif_key = f'notif{i}'
        if notif_key in columns:
            count = cursor.execute(f"SELECT COUNT(*) FROM tasks WHERE {notif_key} IS NOT NULL AND {notif_key} != ''").fetchone()[0]
            notif_stats[notif_key] = count
            print(f"      - {notif_key}: {count} tasks có giá trị")
    
    # Hiển thị tasks theo user
    print(f"\n   📝 TASKS THEO USER (top 10 tasks gần nhất):")
    for idx, task in enumerate(tasks[:10], 1):
        task_id = task['task_id']
        title = task['title'] or '(no title)'
        user_id = task['user_id'] if 'user_id' in task.keys() and task['user_id'] else '(no user)'
        status = task['status'] if 'status' in task.keys() and task['status'] else 'pending'
        created_at = task['created_at'] if 'created_at' in task.keys() and task['created_at'] else 'N/A'
        
        # Lấy thông tin user
        user_info = 'N/A'
        if user_id and user_id != '(no user)':
            user_row = conn.execute("""
                SELECT display_name, email, phone_number 
                FROM users 
                WHERE user_id = ?
            """, (user_id,)).fetchone()
            if user_row:
                user_info = f"{user_row['display_name'] or user_row['email'] or user_id}"
        
        print(f"\n   [{idx}] Task ID: {task_id}")
        print(f"       Title: {title}")
        print(f"       User: {user_id} ({user_info})")
        print(f"       Status: {status}")
        print(f"       Created: {created_at}")
        
        # Hiển thị các trường quan trọng
        if 'description' in columns and task['description']:
            desc = task['description']
            print(f"       Description: {desc[:80]}{'...' if len(desc) > 80 else ''}")
        if 'start_date' in columns and task['start_date']:
            print(f"       Start Date: {task['start_date']}")
        if 'end_date' in columns and task['end_date']:
            print(f"       End Date: {task['end_date']}")
        if 'deadline' in columns and task['deadline']:
            print(f"       Deadline: {task['deadline']}")
        if 'notification_time' in columns and task['notification_time']:
            print(f"       Notification Time: {task['notification_time']}")
        
        # Hiển thị các cột notif1-8
        print(f"       Notifications:")
        for i in range(1, 9):
            notif_key = f'notif{i}'
            if notif_key in columns:
                notif_val = task[notif_key] if task[notif_key] else '(empty)'
                print(f"         Notif{i}: {notif_val}")
        
        if 'priority' in columns and task['priority']:
            print(f"       Priority: {task['priority']}")
        if 'category' in columns and task['category']:
            print(f"       Category: {task['category']}")

# 3. Kiểm tra Calendar Events
print("\n📋 3. DỮ LIỆU CALENDAR_EVENTS:")
events_count = cursor.execute("SELECT COUNT(*) FROM calendar_events").fetchone()[0]
print(f"   Tổng số events: {events_count}")

if events_count > 0:
    # Events không có task tương ứng (orphaned)
    orphaned_events = cursor.execute("""
        SELECT e.* 
        FROM calendar_events e
        LEFT JOIN tasks t ON e.task_id = t.task_id
        WHERE t.task_id IS NULL
    """).fetchall()
    
    print(f"   - Events orphaned (không có task): {len(orphaned_events)}")
    
    # Events không có user_id
    events_no_user = cursor.execute("""
        SELECT COUNT(*) FROM calendar_events WHERE user_id IS NULL OR user_id = ''
    """).fetchone()[0]
    print(f"   - Events không có user_id: {events_no_user}")
    
    # Events có user_id nhưng user không tồn tại
    events_invalid_user = cursor.execute("""
        SELECT COUNT(*) 
        FROM calendar_events e
        LEFT JOIN users u ON e.user_id = u.user_id
        WHERE e.user_id IS NOT NULL AND e.user_id != '' AND u.user_id IS NULL
    """).fetchone()[0]
    print(f"   - Events có user_id không tồn tại: {events_invalid_user}")
    
    if orphaned_events:
        print(f"\n   ⚠️  ORPHANED EVENTS ({len(orphaned_events)}):")
        for event in orphaned_events[:5]:
            print(f"      - {event['event_id']}: task_id='{event.get('task_id')}', title='{event.get('title', 'N/A')}'")
        if len(orphaned_events) > 5:
            print(f"      ... và {len(orphaned_events) - 5} events khác")

# 4. Kiểm tra Notifications
print("\n📋 4. DỮ LIỆU NOTIFICATIONS:")
notifs_count = cursor.execute("SELECT COUNT(*) FROM notifications").fetchone()[0]
print(f"   Tổng số notifications: {notifs_count}")

if notifs_count > 0:
    # Notifications không có task tương ứng (orphaned)
    orphaned_notifs = cursor.execute("""
        SELECT n.* 
        FROM notifications n
        LEFT JOIN tasks t ON n.task_id = t.task_id
        WHERE n.task_id IS NOT NULL AND t.task_id IS NULL
    """).fetchall()
    
    print(f"   - Notifications orphaned (không có task): {len(orphaned_notifs)}")
    
    # Notifications theo status
    notifs_by_status = cursor.execute("""
        SELECT status, COUNT(*) as cnt
        FROM notifications
        GROUP BY status
    """).fetchall()
    
    print(f"\n   📊 NOTIFICATIONS THEO STATUS:")
    for row in notifs_by_status:
        print(f"      - {row['status']}: {row['cnt']}")
    
    # Notifications theo task và user
    notifs_with_task_info = cursor.execute("""
        SELECT 
            n.notification_id,
            n.task_id,
            n.status,
            n.scheduled_time,
            t.title as task_title,
            t.user_id,
            COALESCE(u.display_name, u.email, u.phone_number, t.user_id) as user_label
        FROM notifications n
        LEFT JOIN tasks t ON n.task_id = t.task_id
        LEFT JOIN users u ON t.user_id = u.user_id
        ORDER BY n.scheduled_time DESC
        LIMIT 10
    """).fetchall()
    
    if notifs_with_task_info:
        print(f"\n   📝 NOTIFICATIONS GẦN NHẤT (top 10):")
        for idx, notif in enumerate(notifs_with_task_info, 1):
            print(f"\n   [{idx}] Notification ID: {notif['notification_id']}")
            print(f"       Task: {notif['task_id'] or 'N/A'} - '{notif['task_title'] or 'N/A'}'")
            print(f"       User: {notif['user_id'] or 'N/A'} ({notif['user_label'] or 'N/A'})")
            print(f"       Status: {notif['status']}")
            print(f"       Scheduled: {notif['scheduled_time'] or 'N/A'}")
    
    if orphaned_notifs:
        print(f"\n   ⚠️  ORPHANED NOTIFICATIONS ({len(orphaned_notifs)}):")
        for notif in orphaned_notifs[:5]:
            task_id = notif['task_id'] if 'task_id' in notif.keys() and notif['task_id'] else 'N/A'
            print(f"      - {notif['notification_id']}: task_id='{task_id}'")
        if len(orphaned_notifs) > 5:
            print(f"      ... và {len(orphaned_notifs) - 5} notifications khác")

# 5. So sánh với cách frontend lấy tasks
print("\n📋 5. SO SÁNH VỚI FRONTEND:")
print("   Frontend route /tasks lấy tasks bằng: task_manager.get_tasks(user_id=session['user_id'])")
print("   (Filter theo user_id từ session)")

# Lấy danh sách users có tasks
print(f"\n   📊 TASKS THEO USER:")
for user_id, user_tasks in sorted(tasks_by_user.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
    user_row = conn.execute("""
        SELECT display_name, email, phone_number 
        FROM users 
        WHERE user_id = ?
    """, (user_id,)).fetchone()
    
    if user_row:
        user_label = user_row['display_name'] or user_row['email'] or user_row['phone_number'] or user_id
    else:
        user_label = f"{user_id} (KHÔNG TỒN TẠI)"
    
    print(f"      - {user_label}: {len(user_tasks)} tasks")

# 6. Tóm tắt các vấn đề
print("\n" + "=" * 80)
print("📊 TÓM TẮT VẤN ĐỀ:")
print("=" * 80)

issues = []

if tasks_no_user:
    issues.append(f"⚠️  {len(tasks_no_user)} tasks KHÔNG có user_id")
if tasks_invalid_user:
    issues.append(f"❌ {len(tasks_invalid_user)} tasks có user_id KHÔNG tồn tại")
if orphaned_events:
    issues.append(f"⚠️  {len(orphaned_events)} calendar_events orphaned (không có task)")
if orphaned_notifs:
    issues.append(f"⚠️  {len(orphaned_notifs)} notifications orphaned (không có task)")

if issues:
    print("\n   Các vấn đề cần xử lý:")
    for issue in issues:
        print(f"   {issue}")
else:
    print("\n   ✅ Không có vấn đề! Database nhất quán.")

print("\n" + "=" * 80)
print("✅ Hoàn tất kiểm tra!")
print("=" * 80)

conn.close()
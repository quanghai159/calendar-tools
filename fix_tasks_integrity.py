# fix_tasks_integrity.py
# -*- coding: utf-8 -*-
"""
Script để fix các vấn đề với tasks:
1. Gán user_id cho tasks không có user_id (hoặc xóa nếu không cần)
2. Xóa orphaned notifications
3. Gán user_id cho events không có user_id
"""
import sqlite3
import json
import os
from pathlib import Path

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

# Backup database
import shutil
backup_path = str(db_path) + f".backup.{int(__import__('time').time())}"
shutil.copy2(db_path, backup_path)
print(f"✅ Đã backup database: {backup_path}\n")

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=" * 80)
print("🔧 FIX TASKS INTEGRITY")
print("=" * 80)

# 1. Fix tasks không có user_id
print("\n🔧 1. Xử lý tasks không có user_id...")
tasks_no_user = cursor.execute("SELECT * FROM tasks WHERE user_id IS NULL OR user_id = ''").fetchall()
print(f"   Tìm thấy {len(tasks_no_user)} tasks không có user_id")

if tasks_no_user:
    print("\n   Bạn có muốn:")
    print("   A) Xóa tất cả tasks không có user_id")
    print("   B) Gán user_id cho các tasks (cần chọn user)")
    print("   C) Bỏ qua (không làm gì)")
    
    choice = input("\n   Chọn (A/B/C): ").strip().upper()
    
    if choice == 'A':
        # Xóa tasks không có user_id và các dữ liệu liên quan
        task_ids = [t['task_id'] for t in tasks_no_user]
        
        # Xóa notifications liên quan
        placeholders = ','.join('?' * len(task_ids))
        cursor.execute(f"DELETE FROM notifications WHERE task_id IN ({placeholders})", task_ids)
        deleted_notifs = cursor.rowcount
        
        # Xóa calendar_events liên quan
        cursor.execute(f"DELETE FROM calendar_events WHERE task_id IN ({placeholders})", task_ids)
        deleted_events = cursor.rowcount
        
        # Xóa tasks
        cursor.execute(f"DELETE FROM tasks WHERE task_id IN ({placeholders})", task_ids)
        deleted_tasks = cursor.rowcount
        
        conn.commit()
        print(f"   ✅ Đã xóa:")
        print(f"      - {deleted_tasks} tasks")
        print(f"      - {deleted_events} calendar_events")
        print(f"      - {deleted_notifs} notifications")
    
    elif choice == 'B':
        # Lấy danh sách users
        users = cursor.execute("SELECT user_id, display_name, email FROM users ORDER BY display_name, email").fetchall()
        print(f"\n   Danh sách users:")
        for idx, user in enumerate(users, 1):
            user_label = user['display_name'] or user['email'] or user['user_id']
            print(f"      [{idx}] {user_label} ({user['user_id']})")
        
        user_choice = input("\n   Chọn user (số): ").strip()
        try:
            selected_idx = int(user_choice) - 1
            if 0 <= selected_idx < len(users):
                selected_user_id = users[selected_idx]['user_id']
                
                # Gán user_id cho tasks
                cursor.execute("""
                    UPDATE tasks 
                    SET user_id = ?
                    WHERE user_id IS NULL OR user_id = ''
                """, (selected_user_id,))
                updated_tasks = cursor.rowcount
                
                # Gán user_id cho calendar_events tương ứng
                task_ids = [t['task_id'] for t in tasks_no_user]
                placeholders = ','.join('?' * len(task_ids))
                cursor.execute(f"""
                    UPDATE calendar_events 
                    SET user_id = ?
                    WHERE task_id IN ({placeholders}) AND (user_id IS NULL OR user_id = '')
                """, [selected_user_id] + task_ids)
                updated_events = cursor.rowcount
                
                conn.commit()
                print(f"   ✅ Đã gán user_id '{selected_user_id}' cho:")
                print(f"      - {updated_tasks} tasks")
                print(f"      - {updated_events} calendar_events")
            else:
                print("   ❌ Số không hợp lệ!")
        except ValueError:
            print("   ❌ Vui lòng nhập số!")
    
    else:
        print("   ⏭️  Bỏ qua")

# 2. Fix orphaned notifications
print("\n🔧 2. Xử lý orphaned notifications...")
orphaned_notifs = cursor.execute("""
    SELECT n.* 
    FROM notifications n
    LEFT JOIN tasks t ON n.task_id = t.task_id
    WHERE n.task_id IS NOT NULL AND t.task_id IS NULL
""").fetchall()

print(f"   Tìm thấy {len(orphaned_notifs)} orphaned notifications")

if orphaned_notifs:
    print("\n   Bạn có muốn xóa các notifications này? (y/n): ", end='')
    choice = input().strip().lower()
    
    if choice == 'y':
        notif_ids = [n['notification_id'] for n in orphaned_notifs]
        placeholders = ','.join('?' * len(notif_ids))
        cursor.execute(f"DELETE FROM notifications WHERE notification_id IN ({placeholders})", notif_ids)
        deleted = cursor.rowcount
        conn.commit()
        print(f"   ✅ Đã xóa {deleted} orphaned notifications")
    else:
        print("   ⏭️  Bỏ qua")

# 3. Fix events không có user_id (nếu tasks đã có user_id)
print("\n🔧 3. Xử lý calendar_events không có user_id...")
events_no_user = cursor.execute("""
    SELECT e.*, t.user_id as task_user_id
    FROM calendar_events e
    LEFT JOIN tasks t ON e.task_id = t.task_id
    WHERE (e.user_id IS NULL OR e.user_id = '') AND t.user_id IS NOT NULL
""").fetchall()

print(f"   Tìm thấy {len(events_no_user)} events không có user_id (nhưng task có user_id)")

if events_no_user:
    # Tự động sync user_id từ tasks
    cursor.execute("""
        UPDATE calendar_events
        SET user_id = (
            SELECT user_id FROM tasks WHERE tasks.task_id = calendar_events.task_id
        )
        WHERE (user_id IS NULL OR user_id = '') 
          AND task_id IN (SELECT task_id FROM tasks WHERE user_id IS NOT NULL)
    """)
    updated = cursor.rowcount
    conn.commit()
    print(f"   ✅ Đã sync user_id cho {updated} calendar_events từ tasks")

print("\n" + "=" * 80)
print("✅ Hoàn tất fix!")
print("=" * 80)

conn.close()
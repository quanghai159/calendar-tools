# fix_database_sync.py
# -*- coding: utf-8 -*-
"""
Script để fix:
1. Migrate users từ group 'member' sang 'user'
2. Sync users table với user_settings (display_name, phone_number)
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
print("=" * 80)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 1. Fix group 'member' -> 'user'
print("\n🔧 1. Migrate users từ group 'member' sang 'user'...")
members_in_member_group = cursor.execute("""
    SELECT user_id FROM user_group_memberships WHERE group_id = 'member'
""").fetchall()

if members_in_member_group:
    print(f"   Tìm thấy {len(members_in_member_group)} users trong group 'member'")
    for row in members_in_member_group:
        user_id = row['user_id']
        # Kiểm tra xem user đã có trong group 'user' chưa
        existing = cursor.execute("""
            SELECT 1 FROM user_group_memberships 
            WHERE user_id = ? AND group_id = 'user'
        """, (user_id,)).fetchone()
        
        if not existing:
            # Thêm vào group 'user'
            cursor.execute("""
                INSERT OR IGNORE INTO user_group_memberships (user_id, group_id)
                VALUES (?, 'user')
            """, (user_id,))
            print(f"   ✅ Đã thêm user {user_id} vào group 'user'")
        else:
            print(f"   ℹ️  User {user_id} đã có trong group 'user'")
    
    # Xóa tất cả memberships với group 'member'
    cursor.execute("DELETE FROM user_group_memberships WHERE group_id = 'member'")
    deleted = cursor.rowcount
    print(f"   ✅ Đã xóa {deleted} memberships với group 'member'")
else:
    print("   ✅ Không có users trong group 'member'")

# 2. Sync users table với user_settings
print("\n🔧 2. Sync users table với user_settings...")
users_with_settings = cursor.execute("""
    SELECT DISTINCT us.user_id
    FROM user_settings us
    WHERE us.setting_key IN ('display_name', 'phone_number')
      AND us.tool_id IS NULL
""").fetchall()

synced_count = 0
for row in users_with_settings:
    user_id = row['user_id']
    
    # Lấy giá trị mới nhất từ user_settings
    display_name_row = cursor.execute("""
        SELECT setting_value FROM user_settings
        WHERE user_id = ? AND setting_key = 'display_name' AND tool_id IS NULL
        ORDER BY updated_at DESC LIMIT 1
    """, (user_id,)).fetchone()
    
    phone_number_row = cursor.execute("""
        SELECT setting_value FROM user_settings
        WHERE user_id = ? AND setting_key = 'phone_number' AND tool_id IS NULL
        ORDER BY updated_at DESC LIMIT 1
    """, (user_id,)).fetchone()
    
    display_name = display_name_row['setting_value'] if display_name_row and display_name_row['setting_value'] else None
    phone_number = phone_number_row['setting_value'] if phone_number_row and phone_number_row['setting_value'] else None
    
    # Lấy giá trị hiện tại từ users table
    user_row = cursor.execute("""
        SELECT display_name, phone_number FROM users WHERE user_id = ?
    """, (user_id,)).fetchone()
    
    if user_row:
        current_display_name = user_row['display_name'] if user_row['display_name'] else None
        current_phone = user_row['phone_number'] if user_row['phone_number'] else None
        
        # Chỉ update nếu có thay đổi
        if (display_name and display_name != current_display_name) or (phone_number and phone_number != current_phone):
            cursor.execute("""
                UPDATE users 
                SET display_name = COALESCE(?, display_name),
                    phone_number = COALESCE(?, phone_number),
                    updated_at = datetime('now')
                WHERE user_id = ?
            """, (
                display_name if display_name else None,
                phone_number if phone_number else None,
                user_id
            ))
            synced_count += 1
            print(f"   ✅ Synced user {user_id}:")
            if display_name and display_name != current_display_name:
                print(f"      display_name: '{current_display_name}' -> '{display_name}'")
            if phone_number and phone_number != current_phone:
                print(f"      phone_number: '{current_phone}' -> '{phone_number}'")

print(f"\n   ✅ Đã sync {synced_count} users")

conn.commit()
conn.close()

print("\n" + "=" * 80)
print("✅ Hoàn tất!")
print("=" * 80)
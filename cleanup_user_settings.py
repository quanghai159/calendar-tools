# cleanup_user_settings.py
# -*- coding: utf-8 -*-
"""
Script cleanup duplicates trong user_settings table
Giữ lại bản ghi mới nhất cho mỗi (user_id, tool_id, setting_key)
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

import os
print(f"📂 Database path: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🔍 Đang kiểm tra duplicates...")

# Đếm duplicates
duplicates = cursor.execute("""
    SELECT user_id, tool_id, setting_key, COUNT(*) as cnt
    FROM user_settings
    GROUP BY user_id, COALESCE(tool_id, ''), setting_key
    HAVING COUNT(*) > 1
""").fetchall()

print(f"   Tìm thấy {len(duplicates)} nhóm duplicates")

if duplicates:
    print("\n🗑️  Đang xóa duplicates (giữ lại bản ghi mới nhất)...")
    
    deleted_count = 0
    for dup in duplicates:
        user_id, tool_id, setting_key, cnt = dup
        # Xóa tất cả trừ bản ghi có updated_at mới nhất
        cursor.execute("""
            DELETE FROM user_settings
            WHERE user_id = ? 
              AND (tool_id = ? OR (tool_id IS NULL AND ? IS NULL))
              AND setting_key = ?
              AND updated_at < (
                  SELECT MAX(updated_at)
                  FROM user_settings
                  WHERE user_id = ?
                    AND (tool_id = ? OR (tool_id IS NULL AND ? IS NULL))
                    AND setting_key = ?
              )
        """, (user_id, tool_id, tool_id, setting_key, user_id, tool_id, tool_id, setting_key))
        deleted_count += cursor.rowcount
    
    conn.commit()
    print(f"   ✅ Đã xóa {deleted_count} bản ghi trùng lặp")
else:
    print("   ✅ Không có duplicates!")

conn.close()
print("\n✅ Hoàn tất!")
# -*- coding: utf-8 -*-
"""
Migration 001g: Tạo indexes để tối ưu performance
"""

import sqlite3

def migrate_indexes(conn):
    """Tạo các indexes"""
    cursor = conn.cursor()
    
    print("\n📋 11. Tạo indexes...")
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_user_groups_user_id ON user_group_memberships (user_id)",
        "CREATE INDEX IF NOT EXISTS idx_user_groups_group_id ON user_group_memberships (group_id)",
        "CREATE INDEX IF NOT EXISTS idx_permissions_tool_id ON permissions (tool_id)",
        "CREATE INDEX IF NOT EXISTS idx_group_permissions_group_id ON group_permissions (group_id)",
        "CREATE INDEX IF NOT EXISTS idx_user_permissions_user_id ON user_permissions (user_id)",
        "CREATE INDEX IF NOT EXISTS idx_user_tool_access_user_id ON user_tool_access (user_id)",
        "CREATE INDEX IF NOT EXISTS idx_user_tool_access_tool_id ON user_tool_access (tool_id)",
        "CREATE INDEX IF NOT EXISTS idx_group_tool_access_group_id ON group_tool_access (group_id)",
        "CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings (user_id)",
        "CREATE INDEX IF NOT EXISTS idx_user_settings_tool_id ON user_settings (tool_id)",
    ]
    
    for index_sql in indexes:
        try:
            cursor.execute(index_sql)
        except sqlite3.OperationalError as e:
            print(f"   ⚠️  Index có thể đã tồn tại: {e}")
    
    print("   ✅ Tất cả indexes đã được tạo")
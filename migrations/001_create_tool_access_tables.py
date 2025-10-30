# -*- coding: utf-8 -*-
"""
Migration 001e: Tạo bảng user_tool_access và group_tool_access
"""

import sqlite3

def migrate_tool_access_tables(conn):
    """Tạo bảng liên quan đến tool access"""
    cursor = conn.cursor()
    
    # Tạo bảng user_tool_access
    print("\n📋 8. Tạo bảng user_tool_access...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_tool_access (
            user_id TEXT NOT NULL,
            tool_id TEXT NOT NULL,
            granted_by TEXT,
            granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            PRIMARY KEY (user_id, tool_id),
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
            FOREIGN KEY (tool_id) REFERENCES tools (tool_id) ON DELETE CASCADE
        )
    """)
    print("   ✅ Bảng user_tool_access đã được tạo")
    
    # Tạo bảng group_tool_access
    print("\n📋 9. Tạo bảng group_tool_access...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_tool_access (
            group_id TEXT NOT NULL,
            tool_id TEXT NOT NULL,
            granted_by TEXT,
            granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (group_id, tool_id),
            FOREIGN KEY (group_id) REFERENCES user_groups (group_id) ON DELETE CASCADE,
            FOREIGN KEY (tool_id) REFERENCES tools (tool_id) ON DELETE CASCADE
        )
    """)
    print("   ✅ Bảng group_tool_access đã được tạo")
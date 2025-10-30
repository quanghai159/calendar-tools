# -*- coding: utf-8 -*-
"""
Migration 001f: Tạo bảng user_settings
"""

import sqlite3

def migrate_user_settings_table(conn):
    """Tạo bảng user_settings"""
    cursor = conn.cursor()
    
    print("\n📋 10. Tạo bảng user_settings...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id TEXT NOT NULL,
            tool_id TEXT,
            setting_key TEXT NOT NULL,
            setting_value TEXT,
            setting_type TEXT DEFAULT 'string',
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, tool_id, setting_key),
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
            FOREIGN KEY (tool_id) REFERENCES tools (tool_id) ON DELETE SET NULL
        )
    """)
    print("   ✅ Bảng user_settings đã được tạo")
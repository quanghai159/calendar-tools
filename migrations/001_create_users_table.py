# -*- coding: utf-8 -*-
"""
Migration 001a: Tạo/cập nhật bảng users
"""

import sqlite3

def migrate_users_table(conn):
    """Tạo hoặc cập nhật bảng users"""
    cursor = conn.cursor()
    
    print("\n📋 1. Cập nhật bảng users...")
    cursor.execute("PRAGMA table_info(users)")
    user_columns = [col[1] for col in cursor.fetchall()]
    
    if 'user_id' not in user_columns:
        # Tạo bảng users mới
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                username TEXT,
                display_name TEXT,
                avatar_url TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)
        print("   ✅ Tạo bảng users mới")
    else:
        # Thêm các cột mới nếu thiếu
        new_columns = {
            'display_name': 'TEXT',
            'avatar_url': 'TEXT',
            'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
            'last_login': 'TIMESTAMP'
        }
        
        for col_name, col_type in new_columns.items():
            if col_name not in user_columns:
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                    print(f"   ✅ Thêm cột {col_name} vào bảng users")
                except sqlite3.OperationalError as e:
                    print(f"   ⚠️  Cột {col_name} có thể đã tồn tại: {e}")
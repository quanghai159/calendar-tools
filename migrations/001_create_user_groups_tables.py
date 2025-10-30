# -*- coding: utf-8 -*-
"""
Migration 001b: Tạo bảng user_groups và user_group_memberships
"""

import sqlite3

def migrate_user_groups_tables(conn):
    """Tạo bảng user_groups và user_group_memberships"""
    cursor = conn.cursor()
    
    # Tạo bảng user_groups
    print("\n📋 2. Tạo bảng user_groups...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_groups (
            group_id TEXT PRIMARY KEY,
            group_name TEXT NOT NULL UNIQUE,
            description TEXT,
            level INTEGER NOT NULL,
            is_system BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("   ✅ Bảng user_groups đã được tạo")
    
    # Tạo bảng user_group_memberships
    print("\n📋 3. Tạo bảng user_group_memberships...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_group_memberships (
            user_id TEXT NOT NULL,
            group_id TEXT NOT NULL,
            assigned_by TEXT,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            PRIMARY KEY (user_id, group_id),
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
            FOREIGN KEY (group_id) REFERENCES user_groups (group_id) ON DELETE CASCADE
        )
    """)
    print("   ✅ Bảng user_group_memberships đã được tạo")
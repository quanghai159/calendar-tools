# -*- coding: utf-8 -*-
"""
Migration 001d: Tạo bảng group_permissions và user_permissions
"""

import sqlite3

def migrate_permission_relations_tables(conn):
    """Tạo bảng liên quan đến permissions"""
    cursor = conn.cursor()
    
    # Tạo bảng group_permissions
    print("\n📋 6. Tạo bảng group_permissions...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_permissions (
            group_id TEXT NOT NULL,
            permission_id TEXT NOT NULL,
            granted_by TEXT,
            granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (group_id, permission_id),
            FOREIGN KEY (group_id) REFERENCES user_groups (group_id) ON DELETE CASCADE,
            FOREIGN KEY (permission_id) REFERENCES permissions (permission_id) ON DELETE CASCADE
        )
    """)
    print("   ✅ Bảng group_permissions đã được tạo")
    
    # Tạo bảng user_permissions
    print("\n📋 7. Tạo bảng user_permissions...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_permissions (
            user_id TEXT NOT NULL,
            permission_id TEXT NOT NULL,
            granted_by TEXT,
            granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            PRIMARY KEY (user_id, permission_id),
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
            FOREIGN KEY (permission_id) REFERENCES permissions (permission_id) ON DELETE CASCADE
        )
    """)
    print("   ✅ Bảng user_permissions đã được tạo")
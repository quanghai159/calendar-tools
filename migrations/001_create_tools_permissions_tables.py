# -*- coding: utf-8 -*-
"""
Migration 001c: Tạo bảng tools và permissions
"""

import sqlite3

def migrate_tools_permissions_tables(conn):
    """Tạo bảng tools và permissions"""
    cursor = conn.cursor()
    
    # Tạo bảng tools
    print("\n📋 4. Tạo bảng tools...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tools (
            tool_id TEXT PRIMARY KEY,
            tool_name TEXT NOT NULL,
            description TEXT,
            port INTEGER,
            base_url TEXT,
            icon TEXT conducting,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("   ✅ Bảng tools đã được tạo")
    
    # Tạo bảng permissions
    print("\n📋 5. Tạo bảng permissions...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS permissions (
            permission_id TEXT PRIMARY KEY,
            tool_id TEXT NOT NULL,
            permission_key TEXT NOT NULL,
            permission_name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tool_id) REFERENCES tools (tool_id) ON DELETE CASCADE,
            UNIQUE(tool_id, permission_key)
        )
    """)
    print("   ✅ Bảng permissions đã được tạo")
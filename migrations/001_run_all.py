# -*- coding: utf-8 -*-
"""
Migration 001: Tạo toàn bộ bảng phân quyền
"""
import os
import sys
import sqlite3
import importlib.util

current_dir = os.path.dirname(os.path.abspath(__file__))

def _load_by_path(filename, func_name):
    path = os.path.join(current_dir, filename)
    spec = importlib.util.spec_from_file_location(func_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, func_name)

# Nạp các hàm migrate từ file cùng thư mục theo đường dẫn
migrate_users_table = _load_by_path("001_create_users_table.py", "migrate_users_table")
migrate_user_groups_tables = _load_by_path("001_create_user_groups_tables.py", "migrate_user_groups_tables")
migrate_tools_permissions_tables = _load_by_path("001_create_tools_permissions_tables.py", "migrate_tools_permissions_tables")
migrate_permission_relations_tables = _load_by_path("001_create_permission_relations_tables.py", "migrate_permission_relations_tables")
migrate_tool_access_tables = _load_by_path("001_create_tool_access_tables.py", "migrate_tool_access_tables")
migrate_user_settings_table = _load_by_path("001_create_user_settings_table.py", "migrate_user_settings_table")
migrate_indexes = _load_by_path("001_create_indexes.py", "migrate_indexes")

def run_migration(database_path: str = "database/calendar_tools.db"):
    print("=" * 60)
    print("PHASE 1: TAO BANG PHAN QUYEN")
    print("=" * 60)

    conn = sqlite3.connect(database_path)
    try:
        migrate_users_table(conn)
        migrate_user_groups_tables(conn)
        migrate_tools_permissions_tables(conn)
        migrate_permission_relations_tables(conn)
        migrate_tool_access_tables(conn)
        migrate_user_settings_table(conn)
        migrate_indexes(conn)

        conn.commit()
        print("\n" + "=" * 60)
        print("✅ MIGRATION HOAN TAT!")
        print("=" * 60)
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Loi migration: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    # Lấy db_path từ config nếu có
    try:
        sys.path.insert(0, os.path.dirname(current_dir))
        from backend.utils.config_loader import ConfigLoader
        config = ConfigLoader("config/config.json")
        db_path = config.get_value('database.path', 'database/calendar_tools.db')
    except:
        db_path = "database/calendar_tools.db"
    run_migration(db_path)
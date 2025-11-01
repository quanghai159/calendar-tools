#!/usr/bin/env python3
"""
Script để chạy migration 003: Tạo bảng task_datetime_offsets
"""
import sys
import os

# Thêm project root vào path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from migrations.migrations_003_create_task_datetime_offsets_table import run_migration

if __name__ == '__main__':
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'database/calendar_tools.db'
    
    # Đảm bảo thư mục database tồn tại
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    
    print(f"Running migration 003 on database: {db_path}")
    success = run_migration(db_path)
    
    if success:
        print("✅ Migration completed successfully!")
        sys.exit(0)
    else:
        print("❌ Migration failed!")
        sys.exit(1)
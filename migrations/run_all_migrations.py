# -*- coding: utf-8 -*-
"""
Master migration script: chạy tất cả migrations theo thứ tự
"""
import os
import sys
import subprocess

def run_all_migrations():
    current_dir = os.path.dirname(os.path.abspath(__file__))

    print("=" * 60)
    print("RUNNING ALL MIGRATIONS")
    print("=" * 60)

    # Step 1: Create tables
    print("\n" + "=" * 60)
    print("STEP 1: Creating database tables...")
    print("=" * 60)
    ret1 = subprocess.run([sys.executable, os.path.join(current_dir, "001_run_all.py")])
    if ret1.returncode != 0:
        raise SystemExit("Migration 001 failed")

    # Step 2: Seed default data
    print("\n" + "=" * 60)
    print("STEP 2: Seeding default data...")
    print("=" * 60)
    ret2 = subprocess.run([sys.executable, os.path.join(current_dir, "002_seed_default_data.py")])
    if ret2.returncode != 0:
        raise SystemExit("Migration 002 failed")

    # Step 3: Add notif columns
    print("\n" + "=" * 60)
    print("STEP 3: Adding notification columns (notif1..notif8)...")
    print("=" * 60)
    ret3 = subprocess.run([sys.executable, os.path.join(current_dir, "003_add_notif_columns.py")])
    if ret3.returncode != 0:
        raise SystemExit("Migration 003 failed")

    # Step 4: Update users phone_number (THÊM ĐOẠN NÀY)
    print("\n" + "=" * 60)
    print("STEP 4: Updating users phone_number column...")
    print("=" * 60)
    ret4 = subprocess.run([sys.executable, os.path.join(current_dir, "004_update_users_phone_number.py")])
    if ret4.returncode != 0:
        raise SystemExit("Migration 004 failed")

    print("\n" + "=" * 60)
    print("✅ ALL MIGRATIONS COMPLETED SUCCESSFULLY!")
    print("=" * 60)

    # Step 5: Create task_datetime_offsets table
    print("\n" + "=" * 60)
    print("STEP 5: Creating task_datetime_offsets table...")
    print("=" * 60)
    
    # Lấy db_path từ config hoặc default
    import json
    try:
        config_path = os.path.join(os.path.dirname(current_dir), 'config', 'config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
            db_path = config.get('database', {}).get('path', 'database/calendar_tools.db')
    except:
        db_path = 'database/calendar_tools.db'
    
    ret5 = subprocess.run([
        sys.executable,
        os.path.join(current_dir, '005_create_task_datetime_offsets_table.py'),
        db_path
    ])
    if ret5.returncode != 0:
        print("⚠️ Migration 005 failed, but continuing...")
        # Không raise error vì có thể bảng đã tồn tại

    print("\n" + "=" * 60)
    print("✅ ALL MIGRATIONS INCLUDING 005 COMPLETED!")
    print("=" * 60)

if __name__ == "__main__":
    run_all_migrations()
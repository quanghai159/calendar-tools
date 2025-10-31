# -*- coding: utf-8 -*-
"""
Migration 004: Update users table - đảm bảo phone_number cho user cũ
"""
import sqlite3
import os
import sys

def migrate_users_phone_number():
    """Cập nhật phone_number cho các user cũ (set NULL nếu thiếu)"""
    # Lấy đường dẫn database từ config hoặc default
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    db_path = os.path.join(project_root, "database", "calendar_tools.db")
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    print("\n📋 Updating users table - phone_number column...")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Kiểm tra cột phone_number có tồn tại không
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'phone_number' not in columns:
                print("   ⚠️  Cột phone_number chưa có, đang thêm...")
                cursor.execute("ALTER TABLE users ADD COLUMN phone_number TEXT")
                print("   ✅ Đã thêm cột phone_number")
            
            # Update các user có phone_number = NULL hoặc rỗng thành NULL (đảm bảo tính nhất quán)
            cursor.execute("""
                UPDATE users 
                SET phone_number = NULL 
                WHERE phone_number = '' OR phone_number IS NULL
            """)
            
            # Đếm số user đã update
            updated = cursor.rowcount
            conn.commit()
            
            print(f"   ✅ Đã cập nhật {updated} user(s)")
            
            # Liệt kê tất cả user để kiểm tra
            cursor.execute("SELECT user_id, email, display_name, phone_number FROM users")
            users = cursor.fetchall()
            print(f"\n   📊 Tổng số user: {len(users)}")
            for u in users:
                uid, email, name, phone = u
                print(f"      - {uid[:8]}... | {email or 'N/A'} | {name or 'N/A'} | phone: {phone or 'NULL'}")
            
            return True
            
    except Exception as e:
        print(f"   ❌ Lỗi: {e}")
        return False

if __name__ == "__main__":
    success = migrate_users_phone_number()
    if success:
        print("\n✅ Migration 004 completed successfully!")
    else:
        print("\n❌ Migration 004 failed!")
        sys.exit(1)
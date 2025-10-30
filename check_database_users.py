#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script kiểm tra database phân tách theo user
"""

import os
import sys
import sqlite3

# Thêm backend vào path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, 'backend')
sys.path.append(backend_dir)

from core.database_manager import DatabaseManager

def check_database_users():
    """Kiểm tra database có phân tách theo user chưa"""
    db_path = "database/calendar_tools.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database không tồn tại: {db_path}")
        return
    
    db = DatabaseManager(db_path)
    
    print("=" * 60)
    print("KIỂM TRA DATABASE PHÂN TÁCH THEO USER")
    print("=" * 60)
    
    with db.get_connection() as conn:
        # 1. Kiểm tra cấu trúc bảng tasks
        print("\n📋 1. CẤU TRÚC BẢNG TASKS:")
        print("-" * 60)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(tasks)")
        columns = cursor.fetchall()
        
        has_user_id = False
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            print(f"  - {col_name}: {col_type}")
            if col_name == 'user_id':
                has_user_id = True
        
        if has_user_id:
            print("\n✅ Bảng tasks có cột user_id")
        else:
            print("\n❌ Bảng tasks KHÔNG có cột user_id")
            return
        
        # 2. Kiểm tra cấu trúc bảng calendar_events
        print("\n📋 2. CẤU TRÚC BẢNG CALENDAR_EVENTS:")
        print("-" * 60)
        cursor.execute("PRAGMA table_info(calendar_events)")
        event_columns = cursor.fetchall()
        
        event_has_user_id = False
        for col in event_columns:
            col_name = col[1]
            col_type = col[2]
            print(f"  - {col_name}: {col_type}")
            if col_name == 'user_id':
                event_has_user_id = True
        
        if event_has_user_id:
            print("\n✅ Bảng calendar_events có cột user_id")
        else:
            print("\n❌ Bảng calendar_events KHÔNG có cột user_id")
        
        # 3. Thống kê tasks theo user
        print("\n📊 3. THỐNG KÊ TASKS THEO USER:")
        print("-" * 60)
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN user_id IS NULL OR user_id = '' THEN '(Chưa có user)'
                    ELSE user_id
                END as user_id,
                COUNT(*) as task_count,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'overdue' THEN 1 ELSE 0 END) as overdue
            FROM tasks
            GROUP BY user_id
            ORDER BY task_count DESC
        """)
        
        stats = cursor.fetchall()
        if stats:
            print(f"\n{'User ID':<40} {'Tổng':<8} {'Pending':<10} {'Completed':<12} {'Overdue':<10}")
            print("-" * 80)
            for stat in stats:
                user_id = stat[0] if stat[0] else '(NULL)'
                total = stat[1]
                pending = stat[2]
                completed = stat[3]
                overdue = stat[4]
                print(f"{user_id:<40} {total:<8} {pending:<10} {completed:<12} {overdue:<10}")
        else:
            print("  (Chưa có tasks nào)")
        
        # 4. Xem một vài tasks mẫu với user_id
        print("\n📝 4. MẪU TASKS (10 tasks đầu tiên):")
        print("-" * 60)
        cursor.execute("""
            SELECT task_id, user_id, title, status, created_at
            FROM tasks
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        tasks = cursor.fetchall()
        if tasks:
            print(f"\n{'Task ID':<20} {'User ID':<30} {'Title':<30} {'Status':<12}")
            print("-" * 92)
            for task in tasks:
                task_id = task[0]
                user_id = task[1] if task[1] else '(NULL)'
                title = (task[2] or '')[:28]
                status = task[3] or 'N/A'
                created_at = task[4] or 'N/A'
                print(f"{task_id:<20} {user_id:<30} {title:<30} {status:<12}")
        else:
            print("  (Chưa có tasks nào)")
        
        # 5. Kiểm tra calendar_events theo user
        print("\n📅 5. THỐNG KÊ CALENDAR_EVENTS THEO USER:")
        print("-" * 60)
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN user_id IS NULL OR user_id = '' THEN '(Chưa có user)'
                    ELSE user_id
                END as user_id,
                COUNT(*) as event_count
            FROM calendar_events
            GROUP BY user_id
            ORDER BY event_count DESC
        """)
        
        event_stats = cursor.fetchall()
        if event_stats:
            print(f"\n{'User ID':<40} {'Số Events':<15}")
            print("-" * 55)
            for stat in event_stats:
                user_id = stat[0] if stat[0] else '(NULL)'
                count = stat[1]
                print(f"{user_id:<40} {count:<15}")
        else:
            print("  (Chưa có events nào)")
    
    print("\n" + "=" * 60)
    print("✅ KIỂM TRA HOÀN TẤT")
    print("=" * 60)

if __name__ == "__main__":
    check_database_users()
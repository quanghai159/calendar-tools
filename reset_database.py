# -*- coding: utf-8 -*-
"""
Reset Database - Xóa database cũ và tạo mới
"""

import os
import sys

# Add backend directory to path
sys.path.append('backend')

from core.database_manager import DatabaseManager

def reset_database():
    """Xóa database cũ và tạo mới"""
    try:
        print("🔄 Resetting database...")
        
        # Xóa database cũ nếu tồn tại
        db_path = "database/calendar_tools.db"
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"✅ Removed old database: {db_path}")
        
        # Tạo database mới
        db = DatabaseManager(db_path)
        print("✅ Created new database with correct schema")
        
        # Test tạo task
        from task_management.simple_task_manager import SimpleTaskManager
        task_manager = SimpleTaskManager(db)
        
        test_task = {
            'title': 'Test Task',
            'description': 'Test description',
            'start_date': '2024-01-15 09:00',
            'end_date': '2024-01-15 17:00',
            'deadline': '2024-01-15 16:00',
            'notification_time': '2024-01-15 15:00',
            'category': 'test',
            'priority': 'medium'
        }
        
        task_id = task_manager.create_task(test_task)
        print(f"✅ Test task created: {task_id}")
        
        # Xóa test task
        tasks = task_manager.get_tasks()
        for task in tasks:
            if task['title'] == 'Test Task':
                # Xóa task test
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM tasks WHERE task_id = ?", (task['task_id'],))
                    cursor.execute("DELETE FROM calendar_events WHERE task_id = ?", (task['task_id'],))
                    conn.commit()
                break
        
        print("✅ Test task cleaned up")
        print("🎉 Database reset completed successfully!")
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reset_database()
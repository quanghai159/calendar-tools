"""
Migration 005: Tạo bảng lưu datetime offsets
"""
import sqlite3
import os

def run_migration(db_path):
    """Tạo bảng task_datetime_offsets"""
    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_datetime_offsets (
                    task_id TEXT NOT NULL,
                    column_name TEXT NOT NULL,
                    offset_value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (task_id, column_name),
                    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
                )
            """)
            
            # Tạo index
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_task_datetime_offsets_task_id 
                ON task_datetime_offsets(task_id)
            """)
            
            conn.commit()
            print("✅ Created task_datetime_offsets table")
            return True
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'database/calendar_tools.db'
    
    # Đảm bảo thư mục database tồn tại
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    
    success = run_migration(db_path)
    sys.exit(0 if success else 1)
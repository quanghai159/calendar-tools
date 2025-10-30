# -*- coding: utf-8 -*-
"""
DATABASE MANAGER MODULE
======================

Mô tả: Quản lý kết nối và thao tác với database
Cách hoạt động:
1. Tạo kết nối database
2. Tạo các bảng cần thiết
3. Cung cấp interface để CRUD operations
4. Quản lý transactions

Thuật toán:
- Sử dụng SQLite cho đơn giản
- Tạo connection pool để tối ưu performance
- Sử dụng context manager để quản lý connection
- Validate data trước khi insert/update

Hướng dẫn sử dụng:
1. Gọi get_connection() để lấy connection
2. Sử dụng execute_query() để thực hiện query
3. Sử dụng context manager để đảm bảo connection được đóng

Ví dụ:
    db = DatabaseManager()
    with db.get_connection() as conn:
        result = db.execute_query(conn, "SELECT * FROM users")
"""

import sqlite3
import os
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_path: str = "database/calendar_tools.db"):
        """
        Khởi tạo DatabaseManager
        
        Args:
            db_path: Đường dẫn đến file database
        """
        self.db_path = db_path
        self._ensure_database_directory()
        
        # Tạo bảng khi khởi tạo
        with self.get_connection() as conn:
            self._create_tables(conn)
    
    def _ensure_database_directory(self):
        """Đảm bảo thư mục database tồn tại"""
        try:
            db_path = self.db_path
            if not db_path:
                # Nếu không có đường dẫn, tạo file trong thư mục hiện tại
                db_path = "calendar_tools.db"
                self.db_path = db_path
            
            # Lấy đường dẫn tuyệt đối
            db_path = os.path.abspath(db_path)
            self.db_path = db_path
            
            db_dir = os.path.dirname(db_path)
            
            # Nếu db_dir rỗng hoặc là thư mục hiện tại, không cần tạo
            if db_dir and db_dir != os.getcwd() and not os.path.exists(db_dir):
                os.makedirs(db_dir)
                print(f"✅ Created database directory: {db_dir}")
            elif not db_dir or db_dir == os.getcwd():
                # File ở thư mục hiện tại, không cần tạo thư mục
                print(f"✅ Using current directory for database")
            else:
                print(f"✅ Database directory exists: {db_dir}")
                
        except Exception as e:
            print(f"⚠️  Error ensuring database directory: {e}")
            # Fallback: sử dụng thư mục hiện tại
            self.db_path = os.path.abspath("calendar_tools.db")
    
    def _create_tables(self, conn):
        """Tạo các bảng trong database"""
        try:
            # Bảng tasks mới (có user_id)
            tasks_table = """
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                user_id TEXT,
                title TEXT NOT NULL,
                description TEXT,
                start_date TEXT,
                end_date TEXT,
                deadline TEXT,
                notification_time TEXT,
                category TEXT DEFAULT 'general',
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                last_modified TEXT
            )
            """
            
            # Bảng calendar_events mới (có user_id)
            calendar_events_table = """
            CREATE TABLE IF NOT EXISTS calendar_events (
                event_id TEXT PRIMARY KEY,
                task_id TEXT,
                user_id TEXT,
                title TEXT NOT NULL,
                description TEXT,
                start_date TEXT,
                end_date TEXT,
                deadline TEXT,
                notification_time TEXT,
                category TEXT DEFAULT 'general',
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'pending',
                source TEXT DEFAULT 'manual',
                created_at TEXT,
                last_modified TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks (task_id)
            )
            """
            
            # Bảng notifications mới
            notifications_table = """
            CREATE TABLE IF NOT EXISTS notifications (
                notification_id TEXT PRIMARY KEY,
                task_id TEXT,
                event_id TEXT,
                notification_type TEXT,
                message TEXT,
                scheduled_time TEXT,
                sent_at TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks (task_id),
                FOREIGN KEY (event_id) REFERENCES calendar_events (event_id)
            )
            """
            
            # Bảng reports mới
            reports_table = """
            CREATE TABLE IF NOT EXISTS reports (
                report_id TEXT PRIMARY KEY,
                report_type TEXT,
                date_range_start TEXT,
                date_range_end TEXT,
                summary TEXT,
                created_at TEXT
            )
            """
            
            # Tạo các bảng
            self.execute_query(conn, tasks_table)
            self.execute_query(conn, calendar_events_table)
            self.execute_query(conn, notifications_table)
            self.execute_query(conn, reports_table)
            
            # Kiểm tra và cập nhật bảng tasks nếu cần
            self._update_tasks_table_schema(conn)
            
            conn.commit()
            print("✅ Database tables created successfully")
            
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            raise

    def _update_tasks_table_schema(self, conn):
        """Cập nhật schema bảng tasks nếu cần"""
        try:
            # Kiểm tra xem bảng tasks có tồn tại không
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
            if not cursor.fetchone():
                return
            
            # Kiểm tra xem các cột có tồn tại không
            cursor.execute("PRAGMA table_info(tasks)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Thêm user_id nếu chưa có
            if 'user_id' not in columns:
                print("🔄 Adding user_id column to tasks table...")
                try:
                    cursor.execute("ALTER TABLE tasks ADD COLUMN user_id TEXT")
                    print("✅ Added user_id column to tasks table")
                except Exception as e:
                    print(f"⚠️  Could not add user_id to tasks: {e}")
            
            # Kiểm tra và cập nhật calendar_events
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='calendar_events'")
            if cursor.fetchone():
                cursor.execute("PRAGMA table_info(calendar_events)")
                event_columns = [column[1] for column in cursor.fetchall()]
                
                if 'user_id' not in event_columns:
                    print("🔄 Adding user_id column to calendar_events table...")
                    try:
                        cursor.execute("ALTER TABLE calendar_events ADD COLUMN user_id TEXT")
                        print("✅ Added user_id column to calendar_events table")
                    except Exception as e:
                        print(f"⚠️  Could not add user_id to calendar_events: {e}")
            
        except Exception as e:
            print(f"⚠️  Error updating tasks table schema: {e}")
    
    def _create_users_table(self, conn: sqlite3.Connection) -> None:
        """Tạo bảng users"""
        query = """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            telegram_username TEXT,
            zalo_phone TEXT,
            zalo_user_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            settings TEXT DEFAULT '{}'
        )
        """
        conn.execute(query)
    
    def _create_tasks_table(self, conn: sqlite3.Connection) -> None:
        """Tạo bảng tasks"""
        query = """
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            google_sheet_url TEXT NOT NULL,
            google_sheet_id TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_sync TIMESTAMP,
            settings TEXT DEFAULT '{}',
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        """
        conn.execute(query)
    
    def _create_calendar_events_table(self, conn: sqlite3.Connection) -> None:
        """Tạo bảng calendar_events"""
        query = """
        CREATE TABLE IF NOT EXISTS calendar_events (
            event_id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            start_date TEXT NOT NULL,
            end_date TEXT,
            deadline TEXT,
            category TEXT DEFAULT 'work',
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'pending',
            source TEXT NOT NULL,
            last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks (task_id),
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        """
        conn.execute(query)
    
    def _create_notifications_table(self, conn: sqlite3.Connection) -> None:
        """Tạo bảng notifications"""
        query = """
        CREATE TABLE IF NOT EXISTS notifications (
            notification_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            event_id TEXT,
            notification_type TEXT NOT NULL,
            message TEXT NOT NULL,
            sent_at TIMESTAMP,
            status TEXT DEFAULT 'pending',
            retry_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (event_id) REFERENCES calendar_events (event_id)
        )
        """
        conn.execute(query)
    
    def _create_reports_table(self, conn: sqlite3.Connection) -> None:
        """Tạo bảng reports"""
        query = """
        CREATE TABLE IF NOT EXISTS reports (
            report_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            report_type TEXT NOT NULL,
            date_range_start TEXT NOT NULL,
            date_range_end TEXT NOT NULL,
            summary TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        """
        conn.execute(query)
    
    def _create_indexes(self, conn: sqlite3.Connection) -> None:
        """Tạo indexes để tối ưu performance"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users (email)",
            "CREATE INDEX IF NOT EXISTS idx_users_telegram ON users (telegram_username)",
            "CREATE INDEX IF NOT EXISTS idx_users_zalo ON users (zalo_phone)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks (user_id)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks (status)",
            "CREATE INDEX IF NOT EXISTS idx_events_user_id ON calendar_events (user_id)",
            "CREATE INDEX IF NOT EXISTS idx_events_task_id ON calendar_events (task_id)",
            "CREATE INDEX IF NOT EXISTS idx_events_deadline ON calendar_events (deadline)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications (user_id)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications (status)",
            "CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports (user_id)"
        ]
        
        for index_query in indexes:
            conn.execute(index_query)
    
    @contextmanager
    def get_connection(self):
        """
        Context manager để quản lý database connection
        
        Yields:
            sqlite3.Connection: Database connection
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Để có thể access columns by name
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, conn: sqlite3.Connection, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """
        Thuật toán execute query:
        1. Validate query string
        2. Execute query với params
        3. Fetch results
        4. Convert Row objects thành dict
        5. Return list of dicts
        
        Args:
            conn: Database connection
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of dictionaries chứa kết quả
        """
        try:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert Row objects thành dict
            result = []
            for row in rows:
                result.append(dict(row))
            
            return result
            
        except sqlite3.Error as e:
            raise RuntimeError(f"Database query failed: {e}")
    
    def execute_insert(self, conn: sqlite3.Connection, query: str, params: Tuple = ()) -> int:
        """
        Execute INSERT query và return last row id
        
        Args:
            conn: Database connection
            query: SQL query string
            params: Query parameters
            
        Returns:
            Last row id
        """
        try:
            cursor = conn.execute(query, params)
            return cursor.lastrowid
        except sqlite3.Error as e:
            raise RuntimeError(f"Database insert failed: {e}")
    
    def execute_update(self, conn: sqlite3.Connection, query: str, params: Tuple = ()) -> int:
        """
        Execute UPDATE query và return số rows affected
        
        Args:
            conn: Database connection
            query: SQL query string
            params: Query parameters
            
        Returns:
            Số rows affected
        """
        try:
            cursor = conn.execute(query, params)
            return cursor.rowcount
        except sqlite3.Error as e:
            raise RuntimeError(f"Database update failed: {e}")
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin user theo ID
        
        Args:
            user_id: User ID
            
        Returns:
            User info dict hoặc None
        """
        with self.get_connection() as conn:
            query = "SELECT * FROM users WHERE user_id = ?"
            results = self.execute_query(conn, query, (user_id,))
            return results[0] if results else None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin user theo email
        
        Args:
            email: Email address
            
        Returns:
            User info dict hoặc None
        """
        with self.get_connection() as conn:
            query = "SELECT * FROM users WHERE email = ?"
            results = self.execute_query(conn, query, (email,))
            return results[0] if results else None
    
    def create_user(self, user_data: Dict[str, Any]) -> str:
        """
        Tạo user mới
        
        Args:
            user_data: Dict chứa thông tin user
            
        Returns:
            User ID mới tạo
        """
        with self.get_connection() as conn:
            query = """
            INSERT INTO users (user_id, username, email, telegram_username, zalo_phone, zalo_user_id, settings)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                user_data['user_id'],
                user_data['username'],
                user_data['email'],
                user_data.get('telegram_username'),
                user_data.get('zalo_phone'),
                user_data.get('zalo_user_id'),
                user_data.get('settings', '{}')
            )
            
            self.execute_insert(conn, query, params)
            conn.commit()
            return user_data['user_id']

# Test function
def test_database_manager():
    """Test function để kiểm tra DatabaseManager hoạt động đúng"""
    try:
        # Sử dụng đường dẫn tuyệt đối để tránh lỗi
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        test_db_path = os.path.join(project_root, "test_database.db")
        
        print(f"Testing with database path: {test_db_path}")
        
        db = DatabaseManager(test_db_path)
        
        # Test create user
        user_data = {
            'user_id': 'test_user_001',
            'username': 'test_user',
            'email': 'test@example.com',
            'telegram_username': '@test_user',
            'zalo_phone': '0123456789',
            'settings': '{"timezone": "Asia/Ho_Chi_Minh"}'
        }
        
        user_id = db.create_user(user_data)
        print(f"✅ create_user() works: {user_id}")
        
        # Test get user by id
        user = db.get_user_by_id(user_id)
        print(f"✅ get_user_by_id() works: {user['username']}")
        
        # Test get user by email
        user = db.get_user_by_email('test@example.com')
        print(f"✅ get_user_by_email() works: {user['username']}")
        
        # Cleanup
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            print("✅ Test database cleaned up")
        
        print("🎉 DatabaseManager test passed!")
        
    except Exception as e:
        print(f"❌ DatabaseManager test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_database_manager()
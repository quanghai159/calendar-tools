# -*- coding: utf-8 -*-
"""
TASK CREATOR MODULE
==================

Mô tả: Tạo và quản lý tác vụ cho người dùng
Cách hoạt động:
1. Tạo tác vụ mới từ Google Sheet URL
2. Validate Google Sheet URL và quyền truy cập
3. Extract Google Sheet ID từ URL
4. Tạo task instance cho user
5. Cấu hình sync settings

Thuật toán chính:
- Parse Google Sheet URL để lấy Sheet ID
- Validate URL format và accessibility
- Generate unique task ID
- Tạo task record trong database
- Set up default sync settings

Hướng dẫn sử dụng:
1. Gọi create_task() để tạo tác vụ mới
2. Gọi get_task_info() để lấy thông tin tác vụ
3. Gọi update_task_settings() để cập nhật cài đặt
4. Gọi validate_task() để kiểm tra tác vụ hợp lệ

Ví dụ:
    creator = TaskCreator(db_manager)
    task_id = creator.create_task(user_id, "https://docs.google.com/spreadsheets/...")
"""

import uuid
import re
import json
import os
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime
from urllib.parse import urlparse, parse_qs

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

class TaskCreator:
    def __init__(self, db_manager):
        """
        Khởi tạo TaskCreator
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db = db_manager
        # Regex patterns để parse Google Sheets URL
        self.sheet_url_patterns = [
            r'https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)',
            r'https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)/edit',
            r'https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)/edit#gid=\d+'
        ]
    
    def create_task(self, user_id: str, google_sheet_url: str, task_settings: Optional[Dict[str, Any]] = None) -> str:
        """
        Thuật toán tạo tác vụ mới:
        1. Validate user tồn tại
        2. Parse và validate Google Sheet URL
        3. Extract Google Sheet ID
        4. Generate unique task ID
        5. Tạo task record trong database
        6. Return task ID
        
        Args:
            user_id: ID của user sở hữu tác vụ
            google_sheet_url: URL của Google Sheet
            task_settings: Cài đặt tùy chọn cho tác vụ
            
        Returns:
            Task ID mới tạo
        """
        # Bước 1: Validate user tồn tại
        self._validate_user_exists(user_id)
        
        # Bước 2: Parse và validate Google Sheet URL
        sheet_id = self._parse_google_sheet_url(google_sheet_url)
        
        # Bước 3: Generate unique task ID
        task_id = self._generate_task_id()
        
        # Bước 4: Tạo task data
        task_data = self._create_task_data(user_id, task_id, google_sheet_url, sheet_id, task_settings)
        
        # Bước 5: Insert vào database
        try:
            created_task_id = self._insert_task_to_db(task_data)
            print(f"✅ Task created successfully: {created_task_id}")
            return created_task_id
        except Exception as e:
            raise RuntimeError(f"Failed to create task: {e}")
    
    def _validate_user_exists(self, user_id: str) -> None:
        """
        Kiểm tra user có tồn tại không
        
        Args:
            user_id: User ID cần kiểm tra
        """
        user = self.db.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")
        if not user.get('is_active', False):
            raise ValueError(f"User is not active: {user_id}")
    
    def _parse_google_sheet_url(self, url: str) -> str:
        """
        Thuật toán parse Google Sheet URL:
        1. Validate URL format
        2. Thử các regex patterns
        3. Extract Sheet ID
        4. Validate Sheet ID format
        
        Args:
            url: Google Sheet URL
            
        Returns:
            Google Sheet ID
        """
        if not url or not isinstance(url, str):
            raise ValueError("Invalid URL: URL cannot be empty")
        
        # Bước 1: Validate URL format cơ bản
        if not url.startswith('https://docs.google.com/spreadsheets/'):
            raise ValueError("Invalid URL: Must be a Google Sheets URL")
        
        # Bước 2: Thử các regex patterns
        for pattern in self.sheet_url_patterns:
            match = re.search(pattern, url)
            if match:
                sheet_id = match.group(1)
                # Bước 3: Validate Sheet ID format
                if self._validate_sheet_id(sheet_id):
                    return sheet_id
        
        # Bước 4: Nếu không match pattern nào
        raise ValueError(f"Could not extract Sheet ID from URL: {url}")
    
    def _validate_sheet_id(self, sheet_id: str) -> bool:
        """
        Validate Google Sheet ID format
        
        Args:
            sheet_id: Sheet ID cần validate
            
        Returns:
            True nếu format hợp lệ
        """
        # Google Sheet ID thường có 44 ký tự, chứa chữ cái, số, gạch ngang và gạch dưới
        if len(sheet_id) < 20 or len(sheet_id) > 50:
            return False
        
        # Chỉ chứa ký tự hợp lệ
        if not re.match(r'^[a-zA-Z0-9_-]+$', sheet_id):
            return False
        
        return True
    
    def _generate_task_id(self) -> str:
        """
        Generate unique task ID
        
        Returns:
            Unique task ID
        """
        return f"task_{uuid.uuid4().hex[:12]}"
    
    def _create_task_data(self, user_id: str, task_id: str, sheet_url: str, sheet_id: str, settings: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Tạo task data để insert vào database
        
        Args:
            user_id: User ID
            task_id: Task ID
            sheet_url: Google Sheet URL
            sheet_id: Google Sheet ID
            settings: Task settings
            
        Returns:
            Task data dict
        """
        # Default settings
        default_settings = {
            'sync_interval': '15_minutes',
            'auto_reminder': True,
            'report_frequency': 'daily',
            'notification_enabled': True,
            'created_at': datetime.now().isoformat()
        }
        
        # Merge với user settings nếu có
        if settings:
            default_settings.update(settings)
        
        return {
            'task_id': task_id,
            'user_id': user_id,
            'google_sheet_url': sheet_url,
            'google_sheet_id': sheet_id,
            'status': 'active',
            'settings': json.dumps(default_settings, ensure_ascii=False)
        }
    
    def _insert_task_to_db(self, task_data: Dict[str, Any]) -> str:
        """
        Insert task vào database
        
        Args:
            task_data: Task data dict
            
        Returns:
            Task ID
        """
        with self.db.get_connection() as conn:
            query = """
            INSERT INTO tasks (task_id, user_id, google_sheet_url, google_sheet_id, status, settings)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            params = (
                task_data['task_id'],
                task_data['user_id'],
                task_data['google_sheet_url'],
                task_data['google_sheet_id'],
                task_data['status'],
                task_data['settings']
            )
            
            self.db.execute_insert(conn, query, params)
            conn.commit()
            return task_data['task_id']
    
    def get_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin tác vụ theo ID
        
        Args:
            task_id: Task ID
            
        Returns:
            Task info dict hoặc None
        """
        with self.db.get_connection() as conn:
            query = "SELECT * FROM tasks WHERE task_id = ?"
            results = self.db.execute_query(conn, query, (task_id,))
            return results[0] if results else None
    
    def get_user_tasks(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Lấy tất cả tác vụ của user
        
        Args:
            user_id: User ID
            
        Returns:
            List các task dict
        """
        with self.db.get_connection() as conn:
            query = "SELECT * FROM tasks WHERE user_id = ? ORDER BY created_at DESC"
            return self.db.execute_query(conn, query, (user_id,))
    
    def update_task_settings(self, task_id: str, new_settings: Dict[str, Any]) -> bool:
        """
        Cập nhật settings của tác vụ
        
        Args:
            task_id: Task ID
            new_settings: New settings dict
            
        Returns:
            True nếu update thành công
        """
        try:
            # Lấy settings hiện tại
            task = self.get_task_info(task_id)
            if not task:
                return False
            
            # Merge settings
            current_settings = json.loads(task['settings'])
            current_settings.update(new_settings)
            
            # Update trong database
            with self.db.get_connection() as conn:
                query = "UPDATE tasks SET settings = ? WHERE task_id = ?"
                self.db.execute_update(conn, query, (json.dumps(current_settings, ensure_ascii=False), task_id))
                conn.commit()
            
            return True
        except Exception as e:
            print(f"Error updating task settings: {e}")
            return False
    
    def update_task_status(self, task_id: str, status: str) -> bool:
        """
        Cập nhật trạng thái tác vụ
        
        Args:
            task_id: Task ID
            status: Trạng thái mới (active, paused, stopped)
            
        Returns:
            True nếu update thành công
        """
        valid_statuses = ['active', 'paused', 'stopped']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
        
        try:
            with self.db.get_connection() as conn:
                query = "UPDATE tasks SET status = ? WHERE task_id = ?"
                self.db.execute_update(conn, query, (status, task_id))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error updating task status: {e}")
            return False
    
    def validate_task(self, task_id: str) -> bool:
        """
        Kiểm tra tác vụ có hợp lệ không
        
        Args:
            task_id: Task ID
            
        Returns:
            True nếu tác vụ hợp lệ
        """
        task = self.get_task_info(task_id)
        return task is not None and task.get('status') == 'active'
    
    def delete_task(self, task_id: str) -> bool:
        """
        Xóa tác vụ (soft delete - chỉ đổi status thành stopped)
        
        Args:
            task_id: Task ID
            
        Returns:
            True nếu xóa thành công
        """
        return self.update_task_status(task_id, 'stopped')

# Test function
def test_task_creator():
    """Test function để kiểm tra TaskCreator hoạt động đúng"""
    try:
        from core.database_manager import DatabaseManager
        
        # Tạo test database
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        test_db_path = os.path.join(project_root, "test_task_db.db")
        
        db = DatabaseManager(test_db_path)
        creator = TaskCreator(db)
        
        # Tạo test user trước
        from user_management.user_registry import UserRegistry
        registry = UserRegistry(db)
        
        user_data = {
            'username': 'test_user_task',
            'email': 'test_task@example.com',
            'telegram_username': '@testtask'
        }
        
        user_id = registry.register_user(user_data)
        print(f"✅ Test user created: {user_id}")
        
        # Test create task
        google_sheet_url = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit"
        task_id = creator.create_task(user_id, google_sheet_url)
        print(f"✅ create_task() works: {task_id}")
        
        # Test get task info
        task_info = creator.get_task_info(task_id)
        print(f"✅ get_task_info() works: {task_info['google_sheet_id']}")
        
        # Test get user tasks
        user_tasks = creator.get_user_tasks(user_id)
        print(f"✅ get_user_tasks() works: {len(user_tasks)} tasks")
        
        # Test validate task
        is_valid = creator.validate_task(task_id)
        print(f"✅ validate_task() works: {is_valid}")
        
        # Test update task settings
        new_settings = {'sync_interval': '30_minutes'}
        updated = creator.update_task_settings(task_id, new_settings)
        print(f"✅ update_task_settings() works: {updated}")
        
        # Test update task status
        status_updated = creator.update_task_status(task_id, 'paused')
        print(f"✅ update_task_status() works: {status_updated}")
        
        # Cleanup
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            print("✅ Test database cleaned up")
        
        print("🎉 TaskCreator test passed!")
        
    except Exception as e:
        print(f"❌ TaskCreator test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_task_creator()
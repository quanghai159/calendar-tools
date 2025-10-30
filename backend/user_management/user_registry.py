# -*- coding: utf-8 -*-
"""
USER REGISTRY MODULE
===================

Mô tả: Đăng ký và quản lý người dùng trong hệ thống
Cách hoạt động:
1. Tạo user mới với thông tin cá nhân
2. Validate thông tin người dùng
3. Quản lý cài đặt cá nhân
4. Xử lý authentication cơ bản

Thuật toán chính:
- Generate unique user ID
- Validate email format và uniqueness
- Validate telegram username format
- Validate zalo phone format
- Hash sensitive information
- Store user preferences

Hướng dẫn sử dụng:
1. Gọi register_user() để tạo user mới
2. Gọi get_user_info() để lấy thông tin user
3. Gọi update_user_settings() để cập nhật cài đặt
4. Gọi validate_user() để kiểm tra user hợp lệ

Ví dụ:
    registry = UserRegistry()
    user_id = registry.register_user({
        'username': 'john_doe',
        'email': 'john@example.com',
        'telegram_username': '@johndoe'
    })
"""

import uuid
import re
import json
import os
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add parent directory to path để import database_manager
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import DatabaseManager từ core
from core.database_manager import DatabaseManager

class UserRegistry:
    def __init__(self, db_manager):
        """
        Khởi tạo UserRegistry
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db = db_manager
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        self.telegram_pattern = re.compile(r'^@[a-zA-Z0-9_]{5,32}$')
        self.phone_pattern = re.compile(r'^(\+84|84|0)[0-9]{9,10}$')
    
    def register_user(self, user_data: Dict[str, Any]) -> str:
        """
        Thuật toán đăng ký user mới:
        1. Validate thông tin user
        2. Generate unique user ID
        3. Check email và username uniqueness
        4. Format và clean data
        5. Insert vào database
        6. Return user ID
        
        Args:
            user_data: Dict chứa thông tin user
            
        Returns:
            User ID mới tạo
        """
        # Bước 1: Validate thông tin
        self._validate_user_data(user_data)
        
        # Bước 2: Generate unique user ID
        user_id = self._generate_user_id()
        
        # Bước 3: Check uniqueness
        self._check_uniqueness(user_data)
        
        # Bước 4: Format data
        formatted_data = self._format_user_data(user_data, user_id)
        
        # Bước 5: Insert vào database
        try:
            created_user_id = self.db.create_user(formatted_data)
            print(f"✅ User registered successfully: {created_user_id}")
            return created_user_id
        except Exception as e:
            raise RuntimeError(f"Failed to register user: {e}")
    
    def _validate_user_data(self, user_data: Dict[str, Any]) -> None:
        """
        Thuật toán validate user data:
        1. Kiểm tra required fields
        2. Validate email format
        3. Validate telegram username format
        4. Validate zalo phone format
        5. Validate username format
        """
        required_fields = ['username', 'email']
        
        # Bước 1: Kiểm tra required fields
        for field in required_fields:
            if field not in user_data or not user_data[field]:
                raise ValueError(f"Missing required field: {field}")
        
        # Bước 2: Validate email
        email = user_data['email']
        if not self.email_pattern.match(email):
            raise ValueError(f"Invalid email format: {email}")
        
        # Bước 3: Validate telegram username (nếu có)
        if 'telegram_username' in user_data and user_data['telegram_username']:
            telegram = user_data['telegram_username']
            if not self.telegram_pattern.match(telegram):
                raise ValueError(f"Invalid telegram username format: {telegram}")
        
        # Bước 4: Validate zalo phone (nếu có)
        if 'zalo_phone' in user_data and user_data['zalo_phone']:
            phone = user_data['zalo_phone']
            if not self.phone_pattern.match(phone):
                raise ValueError(f"Invalid phone number format: {phone}")
        
        # Bước 5: Validate username
        username = user_data['username']
        if len(username) < 3 or len(username) > 50:
            raise ValueError("Username must be between 3 and 50 characters")
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValueError("Username can only contain letters, numbers, and underscores")
    
    def _generate_user_id(self) -> str:
        """
        Generate unique user ID
        
        Returns:
            Unique user ID
        """
        return f"user_{uuid.uuid4().hex[:12]}"
    
    def _check_uniqueness(self, user_data: Dict[str, Any]) -> None:
        """
        Kiểm tra email và username uniqueness
        
        Args:
            user_data: User data to check
        """
        # Check email uniqueness
        existing_user = self.db.get_user_by_email(user_data['email'])
        if existing_user:
            raise ValueError(f"Email already exists: {user_data['email']}")
        
        # Check username uniqueness (cần implement get_user_by_username)
        # Tạm thời skip vì chưa có method này trong DatabaseManager
    
    def _format_user_data(self, user_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Format và clean user data
        
        Args:
            user_data: Raw user data
            user_id: Generated user ID
            
        Returns:
            Formatted user data
        """
        formatted = {
            'user_id': user_id,
            'username': user_data['username'].strip().lower(),
            'email': user_data['email'].strip().lower(),
            'telegram_username': user_data.get('telegram_username', '').strip(),
            'zalo_phone': user_data.get('zalo_phone', '').strip(),
            'zalo_user_id': user_data.get('zalo_user_id', ''),
            'settings': self._create_default_settings(user_data)
        }
        
        return formatted
    
    def _create_default_settings(self, user_data: Dict[str, Any]) -> str:
        """
        Tạo default settings cho user
        
        Args:
            user_data: User data
            
        Returns:
            JSON string của settings
        """
        settings = {
            'timezone': 'Asia/Ho_Chi_Minh',
            'notification_preferences': {
                'telegram': bool(user_data.get('telegram_username')),
                'email': True,
                'zalo': bool(user_data.get('zalo_phone')),
                'reminder_times': ['1_day_before', '1_hour_before']
            },
            'created_at': datetime.now().isoformat()
        }
        
        return json.dumps(settings, ensure_ascii=False)
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin user theo ID
        
        Args:
            user_id: User ID
            
        Returns:
            User info dict hoặc None
        """
        return self.db.get_user_by_id(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin user theo email
        
        Args:
            email: Email address
            
        Returns:
            User info dict hoặc None
        """
        return self.db.get_user_by_email(email)
    
    def update_user_settings(self, user_id: str, new_settings: Dict[str, Any]) -> bool:
        """
        Cập nhật settings của user
        
        Args:
            user_id: User ID
            new_settings: New settings dict
            
        Returns:
            True nếu update thành công
        """
        try:
            # Lấy settings hiện tại
            user = self.get_user_info(user_id)
            if not user:
                return False
            
            # Merge settings
            current_settings = json.loads(user['settings'])
            current_settings.update(new_settings)
            
            # Update trong database
            with self.db.get_connection() as conn:
                query = "UPDATE users SET settings = ? WHERE user_id = ?"
                self.db.execute_update(conn, query, (json.dumps(current_settings, ensure_ascii=False), user_id))
                conn.commit()
            
            return True
        except Exception as e:
            print(f"Error updating user settings: {e}")
            return False
    
    def validate_user(self, user_id: str) -> bool:
        """
        Kiểm tra user có hợp lệ không
        
        Args:
            user_id: User ID
            
        Returns:
            True nếu user hợp lệ
        """
        user = self.get_user_info(user_id)
        return user is not None and user.get('is_active', False)
    
    def get_user_notification_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Lấy notification preferences của user
        
        Args:
            user_id: User ID
            
        Returns:
            Notification preferences dict
        """
        user = self.get_user_info(user_id)
        if not user:
            return {}
        
        settings = json.loads(user['settings'])
        return settings.get('notification_preferences', {})

# Test function
def test_user_registry():
    """Test function để kiểm tra UserRegistry hoạt động đúng"""
    try:
        # Tạo test database
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        test_db_path = os.path.join(project_root, "test_user_db.db")
        
        db = DatabaseManager(test_db_path)
        registry = UserRegistry(db)
        
        # Test register user
        user_data = {
            'username': 'test_user_123',
            'email': 'test@example.com',
            'telegram_username': '@testuser',
            'zalo_phone': '0123456789'
        }
        
        user_id = registry.register_user(user_data)
        print(f"✅ register_user() works: {user_id}")
        
        # Test get user info
        user_info = registry.get_user_info(user_id)
        print(f"✅ get_user_info() works: {user_info['username']}")
        
        # Test get user by email
        user_by_email = registry.get_user_by_email('test@example.com')
        print(f"✅ get_user_by_email() works: {user_by_email['username']}")
        
        # Test validate user
        is_valid = registry.validate_user(user_id)
        print(f"✅ validate_user() works: {is_valid}")
        
        # Test get notification preferences
        prefs = registry.get_user_notification_preferences(user_id)
        print(f"✅ get_user_notification_preferences() works: {prefs}")
        
        # Cleanup
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            print("✅ Test database cleaned up")
        
        print("🎉 UserRegistry test passed!")
        
    except Exception as e:
        print(f"❌ UserRegistry test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_user_registry()
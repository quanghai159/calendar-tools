# -*- coding: utf-8 -*-
"""
CONFIG LOADER MODULE
===================

Mô tả: Đọc và quản lý cấu hình từ file JSON
Cách hoạt động:
1. Đọc file config.json
2. Validate cấu hình
3. Cung cấp interface để truy cập config
4. Hỗ trợ reload config khi cần

Thuật toán:
- Sử dụng JSON parser để đọc file
- Cache config trong memory để tăng performance
- Validate required fields
- Cung cấp default values cho optional fields

Hướng dẫn sử dụng:
1. Gọi get_config() để lấy toàn bộ config
2. Gọi get_section('section_name') để lấy section cụ thể
3. Gọi reload_config() để reload từ file

Ví dụ:
    config = ConfigLoader()
    db_config = config.get_section('database')
    bot_token = config.get_value('notifications.telegram.bot_token')
"""

import json
import os
from typing import Dict, Any, Optional

class ConfigLoader:
    def __init__(self, config_file: str = "config/config.json"):
        """
        Khởi tạo ConfigLoader
        
        Args:
            config_file: Đường dẫn đến file config
        """
        self.config_file = config_file
        self._config = None
        self._load_config()
    
    def _load_config(self) -> None:
        """
        Thuật toán load config:
        1. Kiểm tra file config có tồn tại không
        2. Đọc file JSON
        3. Parse JSON thành Python dict
        4. Validate cấu hình cơ bản
        5. Cache vào memory
        """
        try:
            # Bước 1: Kiểm tra file tồn tại
            if not os.path.exists(self.config_file):
                raise FileNotFoundError(f"Config file not found: {self.config_file}")
            
            # Bước 2: Đọc file JSON
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            
            # Bước 3: Validate cấu hình cơ bản
            self._validate_config()
            
            print(f"✅ Config loaded successfully from {self.config_file}")
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load config: {e}")
    
    def _validate_config(self) -> None:
        """
        Thuật toán validate config:
        1. Kiểm tra các section bắt buộc
        2. Kiểm tra các field bắt buộc trong mỗi section
        3. Validate data types
        4. Set default values cho optional fields
        """
        required_sections = ['database', 'notifications', 'app']
        
        # Bước 1: Kiểm tra sections bắt buộc
        for section in required_sections:
            if section not in self._config:
                raise ValueError(f"Missing required section: {section}")
        
        # Bước 2: Validate database config
        db_config = self._config['database']
        if 'type' not in db_config:
            raise ValueError("Missing database.type")
        
        # Bước 3: Validate notifications config
        notif_config = self._config['notifications']
        required_notif_sections = ['telegram', 'email', 'zalo']
        for section in required_notif_sections:
            if section not in notif_config:
                raise ValueError(f"Missing notification section: {section}")
        
        # Bước 4: Set default values
        self._set_default_values()
    
    def _set_default_values(self) -> None:
        """
        Thuật toán set default values:
        1. Duyệt qua các section
        2. Kiểm tra field nào thiếu
        3. Set giá trị mặc định phù hợp
        """
        # Default cho database
        if 'path' not in self._config['database']:
            self._config['database']['path'] = 'database/calendar_tools.db'
        
        # Default cho app
        app_config = self._config['app']
        if 'host' not in app_config:
            app_config['host'] = '0.0.0.0'
        if 'port' not in app_config:
            app_config['port'] = 5000
        if 'debug' not in app_config:
            app_config['debug'] = True
        if 'timezone' not in app_config:
            app_config['timezone'] = 'Asia/Ho_Chi_Minh'
    
    def get_config(self) -> Dict[str, Any]:
        """
        Lấy toàn bộ config
        
        Returns:
            Dict chứa toàn bộ cấu hình
        """
        return self._config.copy()
    
    def get_section(self, section_name: str) -> Dict[str, Any]:
        """
        Lấy một section cụ thể
        
        Args:
            section_name: Tên section cần lấy
            
        Returns:
            Dict chứa config của section
        """
        if section_name not in self._config:
            raise KeyError(f"Section '{section_name}' not found")
        return self._config[section_name].copy()
    
    def get_value(self, key_path: str, default: Any = None) -> Any:
        """
        Lấy giá trị theo đường dẫn key (dot notation)
        
        Args:
            key_path: Đường dẫn key (vd: 'notifications.telegram.bot_token')
            default: Giá trị mặc định nếu không tìm thấy
            
        Returns:
            Giá trị config hoặc default
        """
        keys = key_path.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def reload_config(self) -> None:
        """
        Reload config từ file
        """
        self._load_config()
    
    def update_config(self, section: str, key: str, value: Any) -> None:
        """
        Cập nhật giá trị config trong memory
        
        Args:
            section: Tên section
            key: Tên key
            value: Giá trị mới
        """
        if section not in self._config:
            self._config[section] = {}
        self._config[section][key] = value

# Test function để kiểm tra module
def test_config_loader():
    """Test function để kiểm tra ConfigLoader hoạt động đúng"""
    try:
        config = ConfigLoader()
        
        # Test get_config
        full_config = config.get_config()
        print("✅ get_config() works")
        
        # Test get_section
        db_config = config.get_section('database')
        print("✅ get_section() works")
        
        # Test get_value
        db_type = config.get_value('database.type')
        print(f"✅ get_value() works: {db_type}")
        
        print("🎉 ConfigLoader test passed!")
        
    except Exception as e:
        print(f"❌ ConfigLoader test failed: {e}")

if __name__ == "__main__":
    test_config_loader()
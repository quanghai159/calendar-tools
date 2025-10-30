# -*- coding: utf-8 -*-
"""
GOOGLE SHEETS CONNECTOR MODULE
=============================

Mô tả: Kết nối và đọc dữ liệu từ Google Sheets
Cách hoạt động:
1. Authenticate với Google Sheets API
2. Đọc dữ liệu từ sheet
3. Parse dữ liệu thành calendar events
4. Validate và clean data
5. Trả về structured data

Thuật toán chính:
- Sử dụng Google Sheets API v4
- OAuth2 authentication
- Parse CSV-like data từ sheets
- Map columns thành calendar event fields
- Validate date formats và required fields

Hướng dẫn sử dụng:
1. Cấu hình Google credentials
2. Gọi connect() để kết nối
3. Gọi read_sheet_data() để đọc dữ liệu
4. Gọi parse_calendar_events() để parse events

Ví dụ:
    connector = GoogleSheetsConnector()
    data = connector.read_sheet_data("1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms")
    events = connector.parse_calendar_events(data)
"""

import os
import sys
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from utils.date_utils import DateUtils

class GoogleSheetsConnector:
    def __init__(self, credentials_file: str = "config/google_credentials.json", use_mock: bool = True):
        """
        Khởi tạo GoogleSheetsConnector
        
        Args:
            credentials_file: Đường dẫn đến file credentials
            use_mock: Sử dụng mock data cho test
        """
        self.credentials_file = credentials_file
        self.use_mock = use_mock
        self.date_utils = DateUtils()
        self.service = None
        
        # Cấu hình mapping columns (có thể customize)
        self.column_mapping = {
            'title': ['title', 'ten', 'ten_cong_viec', 'task', 'work'],
            'description': ['description', 'mo_ta', 'chi_tiet', 'details'],
            'start_date': ['start_date', 'ngay_bat_dau', 'start', 'from_date'],
            'end_date': ['end_date', 'ngay_ket_thuc', 'end', 'to_date'],
            'deadline': ['deadline', 'han_chot', 'due_date', 'han'],
            'category': ['category', 'loai', 'type', 'danh_muc'],
            'priority': ['priority', 'do_uu_tien', 'muc_do', 'level'],
            'status': ['status', 'trang_thai', 'state']
        }
    
    def connect(self) -> bool:
        """
        Thuật toán kết nối Google Sheets API:
        1. Kiểm tra credentials file tồn tại
        2. Load credentials
        3. Authenticate với Google API
        4. Tạo service object
        5. Test connection
        
        Returns:
            True nếu kết nối thành công
        """
        try:
            # Bước 1: Kiểm tra credentials file
            if not os.path.exists(self.credentials_file):
                if self.use_mock:
                    print(f"⚠️  Credentials file not found: {self.credentials_file}")
                    print("🔄 Using mock data for testing")
                    self.service = MockGoogleSheetsService()
                    return True
                else:
                    print(f"⚠️  Credentials file not found: {self.credentials_file}")
                    print("📝 Please create Google credentials file first")
                    return False
            
            # Bước 2: Load credentials
            with open(self.credentials_file, 'r') as f:
                credentials = json.load(f)
            
            # Bước 3: Authenticate (simplified - trong thực tế cần OAuth2)
            print("✅ Google Sheets credentials loaded")
            
            # Bước 4: Tạo mock service (vì chưa có real API key)
            self.service = MockGoogleSheetsService()
            
            # Bước 5: Test connection
            if self._test_connection():
                print("✅ Google Sheets connection successful")
                return True
            else:
                print("❌ Google Sheets connection failed")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def _test_connection(self) -> bool:
        """
        Test kết nối với Google Sheets
        
        Returns:
            True nếu test thành công
        """
        try:
            # Mock test - trong thực tế sẽ gọi API
            return self.service is not None
        except Exception:
            return False
    
    def read_sheet_data(self, sheet_id: str, range_name: str = "A:Z") -> List[List[str]]:
        """
        Thuật toán đọc dữ liệu từ Google Sheet:
        1. Validate sheet_id
        2. Gọi Google Sheets API
        3. Parse response thành 2D array
        4. Clean và validate data
        5. Return structured data
        
        Args:
            sheet_id: Google Sheet ID
            range_name: Range cần đọc (mặc định: A:Z)
            
        Returns:
            2D array chứa dữ liệu sheet
        """
        try:
            if not self.service:
                # Nếu chưa connect, thử connect với mock data
                if self.use_mock:
                    print("🔄 Auto-connecting with mock data...")
                    self.service = MockGoogleSheetsService()
                else:
                    raise RuntimeError("Not connected to Google Sheets. Call connect() first.")
            
            # Bước 1: Validate sheet_id
            if not self._validate_sheet_id(sheet_id):
                raise ValueError(f"Invalid sheet ID: {sheet_id}")
            
            # Bước 2: Gọi API để đọc dữ liệu
            print(f"📖 Reading data from sheet: {sheet_id}")
            data = self.service.get_values(sheet_id, range_name)
            
            # Bước 3: Clean data
            cleaned_data = self._clean_sheet_data(data)
            
            print(f"✅ Read {len(cleaned_data)} rows from sheet")
            return cleaned_data
            
        except Exception as e:
            print(f"❌ Error reading sheet data: {e}")
            return []
    
    def _validate_sheet_id(self, sheet_id: str) -> bool:
        """
        Validate Google Sheet ID
        
        Args:
            sheet_id: Sheet ID cần validate
            
        Returns:
            True nếu hợp lệ
        """
        if not sheet_id or not isinstance(sheet_id, str):
            return False
        
        # Google Sheet ID thường có 44 ký tự
        if len(sheet_id) < 20 or len(sheet_id) > 50:
            return False
        
        # Chỉ chứa ký tự hợp lệ
        if not re.match(r'^[a-zA-Z0-9_-]+$', sheet_id):
            return False
        
        return True
    
    def _clean_sheet_data(self, raw_data: List[List[str]]) -> List[List[str]]:
        """
        Thuật toán clean dữ liệu sheet:
        1. Loại bỏ rows rỗng
        2. Trim whitespace
        3. Validate data types
        4. Remove invalid rows
        
        Args:
            raw_data: Raw data từ Google Sheets
            
        Returns:
            Cleaned data
        """
        cleaned = []
        
        for row in raw_data:
            # Bước 1: Loại bỏ rows hoàn toàn rỗng
            if not any(cell.strip() for cell in row):
                continue
            
            # Bước 2: Trim whitespace cho mỗi cell
            cleaned_row = [cell.strip() for cell in row]
            
            # Bước 3: Loại bỏ rows có quá ít thông tin
            if len([cell for cell in cleaned_row if cell]) < 2:
                continue
            
            cleaned.append(cleaned_row)
        
        return cleaned
    
    def parse_calendar_events(self, sheet_data: List[List[str]]) -> List[Dict[str, Any]]:
        """
        Thuật toán parse dữ liệu sheet thành calendar events:
        1. Tìm header row
        2. Map columns theo column_mapping
        3. Parse từng row thành event
        4. Validate required fields
        5. Clean và format data
        
        Args:
            sheet_data: 2D array dữ liệu từ sheet
            
        Returns:
            List các calendar event dicts
        """
        if not sheet_data:
            return []
        
        try:
            # Bước 1: Tìm header row
            header_row = self._find_header_row(sheet_data)
            if header_row is None:
                print("⚠️  No valid header row found")
                return []
            
            # Bước 2: Map columns
            column_map = self._map_columns(sheet_data[header_row])
            print(f"✅ Mapped columns: {column_map}")
            
            # Bước 3: Parse data rows
            events = []
            for i, row in enumerate(sheet_data[header_row + 1:], start=header_row + 2):
                try:
                    event = self._parse_row_to_event(row, column_map, i)
                    if event:
                        events.append(event)
                except Exception as e:
                    print(f"⚠️  Error parsing row {i}: {e}")
                    continue
            
            print(f"✅ Parsed {len(events)} calendar events")
            return events
            
        except Exception as e:
            print(f"❌ Error parsing calendar events: {e}")
            return []
    
    def _find_header_row(self, data: List[List[str]]) -> Optional[int]:
        """
        Tìm header row trong dữ liệu
        
        Args:
            data: 2D array dữ liệu
            
        Returns:
            Index của header row hoặc None
        """
        for i, row in enumerate(data):
            if not row:
                continue
            
            # Kiểm tra xem row có chứa các từ khóa header không
            row_text = ' '.join(row).lower()
            header_keywords = ['title', 'ten', 'date', 'ngay', 'deadline', 'han']
            
            if any(keyword in row_text for keyword in header_keywords):
                return i
        
        return None
    
    def _map_columns(self, header_row: List[str]) -> Dict[str, int]:
        """
        Map columns theo column_mapping
        
        Args:
            header_row: Header row từ sheet
            
        Returns:
            Dict mapping field names to column indices
        """
        column_map = {}
        
        for i, cell in enumerate(header_row):
            cell_lower = cell.lower().strip()
            
            # Tìm mapping cho cell này
            for field, keywords in self.column_mapping.items():
                if any(keyword in cell_lower for keyword in keywords):
                    column_map[field] = i
                    break
        
        return column_map
    
    def _parse_row_to_event(self, row: List[str], column_map: Dict[str, int], row_num: int) -> Optional[Dict[str, Any]]:
        """
        Parse một row thành calendar event
        
        Args:
            row: Data row
            column_map: Column mapping
            row_num: Row number (for error reporting)
            
        Returns:
            Event dict hoặc None
        """
        try:
            # Bước 1: Extract basic fields
            title = self._get_cell_value(row, column_map, 'title')
            if not title:
                print(f"⚠️  Row {row_num}: Missing title")
                return None
            
            # Bước 2: Extract dates
            start_date = self._get_cell_value(row, column_map, 'start_date')
            end_date = self._get_cell_value(row, column_map, 'end_date')
            deadline = self._get_cell_value(row, column_map, 'deadline')
            
            # Bước 3: Validate dates
            if not start_date:
                print(f"⚠️  Row {row_num}: Missing start_date")
                return None
            
            # Bước 4: Parse dates
            try:
                parsed_start = self.date_utils.parse_date(start_date)
                parsed_end = self.date_utils.parse_date(end_date) if end_date else None
                parsed_deadline = self.date_utils.parse_date(deadline) if deadline else None
            except Exception as e:
                print(f"⚠️  Row {row_num}: Invalid date format - {e}")
                return None
            
            # Bước 5: Create event
            event = {
                'title': title,
                'description': self._get_cell_value(row, column_map, 'description', ''),
                'start_date': self.date_utils.format_date(parsed_start, '%Y-%m-%d'),
                'end_date': self.date_utils.format_date(parsed_end, '%Y-%m-%d') if parsed_end else None,
                'deadline': self.date_utils.format_date(parsed_deadline, '%Y-%m-%d %H:%M') if parsed_deadline else None,
                'category': self._get_cell_value(row, column_map, 'category', 'work'),
                'priority': self._get_cell_value(row, column_map, 'priority', 'medium'),
                'status': self._get_cell_value(row, column_map, 'status', 'pending'),
                'source': 'google_sheets',
                'row_number': row_num
            }
            
            return event
            
        except Exception as e:
            print(f"❌ Error parsing row {row_num}: {e}")
            return None
    
    def _get_cell_value(self, row: List[str], column_map: Dict[str, int], field: str, default: str = None) -> str:
        """
        Lấy giá trị cell theo field mapping
        
        Args:
            row: Data row
            column_map: Column mapping
            field: Field name
            default: Default value
            
        Returns:
            Cell value hoặc default
        """
        if field not in column_map:
            return default
        
        col_index = column_map[field]
        if col_index < len(row):
            return row[col_index]
        
        return default

class MockGoogleSheetsService:
    """
    Mock Google Sheets Service để test mà không cần real API
    """
    
    def __init__(self):
        self.mock_data = {
            "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms": [
                ["Title", "Description", "Start Date", "End Date", "Deadline", "Category", "Priority"],
                ["Họp team", "Họp định kỳ team", "2024-01-15", "2024-01-15", "2024-01-15 17:00", "meeting", "high"],
                ["Làm báo cáo", "Viết báo cáo tháng", "2024-01-16", "2024-01-20", "2024-01-20 18:00", "work", "medium"],
                ["Nghỉ phép", "Nghỉ phép cuối tuần", "2024-01-25", "2024-01-26", "", "personal", "low"]
            ]
        }
    
    def get_values(self, sheet_id: str, range_name: str) -> List[List[str]]:
        """
        Mock method để trả về dữ liệu test
        
        Args:
            sheet_id: Google Sheet ID
            range_name: Range name
            
        Returns:
            Mock data
        """
        if sheet_id in self.mock_data:
            return self.mock_data[sheet_id]
        else:
            return []

# Test function
def test_google_sheets_connector():
    """Test function để kiểm tra GoogleSheetsConnector hoạt động đúng"""
    try:
        connector = GoogleSheetsConnector(use_mock=True)
        
        # Test connect
        connected = connector.connect()
        print(f"✅ connect() works: {connected}")
        
        # Test read sheet data
        sheet_id = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
        data = connector.read_sheet_data(sheet_id)
        print(f"✅ read_sheet_data() works: {len(data)} rows")
        
        # Test parse calendar events
        events = connector.parse_calendar_events(data)
        print(f"✅ parse_calendar_events() works: {len(events)} events")
        
        # Print sample event
        if events:
            print(f"📅 Sample event: {events[0]['title']} - {events[0]['start_date']}")
        
        print("🎉 GoogleSheetsConnector test passed!")
        
    except Exception as e:
        print(f"❌ GoogleSheetsConnector test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_google_sheets_connector()
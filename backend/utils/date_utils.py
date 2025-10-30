# -*- coding: utf-8 -*-
"""
DATE UTILS MODULE
================

Mô tả: Xử lý và chuyển đổi ngày tháng
Cách hoạt động:
1. Chuyển đổi giữa các format ngày tháng
2. Tính toán khoảng thời gian
3. Xử lý timezone
4. Format ngày tháng theo yêu cầu

Thuật toán chính:
- Sử dụng datetime và pytz để xử lý timezone
- Parse string thành datetime object
- Format datetime thành string theo format mong muốn
- Tính toán difference giữa 2 thời điểm

Hướng dẫn sử dụng:
1. Gọi parse_date() để parse string thành datetime
2. Gọi format_date() để format datetime thành string
3. Gọi calculate_difference() để tính khoảng thời gian
4. Gọi get_reminder_times() để lấy thời điểm nhắc nhở

Ví dụ:
    date_utils = DateUtils()
    dt = date_utils.parse_date("2024-01-01 10:00:00")
    formatted = date_utils.format_date(dt, "%d/%m/%Y %H:%M")
    diff = date_utils.calculate_difference(dt, datetime.now())
"""

from datetime import datetime, timedelta
import pytz
from typing import Optional, List, Dict, Any
import re

class DateUtils:
    def __init__(self, default_timezone: str = "Asia/Ho_Chi_Minh"):
        """
        Khởi tạo DateUtils
        
        Args:
            default_timezone: Timezone mặc định
        """
        self.default_timezone = pytz.timezone(default_timezone)
        self.supported_formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%d/%m/%Y",
            "%d-%m-%Y %H:%M:%S",
            "%d-%m-%Y %H:%M",
            "%d-%m-%Y"
        ]
    
    def parse_date(self, date_string: str, format: Optional[str] = None) -> datetime:
        """
        Thuật toán parse date:
        1. Nếu có format cụ thể, thử parse với format đó
        2. Nếu không có format, thử tất cả supported formats
        3. Nếu parse thành công, convert về timezone mặc định
        4. Nếu tất cả đều fail, raise exception
        
        Args:
            date_string: String chứa ngày tháng
            format: Format cổ thể (optional)
            
        Returns:
            datetime object
        """
        if not date_string:
            raise ValueError("Date string cannot be empty")
        
        # Bước 1: Thử parse với format cụ thể
        if format:
            try:
                dt = datetime.strptime(date_string, format)
                return self.default_timezone.localize(dt)
            except ValueError:
                raise ValueError(f"Cannot parse '{date_string}' with format '{format}'")
        
        # Bước 2: Thử tất cả supported formats
        for fmt in self.supported_formats:
            try:
                dt = datetime.strptime(date_string, fmt)
                return self.default_timezone.localize(dt)
            except ValueError:
                continue
        
        # Bước 3: Nếu tất cả đều fail
        raise ValueError(f"Cannot parse date string: '{date_string}'. Supported formats: {self.supported_formats}")
    
    def format_date(self, dt: datetime, format: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        Thuật toán format date:
        1. Convert datetime về timezone mặc định
        2. Format theo format string
        3. Return formatted string
        
        Args:
            dt: datetime object
            format: Format string
            
        Returns:
            Formatted date string
        """
        if not isinstance(dt, datetime):
            raise ValueError("Input must be datetime object")
        
        # Convert về timezone mặc định
        if dt.tzinfo is None:
            dt = self.default_timezone.localize(dt)
        else:
            dt = dt.astimezone(self.default_timezone)
        
        return dt.strftime(format)
    
    def calculate_difference(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Thuật toán tính khoảng thời gian:
        1. Đảm bảo cả 2 datetime đều có timezone
        2. Tính difference
        3. Chuyển đổi thành các đơn vị khác nhau
        4. Return dict chứa các thông tin
        
        Args:
            start_date: Thời điểm bắt đầu
            end_date: Thời điểm kết thúc
            
        Returns:
            Dict chứa thông tin khoảng thời gian
        """
        # Bước 1: Đảm bảo timezone
        if start_date.tzinfo is None:
            start_date = self.default_timezone.localize(start_date)
        if end_date.tzinfo is None:
            end_date = self.default_timezone.localize(end_date)
        
        # Bước 2: Tính difference
        diff = end_date - start_date
        
        # Bước 3: Chuyển đổi thành các đơn vị
        total_seconds = int(diff.total_seconds())
        days = diff.days
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return {
            "total_seconds": total_seconds,
            "days": days,
            "hours": hours,
            "minutes": minutes,
            "seconds": seconds,
            "human_readable": self._format_human_readable(days, hours, minutes)
        }
    
    def _format_human_readable(self, days: int, hours: int, minutes: int) -> str:
        """
        Format khoảng thời gian thành dạng dễ đọc
        
        Args:
            days: Số ngày
            hours: Số giờ
            minutes: Số phút
            
        Returns:
            String dễ đọc
        """
        parts = []
        
        if days > 0:
            parts.append(f"{days} ngày")
        if hours > 0:
            parts.append(f"{hours} giờ")
        if minutes > 0:
            parts.append(f"{minutes} phút")
        
        if not parts:
            return "0 phút"
        
        return " ".join(parts)
    
    def get_reminder_times(self, deadline: datetime, reminder_settings: List[str]) -> List[datetime]:
        """
        Thuật toán tính thời điểm nhắc nhở:
        1. Parse reminder_settings thành timedelta
        2. Tính toán thời điểm nhắc nhở
        3. Filter ra các thời điểm đã qua
        4. Return danh sách thời điểm nhắc nhở
        
        Args:
            deadline: Thời hạn
            reminder_settings: Danh sách cài đặt nhắc nhở
            
        Returns:
            List các thời điểm nhắc nhở
        """
        reminder_times = []
        
        for setting in reminder_settings:
            # Parse setting thành timedelta
            delta = self._parse_reminder_setting(setting)
            if delta:
                reminder_time = deadline - delta
                
                # Chỉ thêm nếu chưa qua
                if reminder_time > datetime.now(self.default_timezone):
                    reminder_times.append(reminder_time)
        
        return sorted(reminder_times)
    
    def _parse_reminder_setting(self, setting: str) -> Optional[timedelta]:
        """
        Parse reminder setting thành timedelta
        
        Args:
            setting: String setting (vd: "1_day_before", "2_hours_before")
            
        Returns:
            timedelta object hoặc None
        """
        # Regex để parse setting
        pattern = r"(\d+)_(day|hour|minute)s?_before"
        match = re.match(pattern, setting)
        
        if not match:
            return None
        
        value = int(match.group(1))
        unit = match.group(2)
        
        if unit == "day":
            return timedelta(days=value)
        elif unit == "hour":
            return timedelta(hours=value)
        elif unit == "minute":
            return timedelta(minutes=value)
        
        return None
    
    def is_working_day(self, dt: datetime) -> bool:
        """
        Kiểm tra xem có phải ngày làm việc không
        
        Args:
            dt: datetime object
            
        Returns:
            True nếu là ngày làm việc
        """
        # Thứ 2-6 là ngày làm việc (0=Monday, 6=Sunday)
        return dt.weekday() < 5
    
    def get_next_working_day(self, dt: datetime) -> datetime:
        """
        Lấy ngày làm việc tiếp theo
        
        Args:
            dt: datetime object
            
        Returns:
            Ngày làm việc tiếp theo
        """
        next_day = dt + timedelta(days=1)
        while not self.is_working_day(next_day):
            next_day += timedelta(days=1)
        return next_day

# Test function
def test_date_utils():
    """Test function để kiểm tra DateUtils hoạt động đúng"""
    try:
        date_utils = DateUtils()
        
        # Test parse_date
        dt = date_utils.parse_date("2024-01-01 10:00:00")
        print("✅ parse_date() works")
        
        # Test format_date
        formatted = date_utils.format_date(dt, "%d/%m/%Y %H:%M")
        print(f"✅ format_date() works: {formatted}")
        
        # Test calculate_difference
        now = datetime.now(date_utils.default_timezone)
        diff = date_utils.calculate_difference(now, dt)
        print(f"✅ calculate_difference() works: {diff['human_readable']}")
        
        # Test get_reminder_times
        reminder_times = date_utils.get_reminder_times(dt, ["1_day_before", "1_hour_before"])
        print(f"✅ get_reminder_times() works: {len(reminder_times)} reminders")
        
        print("🎉 DateUtils test passed!")
        
    except Exception as e:
        print(f"❌ DateUtils test failed: {e}")

if __name__ == "__main__":
    test_date_utils()
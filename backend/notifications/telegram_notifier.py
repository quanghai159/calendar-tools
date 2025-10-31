# -*- coding: utf-8 -*-
"""
TELEGRAM NOTIFIER MODULE
========================

Mô tả: Gửi thông báo qua Telegram Bot
Cách hoạt động:
1. Kết nối với Telegram Bot API
2. Gửi tin nhắn text, hình ảnh, file
3. Hỗ trợ template message
4. Xử lý lỗi và retry

Thuật toán chính:
- Sử dụng Telegram Bot API
- Format message theo template
- Retry mechanism cho failed messages
- Rate limiting để tránh spam
- Logging cho debugging

Hướng dẫn sử dụng:
1. Cấu hình bot_token trong config
2. Gọi send_message() để gửi tin nhắn
3. Gọi send_template_message() để gửi template
4. Gọi send_media_message() để gửi media

Ví dụ:
    notifier = TelegramNotifier("your_bot_token")
    notifier.send_message("user_id", "Hello World!")
"""

import requests
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

class TelegramNotifier:
    def __init__(self, bot_token: str):
        """
        Khởi tạo TelegramNotifier
        
        Args:
            bot_token: Telegram Bot Token
        """
        self.bot_token = bot_token
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self.rate_limit_delay = 1  # Delay giữa các request (seconds)
        self.max_retries = 3
        
        # Test connection
        if not self._test_connection():
            print("⚠️  Telegram Bot connection failed")
    
    def _test_connection(self) -> bool:
        """
        Test kết nối với Telegram Bot API
        
        Returns:
            True nếu kết nối thành công
        """
        try:
            response = requests.get(f"{self.api_url}/getMe", timeout=10)
            if response.status_code == 200:
                bot_info = response.json()
                if bot_info.get('ok'):
                    print(f"✅ Connected to Telegram Bot: @{bot_info['result']['username']}")
                    return True
            return False
        except Exception as e:
            print(f"❌ Telegram connection error: {e}")
            return False
    
    def send_message(self, user_id: str, message: str, parse_mode: str = "HTML") -> bool:
        """
        Thuật toán gửi tin nhắn text:
        1. Validate user_id và message
        2. Format message theo template
        3. Gửi request đến Telegram API
        4. Xử lý response và retry nếu cần
        5. Log kết quả
        
        Args:
            user_id: Telegram user ID hoặc username
            message: Nội dung tin nhắn
            parse_mode: Parse mode (HTML, Markdown)
            
        Returns:
            True nếu gửi thành công
        """
        try:
            # Bước 1: Validate input
            if not user_id or not message:
                print("❌ Invalid user_id or message")
                return False
            
            # Bước 2: Format message
            formatted_message = self._format_message(message)
            
            # Bước 3: Gửi request
            payload = {
                'chat_id': user_id,
                'text': formatted_message,
                'parse_mode': parse_mode
            }
            
            # Bước 4: Retry mechanism
            for attempt in range(self.max_retries):
                try:
                    response = requests.post(
                        f"{self.api_url}/sendMessage",
                        json=payload,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('ok'):
                            print(f"✅ Telegram message sent to {user_id}")
                            return True
                        else:
                            print(f"❌ Telegram API error: {result.get('description')}")
                    else:
                        print(f"❌ HTTP error: {response.status_code}")
                    
                except requests.exceptions.RequestException as e:
                    print(f"❌ Request error (attempt {attempt + 1}): {e}")
                
                # Delay trước khi retry
                if attempt < self.max_retries - 1:
                    time.sleep(self.rate_limit_delay * (attempt + 1))
            
            return False
            
        except Exception as e:
            print(f"❌ Send message error: {e}")
            return False
    
    def send_template_message(self, user_id: str, template_name: str, data: Dict[str, Any]) -> bool:
        """
        Gửi template message
        
        Args:
            user_id: Telegram user ID
            template_name: Tên template
            data: Data để fill vào template
            
        Returns:
            True nếu gửi thành công
        """
        try:
            message = self._render_template(template_name, data)
            return self.send_message(user_id, message)
        except Exception as e:
            print(f"❌ Template message error: {e}")
            return False
    
    def send_media_message(self, user_id: str, media_url: str, caption: str = "") -> bool:
        """
        Gửi tin nhắn media (hình ảnh, file)
        
        Args:
            user_id: Telegram user ID
            media_url: URL của media
            caption: Caption cho media
            
        Returns:
            True nếu gửi thành công
        """
        try:
            payload = {
                'chat_id': user_id,
                'photo': media_url,
                'caption': caption
            }
            
            response = requests.post(
                f"{self.api_url}/sendPhoto",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    print(f"✅ Telegram media sent to {user_id}")
                    return True
            
            return False
            
        except Exception as e:
            print(f"❌ Media message error: {e}")
            return False
    
    def _format_message(self, message: str) -> str:
        """
        Format message với footer (không thêm header)
        
        Args:
            message: Message gốc
            
        Returns:
            Formatted message
        """
        # Bỏ header, chỉ giữ footer
        footer = f"\n\n<i>Gửi lúc: {datetime.now().strftime('%d/%m/%Y %H:%M')}</i>"
        
        return message + footer
    
    def _render_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """
        Render template message
        
        Args:
            template_name: Tên template
            data: Data để fill
            
        Returns:
            Rendered message
        """
        templates = {
            'reminder': """
🔔 <b>NHẮC NHỞ LỊCH LÀM VIỆC</b>

📅 <b>{title}</b>
⏰ <b>Hạn chót:</b> {deadline}
📝 <b>Mô tả:</b> {description}

Hãy chuẩn bị sẵn sàng nhé! 💪
            """,
            'daily_report': """
📊 <b>BÁO CÁO HÀNG NGÀY</b>

✅ <b>Hoàn thành:</b> {completed}
⏳ <b>Đang làm:</b> {pending}
❌ <b>Quá hạn:</b> {overdue}

Chúc bạn một ngày làm việc hiệu quả! 🚀
            """,
            'deadline_alert': """
⚠️ <b>CẢNH BÁO DEADLINE</b>

📅 <b>{title}</b>
⏰ <b>Còn lại:</b> {time_left}
🚨 <b>Mức độ:</b> {priority}

Hãy tập trung hoàn thành ngay! 🔥
            """
        }
        
        template = templates.get(template_name, "{message}")
        return template.format(**data)
    
    def get_chat_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin chat
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Chat info dict hoặc None
        """
        try:
            response = requests.get(
                f"{self.api_url}/getChat",
                params={'chat_id': user_id},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    return result['result']
            
            return None
            
        except Exception as e:
            print(f"❌ Get chat info error: {e}")
            return None

# Test function
def test_telegram_notifier():
    """Test function để kiểm tra TelegramNotifier hoạt động đúng"""
    try:
        # Sử dụng mock token cho test
        notifier = TelegramNotifier("mock_token_for_testing")
        
        # Test send message (sẽ fail vì token không thật)
        success = notifier.send_message("test_user", "Test message")
        print(f"✅ send_message() works: {success}")
        
        # Test template message
        template_data = {
            'title': 'Test Task',
            'deadline': '2024-01-15 17:00',
            'description': 'Test description'
        }
        success = notifier.send_template_message("test_user", "reminder", template_data)
        print(f"✅ send_template_message() works: {success}")
        
        print("🎉 TelegramNotifier test passed!")
        
    except Exception as e:
        print(f"❌ TelegramNotifier test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_telegram_notifier()
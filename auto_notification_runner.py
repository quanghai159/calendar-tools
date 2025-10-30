# -*- coding: utf-8 -*-
"""
AUTOMATIC NOTIFICATION RUNNER
============================

Mô tả: Chạy tự động xử lý notifications định kỳ
Cách hoạt động:
1. Chạy liên tục và kiểm tra notifications mỗi phút
2. Gửi thông báo khi tới thời gian
3. Log kết quả và lỗi
4. Chạy song song với web app

Thuật toán chính:
- Continuous monitoring
- Scheduled execution
- Error handling
- Logging

Hướng dẫn sử dụng:
1. Chạy: python3 auto_notification_runner.py
2. Để chạy song song với web app
3. Tự động gửi thông báo khi tới giờ

Ví dụ:
    python3 auto_notification_runner.py
    # Chạy song song với: python3 frontend/app.py
"""

import os
import sys
import time
from datetime import datetime, timedelta

# Add backend directory to path
sys.path.append('backend')

from core.database_manager import DatabaseManager
from notifications.telegram_notifier import TelegramNotifier
from notifications.notification_scheduler import NotificationScheduler

class AutoNotificationRunner:
    def __init__(self):
        """Khởi tạo Auto Notification Runner"""
        self.running = False
        self.check_interval = 60  # Kiểm tra mỗi 60 giây
        
        # Initialize database
        self.db = DatabaseManager("database/calendar_tools.db")
        
        # Initialize Telegram notifier
        bot_token = "8338680403:AAFZPZM2tllQgFNQcVdM2CzZlMRXYsCJxpw"
        self.telegram_notifier = TelegramNotifier(bot_token)
        
        # Initialize notification scheduler
        self.scheduler = NotificationScheduler(self.db, self.telegram_notifier)
        
        print("✅ Auto Notification Runner initialized")
        print(f"⏰ Check interval: {self.check_interval} seconds")
    
    def start(self):
        """Bắt đầu chạy tự động"""
        self.running = True
        print("🚀 Starting Auto Notification Runner...")
        print("📱 Press Ctrl+C to stop")
        
        try:
            while self.running:
                try:
                    # Kiểm tra và xử lý notifications
                    self._check_and_process_notifications()
                    
                    # Chờ interval
                    time.sleep(self.check_interval)
                    
                except KeyboardInterrupt:
                    print("\n⏹️  Stopping Auto Notification Runner...")
                    self.running = False
                    break
                except Exception as e:
                    print(f"❌ Error in main loop: {e}")
                    time.sleep(10)  # Chờ 10 giây trước khi thử lại
                    
        except Exception as e:
            print(f"❌ Fatal error: {e}")
        finally:
            print("✅ Auto Notification Runner stopped")
    
    def _check_and_process_notifications(self):
        """Kiểm tra và xử lý notifications"""
        try:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"🔍 Checking notifications at {current_time}")
            
            # Xử lý notifications
            result = self.scheduler.process_pending_notifications()
            
            if result['status'] == 'success':
                if result['processed'] > 0:
                    print(f"✅ Processed {result['processed']} notifications, {result['sent']} sent successfully")
                else:
                    print("ℹ️  No notifications to process")
            else:
                print(f"⚠️  Notification processing result: {result}")
                
        except Exception as e:
            print(f"❌ Error checking notifications: {e}")
    
    def stop(self):
        """Dừng runner"""
        self.running = False

def main():
    """Main function"""
    try:
        runner = AutoNotificationRunner()
        runner.start()
    except Exception as e:
        print(f"❌ Failed to start Auto Notification Runner: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
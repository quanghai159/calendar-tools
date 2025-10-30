# -*- coding: utf-8 -*-
"""
NOTIFICATION SCHEDULER MODULE
============================

Mô tả: Module lên lịch và gửi thông báo tự động
Cách hoạt động:
1. Kiểm tra notifications cần gửi
2. Gửi thông báo qua các kênh
3. Cập nhật trạng thái notification
4. Log kết quả

Thuật toán chính:
- Notification scheduling
- Multi-channel delivery
- Status tracking
- Error handling

Hướng dẫn sử dụng:
1. Khởi tạo NotificationScheduler
2. Gọi process_pending_notifications() để xử lý
3. Chạy định kỳ để gửi thông báo

Ví dụ:
    scheduler = NotificationScheduler(db, telegram_notifier)
    scheduler.process_pending_notifications()
"""

import os
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

class NotificationScheduler:
    def __init__(self, db, telegram_notifier=None, email_notifier=None, zalo_notifier=None):
        """
        Khởi tạo NotificationScheduler
        
        Args:
            db: DatabaseManager instance
            telegram_notifier: TelegramNotifier instance
            email_notifier: EmailNotifier instance
            zalo_notifier: ZaloNotifier instance
        """
        self.db = db
        self.telegram_notifier = telegram_notifier
        self.email_notifier = email_notifier
        self.zalo_notifier = zalo_notifier
        print("✅ NotificationScheduler initialized")
    
    def process_pending_notifications(self) -> Dict[str, Any]:
        """
        Xử lý các notifications đang chờ gửi
        
        Returns:
            Dict chứa kết quả xử lý
        """
        try:
            # Lấy notifications cần gửi
            pending_notifications = self._get_pending_notifications()
            
            if not pending_notifications:
                return {'status': 'no_pending', 'processed': 0}
            
            processed_count = 0
            success_count = 0
            
            for notification in pending_notifications:
                try:
                    # Gửi thông báo
                    sent = self._send_notification(notification)
                    
                    if sent:
                        success_count += 1
                        # Cập nhật trạng thái thành sent
                        self._update_notification_status(
                            notification['notification_id'], 
                            'sent'
                        )
                    else:
                        # Cập nhật trạng thái thành failed
                        self._update_notification_status(
                            notification['notification_id'], 
                            'failed'
                        )
                    
                    processed_count += 1
                    
                except Exception as e:
                    print(f"❌ Error processing notification {notification['notification_id']}: {e}")
                    self._update_notification_status(
                        notification['notification_id'], 
                        'failed'
                    )
                    processed_count += 1
            
            print(f"✅ Processed {processed_count} notifications, {success_count} sent successfully")
            
            return {
                'status': 'success',
                'processed': processed_count,
                'sent': success_count,
                'failed': processed_count - success_count
            }
            
        except Exception as e:
            print(f"❌ Error processing pending notifications: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _get_pending_notifications(self) -> List[Dict[str, Any]]:
        """Lấy danh sách notifications cần gửi"""
        try:
            now = datetime.now()
            current_time = now.strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"🔍 Looking for notifications scheduled before: {current_time}")
            
            with self.db.get_connection() as conn:
                query = """
                SELECT n.*, t.title, t.description, t.deadline, t.priority
                FROM notifications n
                JOIN tasks t ON n.task_id = t.task_id
                WHERE n.status = 'pending' 
                AND n.scheduled_time <= ?
                ORDER BY n.scheduled_time
                """
                
                results = self.db.execute_query(conn, query, (current_time,))
                print(f"Found {len(results)} pending notifications")
                
                # Debug: In ra tất cả notifications
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM notifications ORDER BY scheduled_time")
                all_notifications = cursor.fetchall()
                print(f"All notifications in database: {len(all_notifications)}")
                for notif in all_notifications:
                    print(f"  - {notif}")
                
                return results
                    
        except Exception as e:
            print(f"❌ Error getting pending notifications: {e}")
            return []

    def _get_user_telegram_id(self, user_id: str) -> Optional[int]:
        try:
            with self.db.get_connection() as conn:
                row = conn.execute(
                    """
                    SELECT setting_value 
                    FROM user_settings 
                    WHERE user_id = ? AND setting_key = 'telegram_user_id' 
                    AND tool_id IS NULL
                    ORDER BY updated_at DESC 
                    LIMIT 1
                    """,
                    (user_id,)
                ).fetchone()
                if row and row[0]:
                    try:
                        return int(str(row[0]).strip())
                    except:
                        return None
        except Exception as e:
            print(f"❌ Error reading user telegram id: {e}")
        return None        
    
    def _send_notification(self, notification: Dict[str, Any]) -> bool:
        """Gửi thông báo qua các kênh"""
        try:
            message = self._prepare_notification_message(notification)
            sent = False

            # Lấy user_id của task
            target_user_id = notification.get('user_id')
            if not target_user_id:
                # Tra DB theo task_id
                try:
                    with self.db.get_connection() as conn:
                        row = conn.execute(
                            "SELECT user_id FROM tasks WHERE task_id = ?",
                            (notification.get('task_id'),)
                        ).fetchone()
                        if row and row[0]:
                            target_user_id = row[0]
                except Exception as e:
                    print(f"❌ Error fetching task owner: {e}")

            # Gửi qua Telegram theo setting user
            if self.telegram_notifier and target_user_id:
                chat_id = self._get_user_telegram_id(target_user_id)
                if chat_id:
                    if self.telegram_notifier.send_message(chat_id, message):
                        sent = True
                        print(f"✅ Telegram notification sent to {chat_id} for task: {notification.get('title')}")
                else:
                    print(f"⚠️ No telegram_user_id setting for user {target_user_id}")

            # TODO: email / zalo
            return sent

        except Exception as e:
            print(f"❌ Error sending notification: {e}")
            return False
    
    def _prepare_notification_message(self, notification: Dict[str, Any]) -> str:
        """Chuẩn bị nội dung thông báo"""
        try:
            title = notification.get('title', 'Task')
            deadline = notification.get('deadline', 'N/A')
            priority = notification.get('priority', 'medium')
            
            # Tạo emoji theo priority
            priority_emoji = {
                'high': '🔴',
                'medium': '🟡', 
                'low': '🟢',
                'urgent': '🚨'
            }.get(priority, '🟡')
            
            message = f"""
{priority_emoji} **NHẮC NHỞ TÁC VỤ**

📋 **Tên tác vụ:** {title}
⏰ **Deadline:** {deadline}
🎯 **Mức độ ưu tiên:** {priority.upper()}

💡 Hãy hoàn thành tác vụ trước deadline!

---
📱 Calendar Tools Bot
            """
            
            return message.strip()
            
        except Exception as e:
            print(f"❌ Error preparing notification message: {e}")
            return "Nhắc nhở tác vụ từ Calendar Tools"
    
    def _update_notification_status(self, notification_id: str, status: str):
        """Cập nhật trạng thái notification"""
        try:
            with self.db.get_connection() as conn:
                query = "UPDATE notifications SET status = ?, sent_at = ? WHERE notification_id = ?"
                params = (status, datetime.now().isoformat(), notification_id)
                
                self.db.execute_update(conn, query, params)
                conn.commit()
                
        except Exception as e:
            print(f"⚠️  Error updating notification status: {e}")

# Test function
def test_notification_scheduler():
    """Test function để kiểm tra NotificationScheduler hoạt động đúng"""
    try:
        from core.database_manager import DatabaseManager
        from notifications.telegram_notifier import TelegramNotifier
        
        # Khởi tạo database
        db = DatabaseManager("test_notifications.db")
        
        # Khởi tạo Telegram notifier
        telegram_notifier = TelegramNotifier("8338680403:AAFZPZM2tllQgFNQcVdM2CzZlMRXYsCJxpw")
        
        # Khởi tạo scheduler
        scheduler = NotificationScheduler(db, telegram_notifier)
        
        # Test xử lý notifications
        result = scheduler.process_pending_notifications()
        print(f"✅ Process notifications result: {result}")
        
        # Cleanup
        import os
        if os.path.exists("test_notifications.db"):
            os.remove("test_notifications.db")
            print("✅ Test database cleaned up")
        
        print("🎉 NotificationScheduler test passed!")
        
    except Exception as e:
        print(f"❌ NotificationScheduler test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_notification_scheduler()
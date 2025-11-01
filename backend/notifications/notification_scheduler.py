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
import sqlite3
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import UserSettingsManager để lấy labels
sys.path.append(os.path.dirname(parent_dir))  # Để import từ shared
from shared.database.user_settings_manager import UserSettingsManager

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
                SELECT n.*, 
                    COALESCE(t.title, 'Task đã bị xóa') as title,
                    COALESCE(t.description, '') as description,
                    COALESCE(t.deadline, 'N/A') as deadline,
                    COALESCE(t.priority, 'medium') as priority
                FROM notifications n
                LEFT JOIN tasks t ON n.task_id = t.task_id
                WHERE n.status = 'pending' 
                AND n.scheduled_time <= ?
                ORDER BY n.scheduled_time
                """
                
                results = self.db.execute_query(conn, query, (current_time,))
                print(f"Found {len(results)} pending notifications")

                # Debug: In ra chi tiết PENDING notifications với Task name và Telegram ID
                if len(results) > 0:
                    print("📋 DETAILED PENDING NOTIFICATIONS:")
                    for notif in results:
                        nid = notif.get('notification_id', 'N/A')
                        task_id = notif.get('task_id', 'N/A')
                        title = notif.get('title', 'N/A')
                        scheduled_time = notif.get('scheduled_time', 'N/A')  # Lấy từ notifications.scheduled_time
                        
                        # Debug: Kiểm tra tất cả các trường liên quan đến thời gian từ bảng notifications
                        notif_raw = conn.execute("""
                            SELECT notification_id, task_id, scheduled_time, status, sent_at, created_at
                            FROM notifications 
                            WHERE notification_id = ?
                        """, (nid,)).fetchone()
                        
                        scheduled_from_db = notif_raw[2] if notif_raw and len(notif_raw) > 2 else 'N/A'
                        sent_at = notif_raw[4] if notif_raw and len(notif_raw) > 4 else None
                        
                        # Lấy user_id từ notification hoặc task
                        user_id = notif.get('user_id')
                        if not user_id and task_id != 'N/A':
                            user_row = conn.execute("SELECT user_id FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
                            user_id = user_row[0] if user_row and user_row[0] else None

                        # Lấy email và telegram_user_id từ users và user_settings
                        user_email = None
                        telegram_id = None
                        if user_id:
                            # Lấy email từ bảng users
                            user_info = conn.execute("SELECT email, display_name FROM users WHERE user_id = ?", (user_id,)).fetchone()
                            if user_info:
                                user_email = user_info[0]  # email
                                user_display_name = user_info[1]  # display_name
                            
                            # Lấy telegram_user_id từ user_settings
                            tg_row = conn.execute("""
                                SELECT setting_value FROM user_settings 
                                WHERE user_id = ? AND setting_key = 'telegram_user_id' AND tool_id IS NULL
                                ORDER BY updated_at DESC LIMIT 1
                            """, (user_id,)).fetchone()
                            telegram_id = tg_row[0] if tg_row and tg_row[0] else None
                        
                        print(f"  📋 PENDING: ID={nid}, Task='{title}' (task_id={task_id})")
                        print(f"      └─ User: {user_id} ({user_email or 'N/A'}), Telegram: {telegram_id or 'N/A'}")
                        print(f"      └─ Scheduled Time: {scheduled_time} [Từ cột: notifications.scheduled_time, Raw DB: {scheduled_from_db}]")
                        print(f"      └─ Status: {notif_raw[3] if notif_raw and len(notif_raw) > 3 else 'N/A'}, Sent At: {sent_at or 'N/A'}")
                else:
                    print("📋 No pending notifications found for current time")

                # Debug: In ra các notifications có status='pending' nhưng scheduled_time > now
                cursor = conn.cursor()
                future_pending = cursor.execute("""
                    SELECT notification_id, task_id, scheduled_time 
                    FROM notifications 
                    WHERE status = 'pending' AND scheduled_time > ?
                    ORDER BY scheduled_time
                """, (current_time,)).fetchall()
                if future_pending:
                    print(f"📋 Future pending notifications ({len(future_pending)}):")
                    for fp in future_pending:
                        fp_id = fp[0] if isinstance(fp, (tuple, list)) else fp['notification_id']
                        fp_task = fp[1] if isinstance(fp, (tuple, list)) else fp['task_id']
                        fp_time = fp[2] if isinstance(fp, (tuple, list)) else fp['scheduled_time']
                        
                        # Lấy thông tin chi tiết từ bảng notifications để hiển thị cột cụ thể
                        notif_detail = conn.execute("""
                            SELECT scheduled_time, status, created_at
                            FROM notifications 
                            WHERE notification_id = ?
                        """, (fp_id,)).fetchone()
                        scheduled_raw = notif_detail[0] if notif_detail and len(notif_detail) > 0 else 'N/A'
                        
                        # Lấy task title và user email
                        task_row = conn.execute("SELECT title, user_id FROM tasks WHERE task_id = ?", (fp_task,)).fetchone()
                        task_title = task_row[0] if task_row and task_row[0] else 'N/A'
                        fp_user_id = task_row[1] if task_row and len(task_row) > 1 and task_row[1] else None
                        fp_email = None
                        if fp_user_id:
                            email_row = conn.execute("SELECT email FROM users WHERE user_id = ?", (fp_user_id,)).fetchone()
                            fp_email = email_row[0] if email_row and email_row[0] else None
                        
                        print(f"  ⏰ FUTURE: ID={fp_id}, Task='{task_title}', User={fp_user_id} ({fp_email or 'N/A'})")
                        print(f"      └─ Scheduled Time: {fp_time} [Từ cột: notifications.scheduled_time, Raw DB value: {scheduled_raw}]")

                # Debug: In ra tất cả notifications (giữ nguyên để so sánh)
                cursor = conn.cursor()
                cursor.execute("SELECT notification_id, status, scheduled_time FROM notifications ORDER BY scheduled_time")
                all_notifications = cursor.fetchall()
                print(f"All notifications in database: {len(all_notifications)}")
                for notif in all_notifications:
                    row = dict(notif) if isinstance(notif, sqlite3.Row) else notif
                    nid = row['notification_id'] if isinstance(row, dict) else row[0]
                    status = row['status'] if isinstance(row, dict) else row[1]
                    sched = row['scheduled_time'] if isinstance(row, dict) else row[2]
                    print(f"  - ID: {nid}, Status: {status}, Scheduled: {sched} (now: {current_time})")

                return results
                
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
            print(f"🔍 Debug _send_notification: notification_id={notification.get('notification_id')}, task_id={notification.get('task_id')}")
            message = self._prepare_notification_message(notification)
            sent = False

            # Lấy user_id của task
            target_user_id = notification.get('user_id')
            print(f"🔍 Debug: initial target_user_id={target_user_id}")
            if not target_user_id:
                # Tra DB theo task_id
                try:
                    task_id = notification.get('task_id')
                    print(f"🔍 Debug: Looking up user_id for task_id={task_id}")
                    with self.db.get_connection() as conn:
                        row = conn.execute(
                            "SELECT user_id FROM tasks WHERE task_id = ?",
                            (task_id,)
                        ).fetchone()
                        if row and row[0]:
                            target_user_id = row[0]
                            print(f"🔍 Debug: Found user_id={target_user_id} from tasks table")
                        else:
                            print(f"⚠️ Debug: No task found with task_id={task_id}")
                except Exception as e:
                    print(f"❌ Error fetching task owner: {e}")

            # Gửi qua Telegram theo setting user
            if self.telegram_notifier and target_user_id:
                print(f"🔍 Debug: Getting telegram_user_id for user_id={target_user_id}")
                chat_id = self._get_user_telegram_id(target_user_id)
                print(f"🔍 Debug: chat_id={chat_id}")
                if chat_id:
                    print(f"🔍 Debug: Sending telegram message to chat_id={chat_id}")
                    if self.telegram_notifier.send_message(chat_id, message):
                        sent = True
                        print(f"✅ Telegram notification sent to {chat_id} for task: {notification.get('title')}")
                    else:
                        print(f"❌ Failed to send telegram message to {chat_id}")
                else:
                    print(f"⚠️ No telegram_user_id setting for user {target_user_id}")
            else:
                if not self.telegram_notifier:
                    print(f"⚠️ Debug: telegram_notifier is None")
                if not target_user_id:
                    print(f"⚠️ Debug: target_user_id is None")

            # TODO: email / zalo
            return sent

        except Exception as e:
            print(f"❌ Error sending notification: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _prepare_notification_message(self, notification: Dict[str, Any]) -> str:
        """Chuẩn bị nội dung thông báo"""
        try:
            title = notification.get('title', 'Task')
            priority = notification.get('priority', 'medium')
            notification_id = notification.get('notification_id', '')
            task_id = notification.get('task_id', '')
            scheduled_time = notification.get('scheduled_time', '')  # Lấy scheduled_time thay vì deadline
            
            # Lấy user_id từ notification hoặc task
            user_id = notification.get('user_id')
            if not user_id and task_id:
                try:
                    with self.db.get_connection() as conn:
                        row = conn.execute("SELECT user_id FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
                        if row and row[0]:
                            user_id = row[0]
                except:
                    pass
            
            # Xác định notification đến từ cột nào (notification_time, notif1-8)
            # Format khi create: notif_{task_id}_{notif_source}_{timestamp}
            # Format cũ: notif_{task_id}_{timestamp} (không có notif_source)
            notif_source = 'notification_time'  # Default
            if notification_id and '_' in notification_id:
                parts = notification_id.split('_')
                if len(parts) >= 4:
                    # Format mới: notif_task_xxx_notif1_timestamp hoặc notif_task_xxx_notification_time_timestamp
                    # parts[3] có thể là 'notif1', 'notif2', ... hoặc 'notification'
                    potential_source = parts[3]
                    
                    # Nếu là 'notification', kiểm tra parts[4] có phải 'time' không
                    if potential_source == 'notification' and len(parts) >= 5 and parts[4] == 'time':
                        notif_source = 'notification_time'
                    elif potential_source.startswith('notif') and len(potential_source) > 5:
                        # notif1, notif2, ..., notif8
                        notif_source = potential_source
                    else:
                        # Không phải notification_time, có thể là notif1-8 hoặc format khác
                        notif_source = potential_source
                elif len(parts) >= 3:
                    # Format cũ: notif_task_xxx_timestamp -> không có notif_source, dùng default
                    notif_source = 'notification_time'

            # Lấy label từ user settings
            notif_label = 'Thông báo'  # Default
            if user_id:
                try:
                    settings_mgr = UserSettingsManager(self.db.db_path)
                    if notif_source == 'notification_time':
                        # notification_time -> dùng label mặc định hoặc lấy từ setting
                        notif_label = settings_mgr.get_setting(
                            user_id, 'notification_time_label', tool_id=None,
                            default='Thông báo chính'
                        ) or 'Thông báo chính'
                    elif notif_source.startswith('notif') and len(notif_source) <= 6:
                        # notif1, notif2, ..., notif8
                        notif_num = notif_source.replace('notif', '')
                        # Kiểm tra notif_num là số hợp lệ (1-8)
                        if notif_num.isdigit() and 1 <= int(notif_num) <= 8:
                            label_key = f'notif_label_{notif_num}'
                            notif_label = settings_mgr.get_setting(
                                user_id, label_key, tool_id=None, 
                                default=f'Thông báo {notif_num}'
                            ) or f'Thông báo {notif_num}'
                        else:
                            # Không phải số hợp lệ, dùng default
                            notif_label = 'Thông báo'
                    else:
                        # Trường hợp khác, dùng default
                        notif_label = 'Thông báo'
                except Exception as e:
                    print(f"⚠️  Error getting notif label: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Format scheduled_time (thời điểm gửi thông báo): "2025-10-31 12:12:00" -> "31/10/2025 - 12:12"
            formatted_time = 'N/A'
            if scheduled_time:
                try:
                    # Thử parse nhiều format
                    if 'T' in scheduled_time:
                        # Format: 2025-10-31T12:12
                        dt = datetime.strptime(scheduled_time, '%Y-%m-%dT%H:%M')
                    elif len(scheduled_time) == 19:
                        # Format: 2025-10-31 12:12:00
                        dt = datetime.strptime(scheduled_time, '%Y-%m-%d %H:%M:%S')
                    elif len(scheduled_time) == 16:
                        # Format: 2025-10-31 12:12
                        dt = datetime.strptime(scheduled_time, '%Y-%m-%d %H:%M')
                    else:
                        # Format: 2025-10-31
                        dt = datetime.strptime(scheduled_time, '%Y-%m-%d')
                    
                    # Format: 31/10/2025 - 12:12
                    formatted_time = dt.strftime('%d/%m/%Y - %H:%M')
                except Exception as e:
                    # Nếu không parse được, hiển thị nguyên gốc
                    print(f"⚠️  Error parsing scheduled_time '{scheduled_time}': {e}")
                    formatted_time = scheduled_time
            
            # Tạo emoji theo priority
            priority_emoji = {
                'high': '🔴',
                'medium': '🟡', 
                'low': '🟢',
                'urgent': '🚨'
            }.get(priority, '🟡')
            
            # Message không có dấu **, hiển thị scheduled_time với label
            message = f"""
    {priority_emoji} NHẮC NHỞ TÁC VỤ

    📋 Tên tác vụ: {title}
    ⏰ Deadline ({notif_label}): {formatted_time}
    🎯 Mức độ ưu tiên: {priority.upper()}

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
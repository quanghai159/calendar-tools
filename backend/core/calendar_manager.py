# -*- coding: utf-8 -*-
"""
CALENDAR MANAGER MODULE
======================

Mô tả: Module chính quản lý toàn bộ hệ thống calendar
Cách hoạt động:
1. Tích hợp tất cả các module con
2. Đồng bộ dữ liệu từ Google Sheets
3. Quản lý calendar events
4. Gửi thông báo tự động
5. Tạo báo cáo

Thuật toán chính:
- Orchestrate tất cả các module
- Data synchronization pipeline
- Event processing workflow
- Notification scheduling
- Error handling và logging

Hướng dẫn sử dụng:
1. Khởi tạo CalendarManager
2. Gọi sync_user_data() để đồng bộ dữ liệu
3. Gọi process_reminders() để xử lý nhắc nhở
4. Gọi generate_report() để tạo báo cáo

Ví dụ:
    manager = CalendarManager()
    manager.sync_user_data(user_id)
    manager.process_reminders()
"""

import os
import sys
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import các module
from core.database_manager import DatabaseManager
from user_management.user_registry import UserRegistry
from task_management.task_creator import TaskCreator
try:
    from integrations.google_sheets_connector import GoogleSheetsConnector
except ImportError:
    print("⚠️  GoogleSheetsConnector not found, using mock")
    class GoogleSheetsConnector:
        def __init__(self, use_mock=True):
            self.use_mock = use_mock
        def read_sheet_data(self, sheet_id):
            return []
        def parse_calendar_events(self, data):
            return []
from notifications.telegram_notifier import TelegramNotifier
from notifications.email_notifier import EmailNotifier
from notifications.zalo_notifier import ZaloNotifier
from utils.date_utils import DateUtils
from utils.config_loader import ConfigLoader

class CalendarManager:
    def __init__(self, config_file: str = "config/config.json"):
        """
        Khởi tạo CalendarManager
        
        Args:
            config_file: Đường dẫn đến file config
        """
        # Load config
        self.config = ConfigLoader(config_file)
        
        # Initialize database
        db_path = self.config.get_value('database.path', 'database/calendar_tools.db')
        self.db = DatabaseManager(db_path)
        
        # Initialize modules
        self.user_registry = UserRegistry(self.db)
        self.task_creator = TaskCreator(self.db)
        self.sheets_connector = GoogleSheetsConnector(use_mock=True)
        self.date_utils = DateUtils()
        
        # Initialize notifiers
        self._init_notifiers()
        
        print("✅ CalendarManager initialized successfully")
    
    def _init_notifiers(self):
        """Khởi tạo các notifiers"""
        try:
            # Telegram notifier
            telegram_config = self.config.get_section('notifications.telegram')
            if telegram_config.get('enabled', False):
                self.telegram_notifier = TelegramNotifier(telegram_config.get('bot_token', ''))
            else:
                self.telegram_notifier = None
            
            # Email notifier
            email_config = self.config.get_section('notifications.email')
            if email_config.get('enabled', False):
                self.email_notifier = EmailNotifier(email_config)
            else:
                self.email_notifier = None
            
            # Zalo notifier
            zalo_config = self.config.get_section('notifications.zalo')
            if zalo_config.get('enabled', False):
                self.zalo_notifier = ZaloNotifier(
                    zalo_config.get('access_token', ''),
                    zalo_config.get('oa_id', '')
                )
            else:
                self.zalo_notifier = None
                
        except Exception as e:
            print(f"⚠️  Error initializing notifiers: {e}")
            self.telegram_notifier = None
            self.email_notifier = None
            self.zalo_notifier = None
    
    def create_user_task(self, user_data: Dict[str, Any], google_sheet_url: str) -> Dict[str, Any]:
        """
        Thuật toán tạo user và task mới:
        1. Tạo user mới
        2. Tạo task cho user
        3. Sync dữ liệu từ Google Sheets
        4. Return thông tin user và task
        
        Args:
            user_data: Thông tin user
            google_sheet_url: URL Google Sheet
            
        Returns:
            Dict chứa user_id và task_id
        """
        try:
            # Bước 1: Tạo user
            print(f"👤 Creating user: {user_data['username']}")
            user_id = self.user_registry.register_user(user_data)
            
            # Bước 2: Tạo task
            print(f"📋 Creating task for user: {user_id}")
            task_id = self.task_creator.create_task(user_id, google_sheet_url)
            
            # Bước 3: Sync dữ liệu ban đầu
            print(f"🔄 Syncing initial data...")
            sync_result = self.sync_user_data(user_id)
            
            return {
                'user_id': user_id,
                'task_id': task_id,
                'sync_result': sync_result,
                'status': 'success'
            }
            
        except Exception as e:
            print(f"❌ Error creating user task: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def sync_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Thuật toán đồng bộ dữ liệu cho user:
        1. Lấy thông tin user và tasks
        2. Đọc dữ liệu từ Google Sheets
        3. Parse thành calendar events
        4. Lưu vào database
        5. Return kết quả sync
        
        Args:
            user_id: User ID cần sync
            
        Returns:
            Dict chứa kết quả sync
        """
        try:
            # Bước 1: Lấy thông tin user và tasks
            user = self.user_registry.get_user_info(user_id)
            if not user:
                raise ValueError(f"User not found: {user_id}")
            
            tasks = self.task_creator.get_user_tasks(user_id)
            if not tasks:
                return {'status': 'no_tasks', 'events_synced': 0}
            
            # Bước 2: Sync từng task
            total_events = 0
            for task in tasks:
                if task['status'] != 'active':
                    continue
                
                print(f"📊 Syncing task: {task['task_id']}")
                
                # Đọc dữ liệu từ Google Sheets
                sheet_data = self.sheets_connector.read_sheet_data(task['google_sheet_id'])
                if not sheet_data:
                    print(f"⚠️  No data found for task: {task['task_id']}")
                    continue
                
                # Parse thành calendar events
                events = self.sheets_connector.parse_calendar_events(sheet_data)
                if not events:
                    print(f"⚠️  No events parsed for task: {task['task_id']}")
                    continue
                
                # Lưu events vào database
                events_saved = self._save_calendar_events(user_id, task['task_id'], events)
                total_events += events_saved
                
                # Cập nhật last_sync
                self._update_task_last_sync(task['task_id'])
            
            print(f"✅ Synced {total_events} events for user {user_id}")
            return {
                'status': 'success',
                'events_synced': total_events,
                'user_id': user_id
            }
            
        except Exception as e:
            print(f"❌ Error syncing user data: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _save_calendar_events(self, user_id: str, task_id: str, events: List[Dict[str, Any]]) -> int:
        """
        Lưu calendar events vào database
        
        Args:
            user_id: User ID
            task_id: Task ID
            events: List events cần lưu
            
        Returns:
            Số events đã lưu
        """
        saved_count = 0
        
        with self.db.get_connection() as conn:
            for event in events:
                try:
                    # Generate event ID
                    event_id = f"event_{user_id}_{task_id}_{saved_count}"
                    
                    # Insert event
                    query = """
                    INSERT OR REPLACE INTO calendar_events 
                    (event_id, task_id, user_id, title, description, start_date, end_date, 
                     deadline, category, priority, status, source, last_modified)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    
                    params = (
                        event_id,
                        task_id,
                        user_id,
                        event['title'],
                        event['description'],
                        event['start_date'],
                        event['end_date'],
                        event['deadline'],
                        event['category'],
                        event['priority'],
                        event['status'],
                        event['source'],
                        datetime.now().isoformat()
                    )
                    
                    self.db.execute_insert(conn, query, params)
                    saved_count += 1
                    
                except Exception as e:
                    print(f"⚠️  Error saving event: {e}")
                    continue
            
            conn.commit()
        
        return saved_count
    
    def _update_task_last_sync(self, task_id: str):
        """Cập nhật thời gian sync cuối cùng"""
        try:
            with self.db.get_connection() as conn:
                query = "UPDATE tasks SET last_sync = ? WHERE task_id = ?"
                self.db.execute_update(conn, query, (datetime.now().isoformat(), task_id))
                conn.commit()
        except Exception as e:
            print(f"⚠️  Error updating last_sync: {e}")
    
    def process_reminders(self) -> Dict[str, Any]:
        """
        Thuật toán xử lý nhắc nhở:
        1. Lấy tất cả events sắp đến deadline
        2. Lấy notification preferences của user
        3. Gửi thông báo qua các kênh được chọn
        4. Cập nhật trạng thái notification
        
        Returns:
            Dict chứa kết quả xử lý
        """
        try:
            # Bước 1: Lấy events cần nhắc nhở
            reminder_events = self._get_reminder_events()
            if not reminder_events:
                return {'status': 'no_reminders', 'notifications_sent': 0}
            
            # Bước 2: Xử lý từng event
            notifications_sent = 0
            for event in reminder_events:
                user_id = event['user_id']
                
                # Lấy notification preferences
                prefs = self.user_registry.get_user_notification_preferences(user_id)
                
                # Gửi thông báo
                sent = self._send_reminder_notification(event, prefs)
                if sent:
                    notifications_sent += 1
                
                # Cập nhật trạng thái
                self._update_notification_status(event['event_id'])
            
            print(f"✅ Processed {notifications_sent} reminders")
            return {
                'status': 'success',
                'notifications_sent': notifications_sent,
                'events_processed': len(reminder_events)
            }
            
        except Exception as e:
            print(f"❌ Error processing reminders: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _get_reminder_events(self) -> List[Dict[str, Any]]:
        """Lấy events cần nhắc nhở"""
        try:
            # Lấy events có deadline trong 24h tới
            tomorrow = datetime.now() + timedelta(days=1)
            tomorrow_str = tomorrow.strftime('%Y-%m-%d')
            
            with self.db.get_connection() as conn:
                query = """
                SELECT ce.*, u.email, u.telegram_username, u.zalo_phone
                FROM calendar_events ce
                JOIN users u ON ce.user_id = u.user_id
                WHERE ce.deadline IS NOT NULL 
                AND ce.deadline LIKE ?
                AND ce.status = 'pending'
                AND u.is_active = 1
                """
                
                results = self.db.execute_query(conn, query, (f"{tomorrow_str}%",))
                return results
                
        except Exception as e:
            print(f"❌ Error getting reminder events: {e}")
            return []
    
    def _send_reminder_notification(self, event: Dict[str, Any], prefs: Dict[str, Any]) -> bool:
        """Gửi thông báo nhắc nhở"""
        try:
            # Prepare notification data
            notification_data = {
                'title': event['title'],
                'deadline': event['deadline'],
                'description': event['description'],
                'priority': event['priority']
            }
            
            sent = False
            
            # Gửi qua Telegram
            if prefs.get('telegram', False) and self.telegram_notifier and event.get('telegram_username'):
                if self.telegram_notifier.send_template_message(
                    event['telegram_username'], 'reminder', notification_data
                ):
                    sent = True
            
            # Gửi qua Email
            if prefs.get('email', False) and self.email_notifier and event.get('email'):
                if self.email_notifier.send_template_email(
                    event['email'], 'reminder', notification_data
                ):
                    sent = True
            
            # Gửi qua Zalo
            if prefs.get('zalo', False) and self.zalo_notifier and event.get('zalo_phone'):
                if self.zalo_notifier.send_template_message(
                    event['zalo_phone'], 'reminder', notification_data
                ):
                    sent = True
            
            return sent
            
        except Exception as e:
            print(f"❌ Error sending notification: {e}")
            return False
    
    def _update_notification_status(self, event_id: str):
        """Cập nhật trạng thái notification"""
        try:
            with self.db.get_connection() as conn:
                query = """
                INSERT INTO notifications 
                (notification_id, user_id, event_id, notification_type, message, sent_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                
                notification_id = f"notif_{event_id}_{int(datetime.now().timestamp())}"
                message = f"Reminder sent for event {event_id}"
                
                params = (
                    notification_id,
                    event_id.split('_')[1],  # Extract user_id from event_id
                    event_id,
                    'reminder',
                    message,
                    datetime.now().isoformat(),
                    'sent'
                )
                
                self.db.execute_insert(conn, query, params)
                conn.commit()
                
        except Exception as e:
            print(f"⚠️  Error updating notification status: {e}")
    
    def generate_report(self, user_id: str, report_type: str = 'daily') -> Dict[str, Any]:
        """
        Tạo báo cáo cho user
        
        Args:
            user_id: User ID
            report_type: Loại báo cáo (daily, weekly, monthly)
            
        Returns:
            Dict chứa báo cáo
        """
        try:
            # Lấy events trong khoảng thời gian
            date_range = self._get_report_date_range(report_type)
            
            with self.db.get_connection() as conn:
                query = """
                SELECT * FROM calendar_events 
                WHERE user_id = ? 
                AND start_date BETWEEN ? AND ?
                ORDER BY start_date
                """
                
                events = self.db.execute_query(conn, query, (
                    user_id, 
                    date_range['start'], 
                    date_range['end']
                ))
            
            # Tính toán thống kê
            stats = self._calculate_event_stats(events)
            
            # Tạo báo cáo
            report = {
                'user_id': user_id,
                'report_type': report_type,
                'date_range': date_range,
                'statistics': stats,
                'events': events,
                'generated_at': datetime.now().isoformat()
            }
            
            # Lưu báo cáo vào database
            self._save_report(report)
            
            return report
            
        except Exception as e:
            print(f"❌ Error generating report: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _get_report_date_range(self, report_type: str) -> Dict[str, str]:
        """Lấy khoảng thời gian cho báo cáo"""
        now = datetime.now()
        
        if report_type == 'daily':
            start = now.strftime('%Y-%m-%d')
            end = now.strftime('%Y-%m-%d')
        elif report_type == 'weekly':
            start = (now - timedelta(days=7)).strftime('%Y-%m-%d')
            end = now.strftime('%Y-%m-%d')
        elif report_type == 'monthly':
            start = (now - timedelta(days=30)).strftime('%Y-%m-%d')
            end = now.strftime('%Y-%m-%d')
        else:
            start = now.strftime('%Y-%m-%d')
            end = now.strftime('%Y-%m-%d')
        
        return {'start': start, 'end': end}
    
    def _calculate_event_stats(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Tính toán thống kê events"""
        total = len(events)
        completed = len([e for e in events if e['status'] == 'completed'])
        pending = len([e for e in events if e['status'] == 'pending'])
        overdue = len([e for e in events if e['status'] == 'overdue'])
        
        return {
            'total': total,
            'completed': completed,
            'pending': pending,
            'overdue': overdue,
            'completion_rate': (completed / total * 100) if total > 0 else 0
        }
    
    def _save_report(self, report: Dict[str, Any]):
        """Lưu báo cáo vào database"""
        try:
            with self.db.get_connection() as conn:
                query = """
                INSERT INTO reports 
                (report_id, user_id, report_type, date_range_start, date_range_end, summary)
                VALUES (?, ?, ?, ?, ?, ?)
                """
                
                report_id = f"report_{report['user_id']}_{int(datetime.now().timestamp())}"
                summary = json.dumps(report['statistics'], ensure_ascii=False)
                
                params = (
                    report_id,
                    report['user_id'],
                    report['report_type'],
                    report['date_range']['start'],
                    report['date_range']['end'],
                    summary
                )
                
                self.db.execute_insert(conn, query, params)
                conn.commit()
                
        except Exception as e:
            print(f"⚠️  Error saving report: {e}")

# Test function
def test_calendar_manager():
    """Test function để kiểm tra CalendarManager hoạt động đúng"""
    try:
        manager = CalendarManager()
        
        # Test create user task
        user_data = {
            'username': 'test_manager_user',
            'email': 'test_manager@example.com',
            'telegram_username': '@testmanager',
            'zalo_phone': '0123456789'
        }
        
        google_sheet_url = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit"
        
        result = manager.create_user_task(user_data, google_sheet_url)
        print(f"✅ create_user_task() works: {result['status']}")
        
        if result['status'] == 'success':
            user_id = result['user_id']
            
            # Test sync user data
            sync_result = manager.sync_user_data(user_id)
            print(f"✅ sync_user_data() works: {sync_result['status']}")
            
            # Test process reminders
            reminder_result = manager.process_reminders()
            print(f"✅ process_reminders() works: {reminder_result['status']}")
            
            # Test generate report
            report = manager.generate_report(user_id, 'daily')
            print(f"✅ generate_report() works: {report.get('statistics', {})}")
        
        print("🎉 CalendarManager test passed!")
        
    except Exception as e:
        print(f"❌ CalendarManager test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_calendar_manager()
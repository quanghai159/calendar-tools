# -*- coding: utf-8 -*-
"""
SIMPLE TASK MANAGER MODULE
=========================

Mô tả: Quản lý tasks đơn giản không cần user
Cách hoạt động:
1. Tạo task mới với thông tin chi tiết
2. Quản lý thời gian thông báo
3. Cập nhật trạng thái task
4. Lấy danh sách tasks

Thuật toán chính:
- Task creation workflow
- Notification scheduling
- Status management
- Data validation

Hướng dẫn sử dụng:
1. Khởi tạo SimpleTaskManager
2. Gọi create_task() để tạo task mới
3. Gọi get_tasks() để lấy danh sách
4. Gọi update_task_status() để cập nhật

Ví dụ:
    manager = SimpleTaskManager(db)
    task_id = manager.create_task(task_data)
    tasks = manager.get_tasks()
"""

import os
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

class SimpleTaskManager:
    def __init__(self, db):
        """
        Khởi tạo SimpleTaskManager
        
        Args:
            db: DatabaseManager instance
        """
        self.db = db
        print("✅ SimpleTaskManager initialized")
    
    def create_task(self, task_data: Dict[str, Any]) -> str:
        """
        Thuật toán tạo task mới:
        1. Validate dữ liệu đầu vào
        2. Generate task_id unique
        3. Lưu vào database
        4. Tạo calendar event tương ứng
        5. Schedule notification nếu có
        
        Args:
            task_data: Thông tin task
                    - title: Tên task
                    - description: Mô tả
                    - start_date: Ngày bắt đầu
                    - end_date: Ngày kết thúc
                    - deadline: Deadline
                    - notification_time: Thời gian thông báo
                    - category: Loại task
                    - priority: Mức độ ưu tiên
            
            Returns:
                task_id: ID của task vừa tạo
        """
        try:
            # Bước 1: Validate dữ liệu
            required_fields = ['title', 'start_date', 'end_date', 'deadline']
            for field in required_fields:
                if not task_data.get(field):
                    raise ValueError(f"Missing required field: {field}")
            
            # Bước 2: Generate task_id
            task_id = f"task_{uuid.uuid4().hex[:12]}"
            
            # Bước 3: Prepare data
            now = datetime.now().isoformat()
            
            task_record = {
                'task_id': task_id,
                'user_id': task_data.get('user_id'),
                'title': task_data['title'],
                'description': task_data.get('description', ''),
                'start_date': task_data['start_date'],
                'end_date': task_data['end_date'],
                'deadline': task_data['deadline'],
                'notif1': task_data.get('notif1',''),
                'notif2': task_data.get('notif2',''),
                'notif3': task_data.get('notif3',''),
                'notif4': task_data.get('notif4',''),
                'notif5': task_data.get('notif5',''),
                'notif6': task_data.get('notif6',''),
                'notif7': task_data.get('notif7',''),
                'notif8': task_data.get('notif8',''),
                'notification_time': task_data.get('notification_time', ''),
                'category': task_data.get('category', 'general'),
                'priority': task_data.get('priority', 'medium'),
                'status': 'pending',
                'created_at': now,
                'last_modified': now
            }
            
            # Bước 4: Lưu vào database
            with self.db.get_connection() as conn:
                query = """
                INSERT INTO tasks 
                (task_id, user_id, title, description, start_date, end_date, deadline,
                notification_time, category, priority, status, created_at, last_modified,
                notif1, notif2, notif3, notif4, notif5, notif6, notif7, notif8)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                params = (
                    task_record['task_id'],
                    task_record['user_id'],
                    task_record['title'],
                    task_record['description'],
                    task_record['start_date'],
                    task_record['end_date'],
                    task_record['deadline'],
                    task_record['notification_time'],
                    task_record['category'],
                    task_record['priority'],
                    task_record['status'],
                    task_record['created_at'],
                    task_record['last_modified'],
                    task_record['notif1'], task_record['notif2'], task_record['notif3'], task_record['notif4'],
                    task_record['notif5'], task_record['notif6'], task_record['notif7'], task_record['notif8']
                )
                
                self.db.execute_insert(conn, query, params)
                
                # Bước 5: Tạo calendar event
                event_id = f"event_{task_id}"
                event_query = """
                INSERT INTO calendar_events 
                (event_id, task_id, user_id, title, description, start_date, end_date, 
                deadline, notification_time, category, priority, status, 
                source, created_at, last_modified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                event_params = (
                    event_id,
                    task_id,
                    task_record['user_id'],
                    task_record['title'],
                    task_record['description'],
                    task_record['start_date'],
                    task_record['end_date'],
                    task_record['deadline'],
                    task_record['notification_time'],
                    task_record['category'],
                    task_record['priority'],
                    task_record['status'],
                    'manual',
                    now,
                    now
                )
                
                self.db.execute_insert(conn, event_query, event_params)
                
                conn.commit()
            
            # Bước 6: Schedule notifications nếu có (sau khi commit)
            # Tạo notification từ notification_time
            if task_data.get('notification_time'):
                self._schedule_notification_after_commit(task_id, event_id, task_data['notification_time'], 'notification_time')

            # Tạo notifications từ notif1-8
            for i in range(1, 9):
                notif_key = f'notif{i}'
                if task_data.get(notif_key):
                    self._schedule_notification_after_commit(task_id, event_id, task_data[notif_key], notif_key)
            
            print(f"✅ Task created successfully: {task_id}")
            return task_id
            
        except Exception as e:
            print(f"❌ Error creating task: {e}")
            raise

    def _schedule_notification_after_commit(self, task_id: str, event_id: str, notification_time: str, notif_source: str = 'notification_time'):
        """
        Lên lịch thông báo sau khi commit task
        """
        try:
            notification_id = f"notif_{task_id}_{int(datetime.now().timestamp())}"
            
            # Sửa format thời gian từ YYYY-MM-DDTHH:MM thành YYYY-MM-DD HH:MM:SS
            try:
                if 'T' in notification_time:
                    # Convert từ 2025-10-17T23:45 thành 2025-10-17 23:45:00
                    dt = datetime.strptime(notification_time, '%Y-%m-%dT%H:%M')
                    formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    formatted_time = notification_time
            except:
                formatted_time = notification_time
            
            # Sử dụng connection riêng để tránh lock
            import sqlite3
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            query = """
            INSERT INTO notifications 
            (notification_id, task_id, event_id, notification_type, 
            scheduled_time, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                notification_id,
                task_id,
                event_id,
                'reminder',
                formatted_time,  # Sử dụng formatted_time
                'pending',
                datetime.now().isoformat()
            )
            
            cursor.execute(query, params)
            conn.commit()
            conn.close()
            
            print(f"✅ Notification scheduled for {formatted_time}")
            
        except Exception as e:
            print(f"⚠️  Error scheduling notification: {e}")
    
    def get_tasks(self, status: str = None, limit: int = 100, user_id: str = None) -> List[Dict[str, Any]]:
        """
        Lấy danh sách tasks
        
        Args:
            status: Lọc theo trạng thái (pending, completed, overdue)
            limit: Số lượng tối đa
            user_id: Lọc theo user_id (nếu None thì lấy tất cả)
        
        Returns:
            List tasks
        """
        try:
            with self.db.get_connection() as conn:
                conditions = []
                params = []
                
                # Thêm điều kiện filter theo user_id nếu có
                if user_id:
                    conditions.append("user_id = ?")
                    params.append(user_id)
                
                # Thêm điều kiện filter theo status nếu có
                if status:
                    conditions.append("status = ?")
                    params.append(status)
                
                # Xây dựng query
                if conditions:
                    where_clause = " WHERE " + " AND ".join(conditions)
                else:
                    where_clause = ""
                
                query = f"SELECT * FROM tasks{where_clause} ORDER BY created_at DESC LIMIT ?"
                params.append(limit)
                
                results = self.db.execute_query(conn, query, tuple(params))
                return results
                
        except Exception as e:
            print(f"❌ Error getting tasks: {e}")
            return []
    
    def update_task_status(self, task_id: str, status: str) -> bool:
        """
        Cập nhật trạng thái task
        
        Args:
            task_id: ID task
            status: Trạng thái mới
        
        Returns:
            True nếu thành công
        """
        try:
            with self.db.get_connection() as conn:
                query = "UPDATE tasks SET status = ?, last_modified = ? WHERE task_id = ?"
                params = (status, datetime.now().isoformat(), task_id)
                
                self.db.execute_update(conn, query, params)
                conn.commit()
                
                print(f"✅ Task {task_id} status updated to {status}")
                return True
                
        except Exception as e:
            print(f"❌ Error updating task status: {e}")
            return False

    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        if not task_id:
            print("❌ update_task: missing task_id")
            return False
        try:
            allowed_fields = [
                'title','description','start_date','end_date','deadline',
                'notification_time','category','priority','status',
                'notif1','notif2','notif3','notif4','notif5','notif6','notif7','notif8'
            ]
            set_strs, params = [], []
            
            # Theo dõi các field notification có thay đổi
            notification_fields_changed = []
            for f in allowed_fields:
                if f in updates:
                    set_strs.append(f"{f} = ?")
                    params.append(updates[f])
                    # Kiểm tra nếu là notification field
                    if f in ['notification_time', 'notif1', 'notif2', 'notif3', 'notif4', 
                            'notif5', 'notif6', 'notif7', 'notif8']:
                        notification_fields_changed.append(f)
            
            if not set_strs:
                return False

            set_strs.append("last_modified = ?")
            params.append(datetime.now().isoformat())
            params.append(task_id)

            sql = f"UPDATE tasks SET {', '.join(set_strs)} WHERE task_id = ?"
            
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(sql, tuple(params))
                conn.commit()
                if cur.rowcount <= 0:
                    print(f"⚠️ update_task: no rows affected for {task_id}")
                    return False
                
                # Nếu có thay đổi notification fields, cần update notifications
                if notification_fields_changed:
                    # Lấy event_id từ calendar_events
                    event_row = conn.execute(
                        "SELECT event_id FROM calendar_events WHERE task_id = ? LIMIT 1",
                        (task_id,)
                    ).fetchone()
                    event_id = event_row[0] if event_row else f"event_{task_id}"
                    
                    # Xóa notifications pending cũ cho task này
                    conn.execute("""
                        DELETE FROM notifications 
                        WHERE task_id = ? AND status = 'pending'
                    """, (task_id,))
                    deleted_count = cur.rowcount
                    print(f"🗑️  Deleted {deleted_count} old pending notifications")
                    
                    # Lấy giá trị notification mới từ updates
                    notification_times = []
                    
                    # notification_time chính
                    if 'notification_time' in updates and updates['notification_time']:
                        notification_times.append(('notification_time', updates['notification_time']))
                    
                    # notif1-8
                    for i in range(1, 9):
                        notif_key = f'notif{i}'
                        if notif_key in updates and updates[notif_key]:
                            notification_times.append((notif_key, updates[notif_key]))
                    
                    # Tạo notifications mới
                    for notif_source, notif_time in notification_times:
                        try:
                            # Format thời gian
                            if 'T' in notif_time:
                                dt = datetime.strptime(notif_time, '%Y-%m-%dT%H:%M')
                                formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                            else:
                                formatted_time = notif_time
                            
                            notification_id = f"notif_{task_id}_{notif_source}_{int(datetime.now().timestamp())}"
                            
                            conn.execute("""
                                INSERT INTO notifications 
                                (notification_id, task_id, event_id, notification_type, 
                                scheduled_time, status, created_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (
                                notification_id,
                                task_id,
                                event_id,
                                'reminder',
                                formatted_time,
                                'pending',
                                datetime.now().isoformat()
                            ))
                            print(f"✅ Created notification from {notif_source}: {formatted_time}")
                        except Exception as e:
                            print(f"⚠️  Error creating notification from {notif_source}: {e}")
                    
                    conn.commit()
            
            print(f"✅ Task {task_id} updated: {updates}")
            return True
        except Exception as e:
            print(f"❌ Error updating task {task_id}: {e}")
            return False
    
    def _schedule_notification(self, task_id: str, event_id: str, notification_time: str):
        """
        Lên lịch thông báo
        
        Args:
            task_id: ID task
            event_id: ID event
            notification_time: Thời gian thông báo
        """
        try:
            notification_id = f"notif_{task_id}_{int(datetime.now().timestamp())}"
            
            # Sử dụng connection riêng để tránh lock
            import sqlite3
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            query = """
            INSERT INTO notifications 
            (notification_id, task_id, event_id, notification_type, 
            scheduled_time, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                notification_id,
                task_id,
                event_id,
                'reminder',
                notification_time,
                'pending',
                datetime.now().isoformat()
            )
            
            cursor.execute(query, params)
            conn.commit()
            conn.close()
            
            print(f"✅ Notification scheduled for {notification_time}")
            
        except Exception as e:
            print(f"⚠️  Error scheduling notification: {e}")
            # Không raise exception để không ảnh hưởng đến việc tạo task

# Test function
def test_simple_task_manager():
    """Test function để kiểm tra SimpleTaskManager hoạt động đúng"""
    try:
        from core.database_manager import DatabaseManager
        
        # Khởi tạo database
        db = DatabaseManager("test_simple_tasks.db")
        
        # Khởi tạo task manager
        manager = SimpleTaskManager(db)
        
        # Test tạo task
        task_data = {
            'title': 'Test Task từ Simple Manager',
            'description': 'Đây là task test cho Simple Task Manager',
            'start_date': '2024-01-15 09:00',
            'end_date': '2024-01-15 17:00',
            'deadline': '2024-01-15 16:00',
            'notification_time': '2024-01-15 15:00',
            'category': 'test',
            'priority': 'high'
        }
        
        task_id = manager.create_task(task_data)
        print(f"✅ create_task() works: {task_id}")
        
        # Test lấy danh sách tasks
        tasks = manager.get_tasks()
        print(f"✅ get_tasks() works: {len(tasks)} tasks")
        
        # Test cập nhật trạng thái
        success = manager.update_task_status(task_id, 'completed')
        print(f"✅ update_task_status() works: {success}")
        
        # Cleanup
        os.remove("test_simple_tasks.db")
        print("✅ Test database cleaned up")
        
        print("🎉 SimpleTaskManager test passed!")
        
    except Exception as e:
        print(f"❌ SimpleTaskManager test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_task_manager()
# SPEC: TASK MODULE ENHANCEMENT - PART 2

> Tiếp theo từ SPEC_TASK_ENHANCEMENT.md

---

## 4. TASK DEPENDENCIES FEATURE (tiếp)

### 4.3. Backend Logic - Dependency Manager

**File:** `backend/task_management/task_dependency_manager.py`

```python
# -*- coding: utf-8 -*-
"""
TASK DEPENDENCY MANAGER
=======================

Quản lý dependencies giữa các tasks

Functions:
- add_dependency(task_id, depends_on_task_id) -> dependency_id
- remove_dependency(dependency_id) -> bool
- get_dependencies(task_id) -> list  (tasks mà task_id phụ thuộc vào)
- get_blocking_tasks(task_id) -> list  (tasks đang bị task_id block)
- check_circular_dependency(task_id, depends_on_task_id) -> bool
- get_dependency_chain(task_id) -> list  (toàn bộ chuỗi dependencies)
- notify_unblocked_tasks(task_id) -> int  (gửi thông báo khi task hoàn thành)
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

class TaskDependencyManager:
    def __init__(self, db):
        self.db = db

    def add_dependency(self, task_id: str, depends_on_task_id: str) -> str:
        """
        Thêm dependency: task_id phụ thuộc vào depends_on_task_id

        Args:
            task_id: Task sẽ bị block
            depends_on_task_id: Task phải hoàn thành trước

        Returns:
            dependency_id

        Raises:
            ValueError: Nếu tạo circular dependency

        Algorithm:
            1. Check circular dependency
            2. Check duplicate
            3. Insert dependency
            4. Return dependency_id
        """
        try:
            # Validate không phải cùng 1 task
            if task_id == depends_on_task_id:
                raise ValueError("Task cannot depend on itself")

            # Check circular dependency
            if self._check_circular_dependency(task_id, depends_on_task_id):
                raise ValueError("Circular dependency detected")

            # Generate ID
            dependency_id = f"dep_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()

            with self.db.get_connection() as conn:
                # Check duplicate
                check_query = """
                    SELECT dependency_id FROM task_dependencies
                    WHERE task_id = ? AND depends_on_task_id = ?
                """
                existing = self.db.execute_query(conn, check_query, (task_id, depends_on_task_id))
                if existing:
                    raise ValueError("Dependency already exists")

                # Insert
                query = """
                    INSERT INTO task_dependencies
                    (dependency_id, task_id, depends_on_task_id, dependency_type, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """
                self.db.execute_insert(conn, query, (
                    dependency_id,
                    task_id,
                    depends_on_task_id,
                    'blocks',
                    now
                ))
                conn.commit()

            print(f"✅ Dependency added: {task_id} depends on {depends_on_task_id}")
            return dependency_id

        except Exception as e:
            print(f"❌ Error adding dependency: {e}")
            raise

    def _check_circular_dependency(self, task_id: str, depends_on_task_id: str, visited: set = None) -> bool:
        """
        Kiểm tra circular dependency

        Args:
            task_id: Task muốn thêm dependency
            depends_on_task_id: Task phụ thuộc vào
            visited: Set các task đã visit (để tránh infinite loop)

        Returns:
            True nếu có circular dependency

        Algorithm (DFS):
            1. Nếu depends_on_task_id == task_id ban đầu → circular
            2. Lấy tất cả tasks mà depends_on_task_id phụ thuộc vào
            3. Đệ quy check từng task đó
            4. Nếu bất kỳ nhánh nào trả về True → circular

        Example:
            A depends on B
            B depends on C
            Nếu muốn C depends on A → circular!

            A → B → C
            └─────┘ (circular)
        """
        if visited is None:
            visited = set()

        # Base case: đã visit rồi
        if depends_on_task_id in visited:
            return False

        # Check trực tiếp
        if depends_on_task_id == task_id:
            return True

        visited.add(depends_on_task_id)

        try:
            with self.db.get_connection() as conn:
                # Lấy tất cả tasks mà depends_on_task_id phụ thuộc vào
                query = """
                    SELECT depends_on_task_id
                    FROM task_dependencies
                    WHERE task_id = ?
                """
                results = self.db.execute_query(conn, query, (depends_on_task_id,))

                for row in results:
                    next_task_id = row['depends_on_task_id']
                    if self._check_circular_dependency(task_id, next_task_id, visited):
                        return True

            return False

        except Exception as e:
            print(f"⚠️  Error checking circular dependency: {e}")
            return False

    def remove_dependency(self, dependency_id: str) -> bool:
        """Xóa dependency"""
        try:
            with self.db.get_connection() as conn:
                query = "DELETE FROM task_dependencies WHERE dependency_id = ?"
                self.db.execute_update(conn, query, (dependency_id,))
                conn.commit()

            print(f"✅ Dependency removed: {dependency_id}")
            return True

        except Exception as e:
            print(f"❌ Error removing dependency: {e}")
            return False

    def get_dependencies(self, task_id: str) -> List[Dict[str, Any]]:
        """
        Lấy danh sách tasks mà task_id phụ thuộc vào

        Returns:
            List of dicts with task info + dependency info
        """
        try:
            with self.db.get_connection() as conn:
                query = """
                    SELECT
                        d.dependency_id,
                        d.depends_on_task_id,
                        t.*
                    FROM task_dependencies d
                    JOIN tasks t ON d.depends_on_task_id = t.task_id
                    WHERE d.task_id = ?
                """
                results = self.db.execute_query(conn, query, (task_id,))
                return results

        except Exception as e:
            print(f"❌ Error getting dependencies: {e}")
            return []

    def get_blocking_tasks(self, task_id: str) -> List[Dict[str, Any]]:
        """
        Lấy danh sách tasks đang bị task_id block

        Returns:
            List of tasks đang chờ task_id hoàn thành
        """
        try:
            with self.db.get_connection() as conn:
                query = """
                    SELECT
                        d.dependency_id,
                        d.task_id as blocked_task_id,
                        t.*
                    FROM task_dependencies d
                    JOIN tasks t ON d.task_id = t.task_id
                    WHERE d.depends_on_task_id = ?
                """
                results = self.db.execute_query(conn, query, (task_id,))
                return results

        except Exception as e:
            print(f"❌ Error getting blocking tasks: {e}")
            return []

    def get_dependency_chain(self, task_id: str, depth: int = 0, max_depth: int = 10) -> List[Dict[str, Any]]:
        """
        Lấy toàn bộ chuỗi dependencies (recursive)

        Returns:
            List of tasks theo thứ tự phụ thuộc

        Example:
            Task D depends on C
            Task C depends on B
            Task B depends on A

            get_dependency_chain('D') returns:
            [
                {'task_id': 'A', 'level': 3, 'title': '...'},
                {'task_id': 'B', 'level': 2, 'title': '...'},
                {'task_id': 'C', 'level': 1, 'title': '...'},
                {'task_id': 'D', 'level': 0, 'title': '...'}
            ]
        """
        if depth >= max_depth:
            return []

        chain = []

        try:
            # Lấy dependencies trực tiếp
            deps = self.get_dependencies(task_id)

            for dep in deps:
                dep_task_id = dep['depends_on_task_id']

                # Đệ quy lấy chain của dependency này
                sub_chain = self.get_dependency_chain(dep_task_id, depth + 1, max_depth)
                chain.extend(sub_chain)

                # Thêm dependency này
                dep['level'] = depth + 1
                chain.append(dep)

            # Thêm task hiện tại (nếu depth > 0)
            if depth == 0:
                with self.db.get_connection() as conn:
                    query = "SELECT * FROM tasks WHERE task_id = ?"
                    task = self.db.execute_query(conn, query, (task_id,))
                    if task:
                        task[0]['level'] = 0
                        chain.append(task[0])

            return chain

        except Exception as e:
            print(f"❌ Error getting dependency chain: {e}")
            return []

    def notify_unblocked_tasks(self, completed_task_id: str) -> int:
        """
        Gửi notification cho owners của tasks đang bị block

        Gọi khi 1 task được đánh dấu completed

        Returns:
            Số notifications đã gửi

        Algorithm:
            1. Lấy tất cả tasks bị block bởi completed_task_id
            2. Với mỗi blocked task:
               - Check xem tất cả dependencies đã completed chưa
               - Nếu rồi → Gửi notification
            3. Return count
        """
        try:
            blocked_tasks = self.get_blocking_tasks(completed_task_id)
            count = 0

            for blocked_task in blocked_tasks:
                blocked_task_id = blocked_task['task_id']

                # Check xem tất cả dependencies đã completed chưa
                all_deps = self.get_dependencies(blocked_task_id)
                all_completed = True

                for dep in all_deps:
                    if dep['status'] != 'completed':
                        all_completed = False
                        break

                if all_completed:
                    # Gửi notification
                    self._send_unblock_notification(blocked_task)
                    count += 1

            return count

        except Exception as e:
            print(f"❌ Error notifying unblocked tasks: {e}")
            return 0

    def _send_unblock_notification(self, task: Dict[str, Any]):
        """
        Gửi notification khi task được unblock

        Integration với notification system hiện có
        """
        try:
            # Tạo notification message
            message = f"✅ Task '{task['title']}' đã được unblock! Tất cả dependencies đã hoàn thành."

            # Import notification system
            from notifications.telegram_notifier import TelegramNotifier
            from utils.config_loader import ConfigLoader

            config = ConfigLoader.load_config()
            notifier = TelegramNotifier(config)

            # Lấy telegram_user_id từ user_id
            with self.db.get_connection() as conn:
                query = "SELECT telegram_user_id FROM users WHERE user_id = ?"
                user = self.db.execute_query(conn, query, (task['user_id'],))

                if user and user[0].get('telegram_user_id'):
                    telegram_id = user[0]['telegram_user_id']
                    notifier.send_notification(telegram_id, message)
                    print(f"✅ Sent unblock notification for task: {task['task_id']}")

        except Exception as e:
            print(f"⚠️  Error sending unblock notification: {e}")


# Integration với SimpleTaskManager
def integrate_with_task_manager():
    """
    Thêm vào SimpleTaskManager.update_task_status():

    def update_task_status(self, task_id: str, status: str) -> bool:
        try:
            # ... existing code ...

            # NEW: Nếu status = completed, notify unblocked tasks
            if status == 'completed':
                from task_management.task_dependency_manager import TaskDependencyManager
                dep_manager = TaskDependencyManager(self.db)
                dep_manager.notify_unblocked_tasks(task_id)

            return True

        except Exception as e:
            print(f"❌ Error updating task status: {e}")
            return False
    """
    pass
```

---

## 5. TASK CHECKLISTS FEATURE

### 5.1. Chức năng

**User stories:**
- Là user, tôi muốn thêm checklist vào task để track progress
- Là user, tôi muốn check/uncheck items
- Hiển thị progress bar (5/10 items completed)

### 5.2. UI Mockup

**Checklist trong task detail:**
```html
┌──────────────────────────────────────────────────────────────┐
│  📋 TASK: Khảo sát công trình Villa Thảo Điền               │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ... (các field khác) ...                                    │
│                                                               │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│                                                               │
│  ☑️ CHECKLIST                                                 │
│                                                               │
│  Progress: 6/10 hoàn thành                                   │
│  ████████████▒▒▒▒▒▒▒▒ 60%                                    │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ ✅ [✓] Đo đạc kích thước căn hộ                       │    │
│  │        ✓ by Nguyễn Hải lúc 10:30 01/11/2025          │    │
│  │                                                       │    │
│  │ ✅ [✓] Chụp ảnh hiện trạng                            │    │
│  │        ✓ by Nguyễn Hải lúc 11:00 01/11/2025          │    │
│  │                                                       │    │
│  │ ✅ [✓] Kiểm tra điều kiện kỹ thuật                    │    │
│  │        ✓ by Nguyễn Hải lúc 11:30 01/11/2025          │    │
│  │                                                       │    │
│  │ ⬜ [ ] Ghi nhận yêu cầu khách hàng                    │    │
│  │        [🗑️ Xóa]                                       │    │
│  │                                                       │    │
│  │ ⬜ [ ] Lập báo cáo khảo sát                           │    │
│  │        [🗑️ Xóa]                                       │    │
│  │                                                       │    │
│  │ ⬜ [ ] Upload báo cáo lên hệ thống                    │    │
│  │        [🗑️ Xóa]                                       │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
│  [+ Thêm checklist item]                                     │
│                                                               │
│  ┌─ Thêm item mới ──────────────────────────────────────┐    │
│  │ ⬜ [Gửi báo cáo cho khách hàng____________]  [💾 Thêm] │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

### 5.3. Backend Logic - Checklist Manager

**File:** `backend/task_management/task_checklist_manager.py`

```python
# -*- coding: utf-8 -*-
"""
TASK CHECKLIST MANAGER
======================

Quản lý checklists trong tasks

Functions:
- add_checklist_item(task_id, item_text, description) -> checklist_id
- toggle_checklist_item(checklist_id, user_id) -> bool
- update_checklist_item(checklist_id, item_text) -> bool
- delete_checklist_item(checklist_id) -> bool
- get_checklist(task_id) -> list
- reorder_checklist(task_id, item_orders) -> bool
- get_checklist_progress(task_id) -> dict
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

class TaskChecklistManager:
    def __init__(self, db):
        self.db = db

    def add_checklist_item(
        self,
        task_id: str,
        item_text: str,
        description: str = None,
        sort_order: int = None
    ) -> str:
        """
        Thêm item vào checklist

        Args:
            task_id: ID task
            item_text: Nội dung item
            description: Mô tả chi tiết (optional)
            sort_order: Thứ tự (optional, auto-increment nếu None)

        Returns:
            checklist_id

        Algorithm:
            1. Nếu sort_order = None → lấy max sort_order + 1
            2. Insert item
            3. Return checklist_id
        """
        try:
            if not item_text:
                raise ValueError("item_text is required")

            # Generate ID
            checklist_id = f"check_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()

            with self.db.get_connection() as conn:
                # Auto sort_order nếu không cung cấp
                if sort_order is None:
                    query = "SELECT MAX(sort_order) as max_order FROM task_checklists WHERE task_id = ?"
                    result = self.db.execute_query(conn, query, (task_id,))
                    max_order = result[0]['max_order'] if result and result[0]['max_order'] else 0
                    sort_order = max_order + 1

                # Insert
                query = """
                    INSERT INTO task_checklists
                    (checklist_id, task_id, item_text, description, is_completed,
                    completed_by, completed_at, sort_order, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """

                self.db.execute_insert(conn, query, (
                    checklist_id,
                    task_id,
                    item_text,
                    description,
                    0,  # is_completed
                    None,  # completed_by
                    None,  # completed_at
                    sort_order,
                    now
                ))
                conn.commit()

            print(f"✅ Checklist item added: {checklist_id}")
            return checklist_id

        except Exception as e:
            print(f"❌ Error adding checklist item: {e}")
            raise

    def toggle_checklist_item(self, checklist_id: str, user_id: str) -> bool:
        """
        Toggle (check/uncheck) checklist item

        Args:
            checklist_id: ID item
            user_id: User đang thao tác

        Returns:
            True nếu thành công

        Algorithm:
            1. Lấy item hiện tại
            2. Nếu is_completed = 0 → set 1, save user_id và completed_at
            3. Nếu is_completed = 1 → set 0, clear user_id và completed_at
            4. Update database
        """
        try:
            with self.db.get_connection() as conn:
                # Get current state
                query = "SELECT is_completed FROM task_checklists WHERE checklist_id = ?"
                result = self.db.execute_query(conn, query, (checklist_id,))

                if not result:
                    raise ValueError(f"Checklist item not found: {checklist_id}")

                current_state = result[0]['is_completed']
                new_state = 0 if current_state else 1

                # Update
                if new_state == 1:
                    # Marking as completed
                    update_query = """
                        UPDATE task_checklists
                        SET is_completed = 1,
                            completed_by = ?,
                            completed_at = ?
                        WHERE checklist_id = ?
                    """
                    params = (user_id, datetime.now().isoformat(), checklist_id)
                else:
                    # Marking as incomplete
                    update_query = """
                        UPDATE task_checklists
                        SET is_completed = 0,
                            completed_by = NULL,
                            completed_at = NULL
                        WHERE checklist_id = ?
                    """
                    params = (checklist_id,)

                self.db.execute_update(conn, update_query, params)
                conn.commit()

            status = "completed" if new_state == 1 else "incomplete"
            print(f"✅ Checklist item {checklist_id} marked as {status}")
            return True

        except Exception as e:
            print(f"❌ Error toggling checklist item: {e}")
            return False

    def update_checklist_item(self, checklist_id: str, item_text: str, description: str = None) -> bool:
        """Cập nhật nội dung checklist item"""
        try:
            with self.db.get_connection() as conn:
                query = """
                    UPDATE task_checklists
                    SET item_text = ?, description = ?
                    WHERE checklist_id = ?
                """
                self.db.execute_update(conn, query, (item_text, description, checklist_id))
                conn.commit()

            print(f"✅ Checklist item updated: {checklist_id}")
            return True

        except Exception as e:
            print(f"❌ Error updating checklist item: {e}")
            return False

    def delete_checklist_item(self, checklist_id: str) -> bool:
        """Xóa checklist item"""
        try:
            with self.db.get_connection() as conn:
                query = "DELETE FROM task_checklists WHERE checklist_id = ?"
                self.db.execute_update(conn, query, (checklist_id,))
                conn.commit()

            print(f"✅ Checklist item deleted: {checklist_id}")
            return True

        except Exception as e:
            print(f"❌ Error deleting checklist item: {e}")
            return False

    def get_checklist(self, task_id: str) -> List[Dict[str, Any]]:
        """
        Lấy tất cả checklist items của task

        Returns:
            List of checklist items (sorted by sort_order)
        """
        try:
            with self.db.get_connection() as conn:
                query = """
                    SELECT
                        c.*,
                        u.display_name as completed_by_name
                    FROM task_checklists c
                    LEFT JOIN users u ON c.completed_by = u.user_id
                    WHERE c.task_id = ?
                    ORDER BY c.sort_order ASC
                """
                results = self.db.execute_query(conn, query, (task_id,))
                return results

        except Exception as e:
            print(f"❌ Error getting checklist: {e}")
            return []

    def reorder_checklist(self, task_id: str, item_orders: Dict[str, int]) -> bool:
        """
        Sắp xếp lại thứ tự checklist items

        Args:
            task_id: ID task
            item_orders: {checklist_id: sort_order, ...}

        Example:
            reorder_checklist('task_123', {
                'check_001': 1,
                'check_002': 2,
                'check_003': 3
            })
        """
        try:
            with self.db.get_connection() as conn:
                for checklist_id, sort_order in item_orders.items():
                    query = """
                        UPDATE task_checklists
                        SET sort_order = ?
                        WHERE checklist_id = ? AND task_id = ?
                    """
                    self.db.execute_update(conn, query, (sort_order, checklist_id, task_id))

                conn.commit()

            print(f"✅ Checklist reordered for task: {task_id}")
            return True

        except Exception as e:
            print(f"❌ Error reordering checklist: {e}")
            return False

    def get_checklist_progress(self, task_id: str) -> Dict[str, Any]:
        """
        Lấy progress của checklist

        Returns:
            {
                'total': 10,
                'completed': 6,
                'percent': 60
            }
        """
        try:
            with self.db.get_connection() as conn:
                query = """
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) as completed
                    FROM task_checklists
                    WHERE task_id = ?
                """
                result = self.db.execute_query(conn, query, (task_id,))

                if result:
                    total = result[0]['total'] or 0
                    completed = result[0]['completed'] or 0
                    percent = (completed / total * 100) if total > 0 else 0

                    return {
                        'total': total,
                        'completed': completed,
                        'percent': round(percent, 1)
                    }

                return {'total': 0, 'completed': 0, 'percent': 0}

        except Exception as e:
            print(f"❌ Error getting checklist progress: {e}")
            return {'total': 0, 'completed': 0, 'percent': 0}


# Test function
def test_checklist_manager():
    """Test TaskChecklistManager"""
    from core.database_manager import DatabaseManager

    db = DatabaseManager("test_checklist.db")
    manager = TaskChecklistManager(db)

    task_id = "test_task_001"

    # Add items
    items = [
        "Đo đạc kích thước",
        "Chụp ảnh",
        "Ghi nhận yêu cầu",
        "Lập báo cáo"
    ]

    item_ids = []
    for item in items:
        item_id = manager.add_checklist_item(task_id, item)
        item_ids.append(item_id)

    # Toggle first 2 items
    manager.toggle_checklist_item(item_ids[0], "user_123")
    manager.toggle_checklist_item(item_ids[1], "user_123")

    # Get checklist
    checklist = manager.get_checklist(task_id)
    print(f"✅ Checklist: {len(checklist)} items")

    # Get progress
    progress = manager.get_checklist_progress(task_id)
    print(f"✅ Progress: {progress['completed']}/{progress['total']} ({progress['percent']}%)")

    # Cleanup
    import os
    os.remove("test_checklist.db")
    print("✅ Test passed!")

if __name__ == "__main__":
    test_checklist_manager()
```

---

## 6. BACKEND IMPLEMENTATION SUMMARY

### 6.1. Files cần tạo mới

```
backend/task_management/
├── simple_task_manager.py          [ĐÃ CÓ - cần modify]
├── task_template_manager.py        [MỚI]
├── recurring_task_manager.py       [MỚI]
├── task_dependency_manager.py      [MỚI]
└── task_checklist_manager.py       [MỚI]
```

### 6.2. Modifications cần thiết cho SimpleTaskManager

**File:** `backend/task_management/simple_task_manager.py`

Thêm vào method `update_task_status`:

```python
def update_task_status(self, task_id: str, status: str) -> bool:
    try:
        with self.db.get_connection() as conn:
            query = "UPDATE tasks SET status = ?, last_modified = ? WHERE task_id = ?"
            params = (status, datetime.now().isoformat(), task_id)

            self.db.execute_update(conn, query, params)
            conn.commit()

            # === THÊM PHẦN NÀY ===
            # Nếu status = completed, notify unblocked tasks
            if status == 'completed':
                try:
                    from task_management.task_dependency_manager import TaskDependencyManager
                    dep_manager = TaskDependencyManager(self.db)
                    dep_manager.notify_unblocked_tasks(task_id)
                except Exception as e:
                    print(f"⚠️  Error notifying unblocked tasks: {e}")
            # === KẾT THÚC PHẦN THÊM ===

            print(f"✅ Task {task_id} status updated to {status}")
            return True

    except Exception as e:
        print(f"❌ Error updating task status: {e}")
        return False
```

---

## 7. FRONTEND IMPLEMENTATION

### 7.1. Routes cần thêm vào `frontend/app.py`

```python
# ==================== TASK TEMPLATES ====================

@app.route('/templates', methods=['GET'])
@require_login
def task_templates():
    """Trang quản lý task templates"""
    user_id = session.get('user_id')

    from backend.task_management.task_template_manager import TaskTemplateManager
    manager = TaskTemplateManager(db)

    # Lấy templates (cá nhân + shared)
    templates = manager.get_all_templates(user_id, include_shared=True)

    return render_template('tasks/task_templates.html', templates=templates)


@app.route('/template/create', methods=['GET', 'POST'])
@require_login
def create_template():
    """Tạo task template mới"""
    if request.method == 'POST':
        user_id = session.get('user_id')
        template_data = {
            'user_id': user_id if not request.form.get('is_shared') else None,
            'template_name': request.form.get('template_name'),
            'template_description': request.form.get('template_description'),
            'default_title': request.form.get('default_title'),
            'default_description': request.form.get('default_description'),
            'default_category': request.form.get('default_category'),
            'default_priority': request.form.get('default_priority'),
            'default_duration_hours': int(request.form.get('default_duration_hours', 1)),
            'is_shared': bool(request.form.get('is_shared')),
            'created_by': user_id
        }

        # Notification presets
        for i in range(1, 9):
            template_data[f'notif{i}_offset'] = request.form.get(f'notif{i}_offset')
            template_data[f'notif{i}_label'] = request.form.get(f'notif{i}_label')

        from backend.task_management.task_template_manager import TaskTemplateManager
        manager = TaskTemplateManager(db)

        try:
            template_id = manager.create_template(template_data)
            flash(f'Template created successfully: {template_id}', 'success')
            return redirect(url_for('task_templates'))
        except Exception as e:
            flash(f'Error creating template: {e}', 'error')

    return render_template('tasks/create_template.html')


@app.route('/template/<template_id>/edit', methods=['GET', 'POST'])
@require_login
def edit_template(template_id):
    """Sửa template"""
    from backend.task_management.task_template_manager import TaskTemplateManager
    manager = TaskTemplateManager(db)

    if request.method == 'POST':
        updates = {
            'template_name': request.form.get('template_name'),
            'template_description': request.form.get('template_description'),
            'default_title': request.form.get('default_title'),
            # ... các field khác
        }

        try:
            manager.update_template(template_id, updates)
            flash('Template updated successfully', 'success')
            return redirect(url_for('task_templates'))
        except Exception as e:
            flash(f'Error updating template: {e}', 'error')

    template = manager.get_template(template_id)
    return render_template('tasks/edit_template.html', template=template)


@app.route('/template/<template_id>/delete', methods=['POST'])
@require_login
def delete_template(template_id):
    """Xóa template"""
    from backend.task_management.task_template_manager import TaskTemplateManager
    manager = TaskTemplateManager(db)

    try:
        manager.delete_template(template_id)
        flash('Template deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting template: {e}', 'error')

    return redirect(url_for('task_templates'))


@app.route('/task/create_from_template/<template_id>', methods=['GET', 'POST'])
@require_login
def create_task_from_template(template_id):
    """Tạo task từ template"""
    from backend.task_management.task_template_manager import TaskTemplateManager
    manager = TaskTemplateManager(db)

    if request.method == 'POST':
        user_id = session.get('user_id')

        task_data = {
            'user_id': user_id,
            'start_date': request.form.get('start_date'),
            'variables': {
                'customer_name': request.form.get('customer_name', ''),
                'project_name': request.form.get('project_name', ''),
                # ... các biến khác
            },
            # Optional overrides
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'category': request.form.get('category'),
            'priority': request.form.get('priority')
        }

        try:
            task_id = manager.use_template(template_id, task_data)
            flash(f'Task created from template: {task_id}', 'success')
            return redirect(url_for('task_detail', task_id=task_id))
        except Exception as e:
            flash(f'Error creating task: {e}', 'error')

    template = manager.get_template(template_id)
    return render_template('tasks/create_from_template.html', template=template)


# ==================== RECURRING TASKS ====================

@app.route('/recurring_tasks', methods=['GET'])
@require_login
def recurring_tasks():
    """Trang quản lý recurring tasks"""
    user_id = session.get('user_id')

    with db.get_connection() as conn:
        query = """
            SELECT r.*, t.title, t.start_date, t.category
            FROM task_recurrence r
            JOIN tasks t ON r.parent_task_id = t.task_id
            WHERE r.user_id = ?
            ORDER BY r.is_active DESC, r.next_occurrence_date ASC
        """
        recurrences = db.execute_query(conn, query, (user_id,))

    return render_template('tasks/recurring_tasks.html', recurrences=recurrences)


@app.route('/recurrence/<recurrence_id>/pause', methods=['POST'])
@require_login
def pause_recurrence(recurrence_id):
    """Tạm dừng recurring task"""
    from backend.task_management.recurring_task_manager import RecurringTaskManager
    manager = RecurringTaskManager(db)

    try:
        manager.pause_recurrence(recurrence_id)
        flash('Recurrence paused', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'error')

    return redirect(url_for('recurring_tasks'))


@app.route('/recurrence/<recurrence_id>/resume', methods=['POST'])
@require_login
def resume_recurrence(recurrence_id):
    """Tiếp tục recurring task"""
    from backend.task_management.recurring_task_manager import RecurringTaskManager
    manager = RecurringTaskManager(db)

    try:
        manager.resume_recurrence(recurrence_id)
        flash('Recurrence resumed', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'error')

    return redirect(url_for('recurring_tasks'))


@app.route('/recurrence/<recurrence_id>/delete', methods=['POST'])
@require_login
def delete_recurrence(recurrence_id):
    """Xóa recurring task"""
    from backend.task_management.recurring_task_manager import RecurringTaskManager
    manager = RecurringTaskManager(db)

    delete_instances = request.form.get('delete_instances') == '1'

    try:
        manager.delete_recurrence(recurrence_id, delete_instances)
        flash('Recurrence deleted', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'error')

    return redirect(url_for('recurring_tasks'))


# ==================== TASK DEPENDENCIES ====================

@app.route('/api/task/<task_id>/dependencies', methods=['GET', 'POST', 'DELETE'])
@require_login
def task_dependencies(task_id):
    """API để quản lý task dependencies"""
    from backend.task_management.task_dependency_manager import TaskDependencyManager
    manager = TaskDependencyManager(db)

    if request.method == 'GET':
        # Lấy dependencies
        deps = manager.get_dependencies(task_id)
        blocking = manager.get_blocking_tasks(task_id)

        return jsonify({
            'dependencies': deps,
            'blocking': blocking
        })

    elif request.method == 'POST':
        # Thêm dependency
        depends_on_task_id = request.json.get('depends_on_task_id')

        try:
            dependency_id = manager.add_dependency(task_id, depends_on_task_id)
            return jsonify({'success': True, 'dependency_id': dependency_id})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400

    elif request.method == 'DELETE':
        # Xóa dependency
        dependency_id = request.json.get('dependency_id')

        try:
            manager.remove_dependency(dependency_id)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400


# ==================== TASK CHECKLISTS ====================

@app.route('/api/task/<task_id>/checklist', methods=['GET', 'POST'])
@require_login
def task_checklist(task_id):
    """API để quản lý checklist"""
    from backend.task_management.task_checklist_manager import TaskChecklistManager
    manager = TaskChecklistManager(db)

    if request.method == 'GET':
        # Lấy checklist
        checklist = manager.get_checklist(task_id)
        progress = manager.get_checklist_progress(task_id)

        return jsonify({
            'checklist': checklist,
            'progress': progress
        })

    elif request.method == 'POST':
        # Thêm item mới
        item_text = request.json.get('item_text')
        description = request.json.get('description')

        try:
            checklist_id = manager.add_checklist_item(task_id, item_text, description)
            return jsonify({'success': True, 'checklist_id': checklist_id})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/checklist/<checklist_id>/toggle', methods=['POST'])
@require_login
def toggle_checklist_item(checklist_id):
    """Toggle checklist item"""
    from backend.task_management.task_checklist_manager import TaskChecklistManager
    manager = TaskChecklistManager(db)

    user_id = session.get('user_id')

    try:
        manager.toggle_checklist_item(checklist_id, user_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/checklist/<checklist_id>', methods=['PUT', 'DELETE'])
@require_login
def manage_checklist_item(checklist_id):
    """Sửa hoặc xóa checklist item"""
    from backend.task_management.task_checklist_manager import TaskChecklistManager
    manager = TaskChecklistManager(db)

    if request.method == 'PUT':
        # Update item
        item_text = request.json.get('item_text')
        description = request.json.get('description')

        try:
            manager.update_checklist_item(checklist_id, item_text, description)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400

    elif request.method == 'DELETE':
        # Delete item
        try:
            manager.delete_checklist_item(checklist_id)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
```

---

## 8. API ENDPOINTS SUMMARY

### Task Templates
```
GET    /templates                              - List all templates
GET    /template/create                        - Form tạo template
POST   /template/create                        - Submit tạo template
GET    /template/<template_id>/edit            - Form sửa template
POST   /template/<template_id>/edit            - Submit sửa template
POST   /template/<template_id>/delete          - Xóa template
GET    /task/create_from_template/<template_id> - Form tạo task từ template
POST   /task/create_from_template/<template_id> - Submit tạo task
```

### Recurring Tasks
```
GET    /recurring_tasks                        - List recurring tasks
POST   /recurrence/<recurrence_id>/pause       - Tạm dừng
POST   /recurrence/<recurrence_id>/resume      - Tiếp tục
POST   /recurrence/<recurrence_id>/delete      - Xóa
```

### Task Dependencies
```
GET    /api/task/<task_id>/dependencies        - Lấy dependencies
POST   /api/task/<task_id>/dependencies        - Thêm dependency
DELETE /api/task/<task_id>/dependencies        - Xóa dependency
```

### Task Checklists
```
GET    /api/task/<task_id>/checklist           - Lấy checklist
POST   /api/task/<task_id>/checklist           - Thêm item
POST   /api/checklist/<checklist_id>/toggle    - Toggle item
PUT    /api/checklist/<checklist_id>           - Update item
DELETE /api/checklist/<checklist_id>           - Xóa item
```

---

## 9. MIGRATION SCRIPTS

### File: `migrations/010_task_enhancements.py`

```python
# -*- coding: utf-8 -*-
"""
Migration: Task Enhancements
- task_templates
- task_recurrence
- task_dependencies
- task_checklists
- ALTER tasks table
"""

import sqlite3

DB_PATH = "database/calendar_tools.db"

def run_migration():
    """Run all task enhancement migrations"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("🔄 Running task enhancement migrations...")

    # 1. Create task_templates
    print("  Creating task_templates table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_templates (
            template_id TEXT PRIMARY KEY,
            user_id TEXT,
            template_name TEXT NOT NULL,
            template_description TEXT,
            default_title TEXT NOT NULL,
            default_description TEXT,
            default_category TEXT,
            default_priority TEXT,
            notif1_offset TEXT,
            notif1_label TEXT,
            notif2_offset TEXT,
            notif2_label TEXT,
            notif3_offset TEXT,
            notif3_label TEXT,
            notif4_offset TEXT,
            notif4_label TEXT,
            notif5_offset TEXT,
            notif5_label TEXT,
            notif6_offset TEXT,
            notif6_label TEXT,
            notif7_offset TEXT,
            notif7_label TEXT,
            notif8_offset TEXT,
            notif8_label TEXT,
            default_duration_hours INTEGER,
            is_shared BOOLEAN DEFAULT 0,
            created_by TEXT,
            usage_count INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (created_by) REFERENCES users(user_id)
        )
    """)

    # Index
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_templates_user ON task_templates(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_templates_shared ON task_templates(is_shared)")

    # 2. Create task_recurrence
    print("  Creating task_recurrence table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_recurrence (
            recurrence_id TEXT PRIMARY KEY,
            parent_task_id TEXT NOT NULL,
            user_id TEXT,
            frequency TEXT NOT NULL,
            interval INTEGER DEFAULT 1,
            weekdays TEXT,
            day_of_month INTEGER,
            week_of_month INTEGER,
            day_of_week TEXT,
            custom_pattern TEXT,
            start_date TEXT NOT NULL,
            end_date TEXT,
            max_occurrences INTEGER,
            last_generated_date TEXT,
            next_occurrence_date TEXT,
            occurrences_count INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (parent_task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # Index
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_recurrence_parent ON task_recurrence(parent_task_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_recurrence_active ON task_recurrence(is_active)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_recurrence_next ON task_recurrence(next_occurrence_date)")

    # 3. Create task_dependencies
    print("  Creating task_dependencies table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_dependencies (
            dependency_id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL,
            depends_on_task_id TEXT NOT NULL,
            dependency_type TEXT DEFAULT 'blocks',
            created_at TEXT,
            FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
            FOREIGN KEY (depends_on_task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
            CHECK (task_id != depends_on_task_id)
        )
    """)

    # Index
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_dependencies_task ON task_dependencies(task_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_dependencies_depends ON task_dependencies(depends_on_task_id)")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_dependency ON task_dependencies(task_id, depends_on_task_id)")

    # 4. Create task_checklists
    print("  Creating task_checklists table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_checklists (
            checklist_id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL,
            item_text TEXT NOT NULL,
            description TEXT,
            is_completed BOOLEAN DEFAULT 0,
            completed_by TEXT,
            completed_at TEXT,
            sort_order INTEGER DEFAULT 0,
            created_at TEXT,
            FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
            FOREIGN KEY (completed_by) REFERENCES users(user_id)
        )
    """)

    # Index
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_checklists_task ON task_checklists(task_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_checklists_order ON task_checklists(task_id, sort_order)")

    # 5. ALTER tasks table
    print("  Altering tasks table...")

    def column_exists(table, column):
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        return column in columns

    if not column_exists('tasks', 'parent_task_id'):
        cursor.execute("ALTER TABLE tasks ADD COLUMN parent_task_id TEXT")

    if not column_exists('tasks', 'template_id'):
        cursor.execute("ALTER TABLE tasks ADD COLUMN template_id TEXT")

    if not column_exists('tasks', 'recurrence_id'):
        cursor.execute("ALTER TABLE tasks ADD COLUMN recurrence_id TEXT")

    if not column_exists('tasks', 'is_recurring_instance'):
        cursor.execute("ALTER TABLE tasks ADD COLUMN is_recurring_instance BOOLEAN DEFAULT 0")

    # Commit
    conn.commit()
    conn.close()

    print("✅ Task enhancement migrations completed!")

if __name__ == "__main__":
    run_migration()
```

### File: `migrations/011_seed_task_templates.py`

```python
# -*- coding: utf-8 -*-
"""
Seed default task templates
"""

import sqlite3
from datetime import datetime

DB_PATH = "database/calendar_tools.db"

TEMPLATES = [
    {
        'template_id': 'tmpl_default_001',
        'template_name': 'Gọi điện chào khách hàng mới',
        'template_description': 'Template cho việc liên hệ khách hàng lần đầu',
        'default_title': 'Gọi điện cho {customer_name}',
        'default_description': 'Liên hệ khách hàng để giới thiệu sản phẩm/dịch vụ.\n\nChuẩn bị:\n- Tài liệu giới thiệu\n- Báo giá\n- Case study',
        'default_category': 'sales',
        'default_priority': 'high',
        'notif1_offset': '-1 hour',
        'notif1_label': 'Nhắc trước 1 giờ',
        'notif2_offset': '-10 minutes',
        'notif2_label': 'Nhắc trước 10 phút',
        'default_duration_hours': 1,
        'is_shared': 1
    },
    {
        'template_id': 'tmpl_default_002',
        'template_name': 'Follow up khách hàng sau 3 ngày',
        'template_description': 'Template cho việc follow up khách hàng',
        'default_title': 'Follow up: {customer_name}',
        'default_description': 'Liên hệ lại khách hàng sau cuộc trao đổi lần đầu.\n\nNội dung:\n- Hỏi feedback\n- Giải đáp thắc mắc\n- Gửi thông tin bổ sung',
        'default_category': 'sales',
        'default_priority': 'medium',
        'notif1_offset': '-1 day',
        'notif1_label': 'Nhắc trước 1 ngày',
        'default_duration_hours': 1,
        'is_shared': 1
    },
    {
        'template_id': 'tmpl_default_003',
        'template_name': 'Khảo sát công trình',
        'template_description': 'Template cho việc khảo sát hiện trường',
        'default_title': 'Khảo sát công trình: {project_name}',
        'default_description': 'Khảo sát hiện trường tại địa chỉ: {address}\n\nCông việc:\n- Đo đạc kích thước\n- Chụp ảnh hiện trạng\n- Kiểm tra điều kiện kỹ thuật\n- Ghi nhận yêu cầu khách hàng\n- Lập báo cáo khảo sát',
        'default_category': 'project',
        'default_priority': 'high',
        'notif1_offset': '-1 day',
        'notif1_label': 'Nhắc trước 1 ngày',
        'notif2_offset': '-2 hours',
        'notif2_label': 'Nhắc trước 2 giờ',
        'default_duration_hours': 3,
        'is_shared': 1
    },
    {
        'template_id': 'tmpl_default_004',
        'template_name': 'Họp team hàng tuần',
        'template_description': 'Template cho meeting team',
        'default_title': 'Họp team - {date}',
        'default_description': 'Weekly team meeting\n\nAgenda:\n- Review tiến độ tuần trước\n- Plan công việc tuần này\n- Giải quyết vấn đề\n- Q&A',
        'default_category': 'meeting',
        'default_priority': 'medium',
        'notif1_offset': '-30 minutes',
        'notif1_label': 'Nhắc trước 30 phút',
        'default_duration_hours': 1,
        'is_shared': 1
    }
]

def seed_templates():
    """Seed default templates"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("🌱 Seeding default task templates...")

    now = datetime.now().isoformat()

    for template in TEMPLATES:
        # Check nếu đã tồn tại
        cursor.execute(
            "SELECT template_id FROM task_templates WHERE template_id = ?",
            (template['template_id'],)
        )

        if cursor.fetchone():
            print(f"  ⏭️  Template {template['template_id']} already exists, skipping")
            continue

        # Insert
        template['user_id'] = None  # Shared template
        template['created_by'] = None
        template['usage_count'] = 0
        template['created_at'] = now
        template['updated_at'] = now

        # Fill missing notif fields
        for i in range(1, 9):
            if f'notif{i}_offset' not in template:
                template[f'notif{i}_offset'] = None
                template[f'notif{i}_label'] = None

        columns = ', '.join(template.keys())
        placeholders = ', '.join(['?' for _ in template])
        query = f"INSERT INTO task_templates ({columns}) VALUES ({placeholders})"

        cursor.execute(query, tuple(template.values()))
        print(f"  ✅ Created template: {template['template_name']}")

    conn.commit()
    conn.close()

    print("✅ Template seeding completed!")

if __name__ == "__main__":
    seed_templates()
```

---

## 10. TESTING & VALIDATION

### Test Cases

#### Task Templates:
1. ✅ Tạo template mới (personal & shared)
2. ✅ Load template và fill form
3. ✅ Tạo task từ template với variable replacement
4. ✅ Update template
5. ✅ Delete template
6. ✅ Notification offset calculation
7. ✅ Usage count increment

#### Recurring Tasks:
1. ✅ Tạo daily recurrence
2. ✅ Tạo weekly recurrence với multiple weekdays
3. ✅ Tạo monthly recurrence
4. ✅ Generate next occurrence
5. ✅ Pause/Resume recurrence
6. ✅ End date limit
7. ✅ Max occurrences limit
8. ✅ Background processor

#### Task Dependencies:
1. ✅ Thêm dependency
2. ✅ Kiểm tra circular dependency
3. ✅ Xóa dependency
4. ✅ Lấy dependency chain
5. ✅ Notify unblocked tasks khi complete
6. ✅ Display dependency trong UI

#### Task Checklists:
1. ✅ Thêm checklist item
2. ✅ Toggle item
3. ✅ Update item
4. ✅ Delete item
5. ✅ Reorder items
6. ✅ Calculate progress
7. ✅ Display progress bar

---

## 11. DEPLOYMENT CHECKLIST

```
□ 1. Backup database hiện tại
□ 2. Run migration 010_task_enhancements.py
□ 3. Run seed 011_seed_task_templates.py
□ 4. Copy các file backend mới:
     - task_template_manager.py
     - recurring_task_manager.py
     - task_dependency_manager.py
     - task_checklist_manager.py
□ 5. Update frontend/app.py với routes mới
□ 6. Tạo HTML templates mới:
     - tasks/task_templates.html
     - tasks/create_template.html
     - tasks/edit_template.html
     - tasks/create_from_template.html
     - tasks/recurring_tasks.html
□ 7. Update tasks/task_detail.html với:
     - Dependencies section
     - Checklist section
     - Progress bar
□ 8. Setup cron job cho recurring_task_manager.py
     Ví dụ: 0 * * * * python3 backend/task_management/recurring_task_manager.py
□ 9. Test tất cả features
□ 10. Deploy to production
```

---

## 12. FUTURE ENHANCEMENTS

1. **Task Templates từ AI**
   - Suggest templates dựa trên task history
   - AI generate template description

2. **Smart Recurring**
   - Auto-adjust schedule based on completion patterns
   - Skip holidays

3. **Dependency Gantt Chart**
   - Visual timeline với dependencies
   - Drag & drop để adjust dates

4. **Checklist Templates**
   - Pre-defined checklists cho từng loại task
   - Clone checklist từ task khác

5. **Collaboration**
   - Assign checklist items cho users khác
   - Comments trên từng item

---

**END OF SPEC: TASK MODULE ENHANCEMENT**

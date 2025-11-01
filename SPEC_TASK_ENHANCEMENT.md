# SPEC: TASK MODULE ENHANCEMENT - PHÁT TRIỂN TÍNH NĂNG QUẢN LÝ TASKS

> **Mục đích:** Nâng cấp module Tasks hiện tại với các tính năng mới: Task Templates, Recurring Tasks, Task Dependencies, và Checklists
>
> **Codebase hiện tại:** Python/Flask + SQLite
>
> **File cần modify:**
> - `backend/task_management/simple_task_manager.py`
> - `frontend/app.py`
> - Database: `database/calendar_tools.db`

---

## 📋 MỤC LỤC

1. [Database Schema Changes](#1-database-schema-changes)
2. [Task Templates Feature](#2-task-templates-feature)
3. [Recurring Tasks Feature](#3-recurring-tasks-feature)
4. [Task Dependencies Feature](#4-task-dependencies-feature)
5. [Task Checklists Feature](#5-task-checklists-feature)
6. [Backend Implementation](#6-backend-implementation)
7. [Frontend Implementation](#7-frontend-implementation)
8. [API Endpoints](#8-api-endpoints)
9. [Migration Scripts](#9-migration-scripts)

---

## 1. DATABASE SCHEMA CHANGES

### 1.1. Bảng hiện tại: `tasks`

```sql
-- Bảng tasks hiện có (KHÔNG SỬA)
CREATE TABLE tasks (
    task_id TEXT PRIMARY KEY,
    user_id TEXT,
    title TEXT NOT NULL,
    description TEXT,
    start_date TEXT,
    end_date TEXT,
    deadline TEXT,
    notification_time TEXT,
    notif1 TEXT, notif2 TEXT, notif3 TEXT, notif4 TEXT,
    notif5 TEXT, notif6 TEXT, notif7 TEXT, notif8 TEXT,
    category TEXT,
    priority TEXT,
    status TEXT,
    created_at TEXT,
    last_modified TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

### 1.2. Bảng mới cần tạo

#### A. `task_templates` - Mẫu tác vụ

```sql
CREATE TABLE task_templates (
    template_id TEXT PRIMARY KEY,           -- "tmpl_abc123"
    user_id TEXT,                           -- NULL = shared template cho toàn bộ team
    template_name TEXT NOT NULL,            -- "Gọi điện chào khách hàng mới"
    template_description TEXT,              -- Mô tả template

    -- Default values cho task
    default_title TEXT NOT NULL,            -- "Gọi điện cho {customer_name}"
    default_description TEXT,               -- "Liên hệ khách hàng để..."
    default_category TEXT,                  -- "customer_follow_up"
    default_priority TEXT,                  -- "high"

    -- Notification presets (offset từ start_date)
    notif1_offset TEXT,                     -- "-1 day" = 1 ngày trước start_date
    notif1_label TEXT,                      -- "Nhắc trước 1 ngày"
    notif2_offset TEXT,                     -- "-3 hours"
    notif2_label TEXT,                      -- "Nhắc trước 3 giờ"
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

    -- Duration preset
    default_duration_hours INTEGER,         -- 2 (task kéo dài 2 giờ)

    -- Sharing
    is_shared BOOLEAN DEFAULT 0,            -- 1 = template chung, 0 = cá nhân
    created_by TEXT,                        -- user_id người tạo

    -- Metadata
    usage_count INTEGER DEFAULT 0,          -- Số lần dùng template
    created_at TEXT,
    updated_at TEXT,

    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

-- Index
CREATE INDEX idx_task_templates_user ON task_templates(user_id);
CREATE INDEX idx_task_templates_shared ON task_templates(is_shared);
```

**Sample Data:**
```sql
INSERT INTO task_templates VALUES (
    'tmpl_001',
    NULL,  -- Shared template
    'Gọi điện chào khách hàng mới',
    'Template cho việc liên hệ khách hàng lần đầu',
    'Gọi điện giới thiệu cho {customer_name}',
    'Liên hệ khách hàng để giới thiệu sản phẩm/dịch vụ. Chuẩn bị:\n- Tài liệu giới thiệu\n- Báo giá\n- Case study',
    'sales',
    'high',
    '-1 hour', 'Nhắc trước 1 giờ',
    '-10 minutes', 'Nhắc trước 10 phút',
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    1,  -- 1 hour duration
    1,  -- is_shared
    'admin_user_id',
    0,  -- usage_count
    '2025-11-01 10:00:00',
    '2025-11-01 10:00:00'
);
```

---

#### B. `task_recurrence` - Lặp lại tác vụ

```sql
CREATE TABLE task_recurrence (
    recurrence_id TEXT PRIMARY KEY,         -- "recur_abc123"
    parent_task_id TEXT NOT NULL,           -- ID của task gốc (template)
    user_id TEXT,

    -- Recurrence pattern
    frequency TEXT NOT NULL,                -- "daily", "weekly", "monthly", "custom"
    interval INTEGER DEFAULT 1,             -- Lặp mỗi X đơn vị (1=mỗi ngày, 2=2 ngày/lần)

    -- For weekly
    weekdays TEXT,                          -- JSON: ["monday", "wednesday", "friday"]

    -- For monthly
    day_of_month INTEGER,                   -- 15 = ngày 15 hàng tháng
    week_of_month INTEGER,                  -- 2 = tuần thứ 2
    day_of_week TEXT,                       -- "monday" = thứ 2

    -- For custom
    custom_pattern TEXT,                    -- JSON hoặc cron-like

    -- Duration
    start_date TEXT NOT NULL,               -- Bắt đầu lặp từ ngày nào
    end_date TEXT,                          -- NULL = vô hạn
    max_occurrences INTEGER,                -- NULL = vô hạn, hoặc số lần tối đa

    -- Tracking
    last_generated_date TEXT,               -- Ngày generate task cuối cùng
    next_occurrence_date TEXT,              -- Ngày sẽ generate task tiếp theo
    occurrences_count INTEGER DEFAULT 0,    -- Đã generate bao nhiêu tasks

    -- Status
    is_active BOOLEAN DEFAULT 1,            -- 0 = tạm dừng, 1 = đang chạy

    created_at TEXT,
    updated_at TEXT,

    FOREIGN KEY (parent_task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Index
CREATE INDEX idx_task_recurrence_parent ON task_recurrence(parent_task_id);
CREATE INDEX idx_task_recurrence_active ON task_recurrence(is_active);
CREATE INDEX idx_task_recurrence_next ON task_recurrence(next_occurrence_date);
```

**Sample Data:**
```sql
-- Recurring task: Họp team hàng tuần
INSERT INTO task_recurrence VALUES (
    'recur_001',
    'task_parent_001',  -- Task gốc
    'user_123',
    'weekly',           -- Hàng tuần
    1,                  -- Mỗi tuần
    '["monday", "friday"]',  -- Thứ 2 và Thứ 6
    NULL, NULL, NULL,
    NULL,
    '2025-11-01',       -- Bắt đầu
    '2026-01-31',       -- Kết thúc
    NULL,               -- Không giới hạn số lần
    '2025-11-01',       -- Lần cuối generate
    '2025-11-04',       -- Lần tiếp theo (Thứ 2)
    1,                  -- Đã generate 1 task
    1,                  -- Active
    '2025-11-01 08:00:00',
    '2025-11-01 08:00:00'
);
```

---

#### C. `task_dependencies` - Phụ thuộc task

```sql
CREATE TABLE task_dependencies (
    dependency_id TEXT PRIMARY KEY,         -- "dep_abc123"
    task_id TEXT NOT NULL,                  -- Task bị block
    depends_on_task_id TEXT NOT NULL,       -- Task phải hoàn thành trước
    dependency_type TEXT DEFAULT 'blocks',  -- "blocks" hoặc "blocked_by"

    created_at TEXT,

    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,

    -- Prevent circular dependencies
    CHECK (task_id != depends_on_task_id)
);

-- Index
CREATE INDEX idx_task_dependencies_task ON task_dependencies(task_id);
CREATE INDEX idx_task_dependencies_depends ON task_dependencies(depends_on_task_id);

-- Unique constraint: không cho phép duplicate dependencies
CREATE UNIQUE INDEX idx_unique_dependency ON task_dependencies(task_id, depends_on_task_id);
```

**Sample Data:**
```sql
-- Task B phụ thuộc vào Task A
INSERT INTO task_dependencies VALUES (
    'dep_001',
    'task_B_design',           -- Task thiết kế
    'task_A_survey',           -- Phải hoàn thành khảo sát trước
    'blocks',
    '2025-11-01 10:00:00'
);
```

---

#### D. `task_checklists` - Checklist trong task

```sql
CREATE TABLE task_checklists (
    checklist_id TEXT PRIMARY KEY,          -- "check_abc123"
    task_id TEXT NOT NULL,

    item_text TEXT NOT NULL,                -- "Đo đạc kích thước phòng khách"
    description TEXT,                       -- Mô tả chi tiết hơn (optional)

    is_completed BOOLEAN DEFAULT 0,
    completed_by TEXT,                      -- user_id người check
    completed_at TEXT,

    sort_order INTEGER DEFAULT 0,           -- Thứ tự hiển thị

    created_at TEXT,

    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (completed_by) REFERENCES users(user_id)
);

-- Index
CREATE INDEX idx_task_checklists_task ON task_checklists(task_id);
CREATE INDEX idx_task_checklists_order ON task_checklists(task_id, sort_order);
```

**Sample Data:**
```sql
-- Checklist cho task khảo sát
INSERT INTO task_checklists VALUES
('check_001', 'task_survey_001', 'Đo đạc kích thước căn hộ', NULL, 1, 'user_123', '2025-11-01 15:30:00', 1, '2025-11-01 10:00:00'),
('check_002', 'task_survey_001', 'Chụp ảnh hiện trạng', NULL, 1, 'user_123', '2025-11-01 15:45:00', 2, '2025-11-01 10:00:00'),
('check_003', 'task_survey_001', 'Ghi nhận yêu cầu khách hàng', NULL, 0, NULL, NULL, 3, '2025-11-01 10:00:00'),
('check_004', 'task_survey_001', 'Kiểm tra điều kiện kỹ thuật', NULL, 0, NULL, NULL, 4, '2025-11-01 10:00:00');
```

---

#### E. Thêm cột vào bảng `tasks` (ALTER TABLE)

```sql
-- Thêm các cột mới vào bảng tasks hiện có
ALTER TABLE tasks ADD COLUMN parent_task_id TEXT;              -- Nếu task này được tạo từ recurring
ALTER TABLE tasks ADD COLUMN template_id TEXT;                 -- Nếu task tạo từ template
ALTER TABLE tasks ADD COLUMN recurrence_id TEXT;               -- Link to recurrence config
ALTER TABLE tasks ADD COLUMN is_recurring_instance BOOLEAN DEFAULT 0;  -- 1 = được tạo từ recurring

-- Foreign keys (nếu SQLite hỗ trợ - không thì bỏ qua)
-- FOREIGN KEY (parent_task_id) REFERENCES tasks(task_id)
-- FOREIGN KEY (template_id) REFERENCES task_templates(template_id)
-- FOREIGN KEY (recurrence_id) REFERENCES task_recurrence(recurrence_id)
```

---

## 2. TASK TEMPLATES FEATURE

### 2.1. Chức năng

**User stories:**
- Là user, tôi muốn tạo template cho các task lặp đi lặp lại (gọi khách, họp team, viết report...)
- Là user, tôi muốn dùng template có sẵn để tạo task nhanh chóng
- Là admin, tôi muốn tạo shared templates cho cả team

**Workflow:**
```
1. User vào trang "Task Templates"
2. Click "Tạo template mới"
3. Điền form:
   - Tên template
   - Title mặc định (có thể dùng biến: {customer_name}, {date}, {project_name})
   - Description mặc định
   - Category, Priority
   - Notification presets
   - Duration
   - Shared hay không
4. Save template
5. Khi tạo task mới:
   - User chọn "Từ template"
   - Chọn template
   - Form tự động điền sẵn
   - User có thể customize
   - Save task
```

### 2.2. UI Mockup

**Trang danh sách templates:**
```html
┌──────────────────────────────────────────────────────────────┐
│  📝 TASK TEMPLATES                      [+ Tạo template mới] │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  🔍 [Tìm kiếm template...]   [📁 Của tôi ▼]  [🏢 Shared ▼]  │
│                                                               │
│  ┌─ SHARED TEMPLATES ────────────────────────────────────┐   │
│  │                                                         │   │
│  │  📞 Gọi điện chào khách hàng mới                       │   │
│  │     Sales | High | Dùng: 45 lần                        │   │
│  │     [📋 Xem] [✏️ Sửa] [📑 Dùng template] [🗑️ Xóa]      │   │
│  │                                                         │   │
│  │  📧 Follow up sau 3 ngày                               │   │
│  │     Sales | Medium | Dùng: 32 lần                      │   │
│  │     [📋 Xem] [✏️ Sửa] [📑 Dùng template] [🗑️ Xóa]      │   │
│  │                                                         │   │
│  │  🏗️ Khảo sát công trình                               │   │
│  │     Project | High | Dùng: 18 lần                      │   │
│  │     [📋 Xem] [✏️ Sửa] [📑 Dùng template] [🗑️ Xóa]      │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌─ MY TEMPLATES ─────────────────────────────────────────┐   │
│  │                                                         │   │
│  │  ✅ Checklist công việc hàng ngày                      │   │
│  │     Personal | Medium | Dùng: 120 lần                  │   │
│  │     [📋 Xem] [✏️ Sửa] [📑 Dùng template] [🗑️ Xóa]      │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

**Form tạo/sửa template:**
```html
┌──────────────────────────────────────────────────────────────┐
│  📝 TẠO TASK TEMPLATE                          [💾 Lưu] [❌] │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Tên template: *                                             │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ Gọi điện chào khách hàng mới                         │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
│  Mô tả template:                                             │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ Template cho việc liên hệ khách hàng lần đầu        │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│                                                               │
│  📋 DEFAULT TASK VALUES                                      │
│                                                               │
│  Tiêu đề task: *                                             │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ Gọi điện cho {customer_name}                         │    │
│  └──────────────────────────────────────────────────────┘    │
│  💡 Biến khả dụng: {customer_name}, {date}, {time},         │
│     {project_name}, {user_name}                              │
│                                                               │
│  Mô tả task:                                                 │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ Liên hệ khách hàng để giới thiệu sản phẩm/dịch vụ.  │    │
│  │ Chuẩn bị:                                            │    │
│  │ - Tài liệu giới thiệu                                │    │
│  │ - Báo giá                                            │    │
│  │ - Case study                                         │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
│  Category: [Sales ▼]   Priority: [High ▼]                   │
│                                                               │
│  Thời lượng mặc định: [1] giờ                                │
│                                                               │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│                                                               │
│  🔔 NOTIFICATION PRESETS                                     │
│                                                               │
│  Notif 1: [-1] [hours ▼] (trước start_date)                 │
│           Label: [Nhắc trước 1 giờ]                          │
│                                                               │
│  Notif 2: [-10] [minutes ▼] (trước start_date)              │
│           Label: [Nhắc trước 10 phút]                        │
│                                                               │
│  [+ Thêm notification preset]                                │
│                                                               │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│                                                               │
│  ☑️ [✓] Shared template (cho phép mọi người dùng)           │
│                                                               │
│  [💾 Lưu template] [❌ Hủy]                                  │
└──────────────────────────────────────────────────────────────┘
```

**Form tạo task từ template:**
```html
┌──────────────────────────────────────────────────────────────┐
│  📑 TẠO TASK TỪ TEMPLATE                                     │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Chọn template: *                                            │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ 📞 Gọi điện chào khách hàng mới               [Chọn] │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
│  ━━━ Template sẽ tự động điền các trường bên dưới ━━━       │
│                                                               │
│  Tiêu đề: *                                                  │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ Gọi điện cho Nguyễn Văn A                            │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
│  Mô tả:                                                      │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ Liên hệ khách hàng để giới thiệu sản phẩm...        │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
│  Bắt đầu: [2025-11-02] [14:00]                              │
│  Kết thúc: [2025-11-02] [15:00]  (auto: +1 hour)            │
│  Deadline: [2025-11-02] [15:00]                              │
│                                                               │
│  Category: [Sales ▼]   Priority: [High ▼]                   │
│                                                               │
│  🔔 Thông báo (đã tự động tính):                             │
│  Notif 1: [2025-11-02 13:00] (Nhắc trước 1 giờ)             │
│  Notif 2: [2025-11-02 14:50] (Nhắc trước 10 phút)           │
│                                                               │
│  [✏️ Tùy chỉnh thông báo]                                    │
│                                                               │
│  [💾 Tạo task] [❌ Hủy]                                      │
└──────────────────────────────────────────────────────────────┘
```

### 2.3. Backend Logic - Template Manager

**File:** `backend/task_management/task_template_manager.py`

```python
# -*- coding: utf-8 -*-
"""
TASK TEMPLATE MANAGER
=====================

Quản lý task templates: CRUD operations

Functions:
- create_template(template_data) -> template_id
- get_template(template_id) -> dict
- get_all_templates(user_id, include_shared=True) -> list
- update_template(template_id, updates) -> bool
- delete_template(template_id) -> bool
- use_template(template_id, task_data) -> task_id
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

class TaskTemplateManager:
    def __init__(self, db):
        """
        Args:
            db: DatabaseManager instance
        """
        self.db = db

    def create_template(self, template_data: Dict[str, Any]) -> str:
        """
        Tạo task template mới

        Args:
            template_data: {
                'user_id': str,  # NULL nếu shared
                'template_name': str,
                'template_description': str,
                'default_title': str,
                'default_description': str,
                'default_category': str,
                'default_priority': str,
                'default_duration_hours': int,
                'notif1_offset': str,  # "-1 hour", "-3 days"
                'notif1_label': str,
                # ... notif2-8
                'is_shared': bool,
                'created_by': str
            }

        Returns:
            template_id: "tmpl_abc123"

        Algorithm:
            1. Validate required fields
            2. Generate template_id
            3. Insert into database
            4. Return template_id
        """
        try:
            # Validate
            if not template_data.get('template_name'):
                raise ValueError("template_name is required")
            if not template_data.get('default_title'):
                raise ValueError("default_title is required")

            # Generate ID
            template_id = f"tmpl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()

            # Prepare record
            record = {
                'template_id': template_id,
                'user_id': template_data.get('user_id'),
                'template_name': template_data['template_name'],
                'template_description': template_data.get('template_description', ''),
                'default_title': template_data['default_title'],
                'default_description': template_data.get('default_description', ''),
                'default_category': template_data.get('default_category', 'general'),
                'default_priority': template_data.get('default_priority', 'medium'),
                'default_duration_hours': template_data.get('default_duration_hours', 1),
                'is_shared': 1 if template_data.get('is_shared') else 0,
                'created_by': template_data.get('created_by'),
                'usage_count': 0,
                'created_at': now,
                'updated_at': now
            }

            # Add notification offsets
            for i in range(1, 9):
                record[f'notif{i}_offset'] = template_data.get(f'notif{i}_offset')
                record[f'notif{i}_label'] = template_data.get(f'notif{i}_label')

            # Insert
            with self.db.get_connection() as conn:
                columns = ', '.join(record.keys())
                placeholders = ', '.join(['?' for _ in record])
                query = f"INSERT INTO task_templates ({columns}) VALUES ({placeholders})"

                self.db.execute_insert(conn, query, tuple(record.values()))
                conn.commit()

            print(f"✅ Template created: {template_id}")
            return template_id

        except Exception as e:
            print(f"❌ Error creating template: {e}")
            raise

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin template

        Returns:
            dict hoặc None nếu không tìm thấy
        """
        try:
            with self.db.get_connection() as conn:
                query = "SELECT * FROM task_templates WHERE template_id = ?"
                results = self.db.execute_query(conn, query, (template_id,))

                if results:
                    return results[0]
                return None

        except Exception as e:
            print(f"❌ Error getting template: {e}")
            return None

    def get_all_templates(self, user_id: str = None, include_shared: bool = True) -> List[Dict[str, Any]]:
        """
        Lấy danh sách templates

        Args:
            user_id: Nếu cung cấp, lấy templates của user này
            include_shared: Có bao gồm shared templates không

        Returns:
            List of template dicts

        Algorithm:
            1. Build WHERE clause:
               - Nếu user_id: (user_id = ? OR is_shared = 1)
               - Nếu không: is_shared = 1
            2. Execute query
            3. Return results
        """
        try:
            with self.db.get_connection() as conn:
                conditions = []
                params = []

                if user_id:
                    if include_shared:
                        conditions.append("(user_id = ? OR is_shared = 1)")
                        params.append(user_id)
                    else:
                        conditions.append("user_id = ?")
                        params.append(user_id)
                else:
                    conditions.append("is_shared = 1")

                where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
                query = f"SELECT * FROM task_templates{where_clause} ORDER BY usage_count DESC, created_at DESC"

                results = self.db.execute_query(conn, query, tuple(params))
                return results

        except Exception as e:
            print(f"❌ Error getting templates: {e}")
            return []

    def update_template(self, template_id: str, updates: Dict[str, Any]) -> bool:
        """
        Cập nhật template

        Args:
            template_id: ID template
            updates: Dict các field cần update

        Returns:
            True nếu thành công
        """
        try:
            allowed_fields = [
                'template_name', 'template_description',
                'default_title', 'default_description',
                'default_category', 'default_priority', 'default_duration_hours',
                'is_shared'
            ]

            # Add notif fields
            for i in range(1, 9):
                allowed_fields.extend([f'notif{i}_offset', f'notif{i}_label'])

            set_strs = []
            params = []

            for field in allowed_fields:
                if field in updates:
                    set_strs.append(f"{field} = ?")
                    params.append(updates[field])

            if not set_strs:
                return False

            set_strs.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(template_id)

            with self.db.get_connection() as conn:
                query = f"UPDATE task_templates SET {', '.join(set_strs)} WHERE template_id = ?"
                self.db.execute_update(conn, query, tuple(params))
                conn.commit()

            print(f"✅ Template updated: {template_id}")
            return True

        except Exception as e:
            print(f"❌ Error updating template: {e}")
            return False

    def delete_template(self, template_id: str) -> bool:
        """Xóa template"""
        try:
            with self.db.get_connection() as conn:
                query = "DELETE FROM task_templates WHERE template_id = ?"
                self.db.execute_update(conn, query, (template_id,))
                conn.commit()

            print(f"✅ Template deleted: {template_id}")
            return True

        except Exception as e:
            print(f"❌ Error deleting template: {e}")
            return False

    def use_template(self, template_id: str, task_data: Dict[str, Any]) -> str:
        """
        Tạo task từ template

        Args:
            template_id: ID template
            task_data: {
                'user_id': str,
                'start_date': str,  # "2025-11-02T14:00"
                'variables': {      # Biến để replace trong template
                    'customer_name': 'Nguyễn Văn A',
                    'project_name': 'Villa Thảo Điền',
                    ...
                },
                # Optional overrides:
                'title': str,       # Nếu muốn override default_title
                'description': str,
                'category': str,
                'priority': str
            }

        Returns:
            task_id của task mới tạo

        Algorithm:
            1. Load template
            2. Replace variables trong title/description
            3. Calculate notification times từ offsets
            4. Create task using SimpleTaskManager
            5. Update template usage_count
            6. Return task_id
        """
        try:
            # Load template
            template = self.get_template(template_id)
            if not template:
                raise ValueError(f"Template not found: {template_id}")

            # Parse start_date
            start_date = datetime.strptime(task_data['start_date'], '%Y-%m-%dT%H:%M')

            # Replace variables
            variables = task_data.get('variables', {})
            title = task_data.get('title') or template['default_title']
            description = task_data.get('description') or template['default_description']

            for var_name, var_value in variables.items():
                title = title.replace(f"{{{var_name}}}", str(var_value))
                description = description.replace(f"{{{var_name}}}", str(var_value))

            # Calculate end_date
            duration_hours = template['default_duration_hours'] or 1
            end_date = start_date + timedelta(hours=duration_hours)

            # Calculate notification times
            notifications = {}
            for i in range(1, 9):
                offset_str = template.get(f'notif{i}_offset')
                if offset_str:
                    notif_time = self._calculate_notification_time(start_date, offset_str)
                    if notif_time:
                        notifications[f'notif{i}'] = notif_time.strftime('%Y-%m-%dT%H:%M')

            # Prepare task data
            new_task_data = {
                'user_id': task_data['user_id'],
                'title': title,
                'description': description,
                'start_date': start_date.strftime('%Y-%m-%d %H:%M'),
                'end_date': end_date.strftime('%Y-%m-%d %H:%M'),
                'deadline': end_date.strftime('%Y-%m-%d %H:%M'),
                'category': task_data.get('category') or template['default_category'],
                'priority': task_data.get('priority') or template['default_priority'],
                'template_id': template_id,  # Link back to template
                **notifications
            }

            # Create task
            from task_management.simple_task_manager import SimpleTaskManager
            task_manager = SimpleTaskManager(self.db)
            task_id = task_manager.create_task(new_task_data)

            # Update usage count
            with self.db.get_connection() as conn:
                query = "UPDATE task_templates SET usage_count = usage_count + 1 WHERE template_id = ?"
                self.db.execute_update(conn, query, (template_id,))
                conn.commit()

            print(f"✅ Task created from template: {task_id}")
            return task_id

        except Exception as e:
            print(f"❌ Error using template: {e}")
            raise

    def _calculate_notification_time(self, base_time: datetime, offset_str: str) -> Optional[datetime]:
        """
        Tính notification time từ offset

        Args:
            base_time: Thời gian gốc (start_date)
            offset_str: "-1 hour", "-3 days", "-30 minutes"

        Returns:
            datetime hoặc None

        Examples:
            _calculate_notification_time(2025-11-02 14:00, "-1 hour")
            → 2025-11-02 13:00

            _calculate_notification_time(2025-11-02 14:00, "-3 days")
            → 2025-10-30 14:00
        """
        try:
            parts = offset_str.strip().split()
            if len(parts) != 2:
                return None

            value = int(parts[0])  # Có thể âm
            unit = parts[1].lower()

            if unit in ['hour', 'hours']:
                return base_time + timedelta(hours=value)
            elif unit in ['minute', 'minutes']:
                return base_time + timedelta(minutes=value)
            elif unit in ['day', 'days']:
                return base_time + timedelta(days=value)
            else:
                return None

        except Exception as e:
            print(f"⚠️  Error calculating notification time: {e}")
            return None


# Test function
def test_task_template_manager():
    """Test TaskTemplateManager"""
    from core.database_manager import DatabaseManager

    db = DatabaseManager("test_templates.db")
    manager = TaskTemplateManager(db)

    # Test create
    template_data = {
        'user_id': None,  # Shared
        'template_name': 'Test Template',
        'default_title': 'Call {customer_name}',
        'default_description': 'Contact customer about {project_name}',
        'default_category': 'sales',
        'default_priority': 'high',
        'default_duration_hours': 1,
        'notif1_offset': '-1 hour',
        'notif1_label': 'Nhắc trước 1 giờ',
        'notif2_offset': '-10 minutes',
        'notif2_label': 'Nhắc trước 10 phút',
        'is_shared': True,
        'created_by': 'admin'
    }

    template_id = manager.create_template(template_data)
    print(f"✅ Created template: {template_id}")

    # Test get
    template = manager.get_template(template_id)
    print(f"✅ Got template: {template['template_name']}")

    # Test use
    task_data = {
        'user_id': 'user_123',
        'start_date': '2025-11-02T14:00',
        'variables': {
            'customer_name': 'Nguyễn Văn A',
            'project_name': 'Villa Thảo Điền'
        }
    }

    task_id = manager.use_template(template_id, task_data)
    print(f"✅ Created task from template: {task_id}")

    # Cleanup
    import os
    os.remove("test_templates.db")
    print("✅ Test passed!")

if __name__ == "__main__":
    test_task_template_manager()
```

---

## 3. RECURRING TASKS FEATURE

### 3.1. Chức năng

**User stories:**
- Là user, tôi muốn tạo task lặp lại hàng ngày/tuần/tháng
- Là user, tôi muốn set thời gian kết thúc cho recurring task
- Hệ thống tự động tạo tasks theo lịch

**Workflow:**
```
1. User tạo task thông thường
2. Check "Lặp lại task"
3. Chọn pattern:
   - Hàng ngày
   - Hàng tuần (chọn các ngày: T2, T4, T6...)
   - Hàng tháng (ngày 15 hàng tháng)
   - Custom
4. Set thời gian kết thúc:
   - Không bao giờ
   - Sau X lần
   - Đến ngày DD/MM/YYYY
5. Save task
6. Hệ thống:
   - Tạo task gốc (parent_task)
   - Tạo recurrence config
   - Background job tự động generate tasks mới theo lịch
```

### 3.2. UI Mockup

**Form tạo recurring task:**
```html
┌──────────────────────────────────────────────────────────────┐
│  📋 TẠO TASK                                                 │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Tiêu đề: *                                                  │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ Họp team standup                                     │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
│  Mô tả:                                                      │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ Daily standup meeting với team                       │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
│  Bắt đầu: [2025-11-04] [09:00]                              │
│  Kết thúc: [2025-11-04] [09:30]                              │
│                                                               │
│  Category: [Meeting ▼]   Priority: [Medium ▼]               │
│                                                               │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│                                                               │
│  ☑️ [✓] Lặp lại task                                         │
│                                                               │
│  ┌─ THIẾT LẬP LẶP LẠI ─────────────────────────────────┐    │
│  │                                                       │    │
│  │  Tần suất:                                           │    │
│  │  ○ Hàng ngày                                         │    │
│  │  ● Hàng tuần                                         │    │
│  │  ○ Hàng tháng                                        │    │
│  │  ○ Tùy chỉnh                                         │    │
│  │                                                       │    │
│  │  Lặp vào các ngày: (Với tần suất "Hàng tuần")       │    │
│  │  [✓] Thứ 2   [✓] Thứ 3   [✓] Thứ 4                  │    │
│  │  [✓] Thứ 5   [✓] Thứ 6   [ ] Thứ 7   [ ] CN         │    │
│  │                                                       │    │
│  │  Kết thúc:                                           │    │
│  │  ○ Không bao giờ                                     │    │
│  │  ○ Sau [__] lần                                      │    │
│  │  ● Vào ngày: [2025-12-31]                           │    │
│  │                                                       │    │
│  └───────────────────────────────────────────────────────┘    │
│                                                               │
│  💡 Xem trước: Task sẽ được tạo tự động vào các ngày:        │
│     • Thứ 2, 04/11/2025 09:00                                │
│     • Thứ 3, 05/11/2025 09:00                                │
│     • Thứ 4, 06/11/2025 09:00                                │
│     • Thứ 5, 07/11/2025 09:00                                │
│     • Thứ 6, 08/11/2025 09:00                                │
│     ... (đến 31/12/2025)                                     │
│                                                               │
│  [💾 Tạo task] [❌ Hủy]                                      │
└──────────────────────────────────────────────────────────────┘
```

**Quản lý recurring tasks:**
```html
┌──────────────────────────────────────────────────────────────┐
│  🔄 RECURRING TASKS                                          │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ 🟢 Họp team standup                                  │    │
│  │    📅 Hàng tuần: T2, T3, T4, T5, T6                  │    │
│  │    ⏰ 09:00 - 09:30                                  │    │
│  │    📊 Đã tạo: 45/60 tasks                            │    │
│  │    📅 Tiếp theo: Thứ 2, 04/11/2025 09:00             │    │
│  │    🏁 Kết thúc: 31/12/2025                           │    │
│  │                                                       │    │
│  │    [⏸️ Tạm dừng] [✏️ Sửa] [🗑️ Xóa] [📋 Xem tasks]    │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ 🟢 Viết báo cáo tuần                                 │    │
│  │    📅 Hàng tuần: Thứ 6                               │    │
│  │    ⏰ 16:00 - 17:00                                  │    │
│  │    📊 Đã tạo: 8/∞ tasks                              │    │
│  │    📅 Tiếp theo: Thứ 6, 08/11/2025 16:00             │    │
│  │    🏁 Không kết thúc                                 │    │
│  │                                                       │    │
│  │    [⏸️ Tạm dừng] [✏️ Sửa] [🗑️ Xóa] [📋 Xem tasks]    │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ ⏸️ Checkin dự án hàng tháng                          │    │
│  │    📅 Hàng tháng: Ngày 1                             │    │
│  │    ⏰ 10:00 - 11:00                                  │    │
│  │    📊 Đã tạo: 3/12 tasks                             │    │
│  │    ⏸️ TẠM DỪNG                                        │    │
│  │                                                       │    │
│  │    [▶️ Tiếp tục] [✏️ Sửa] [🗑️ Xóa] [📋 Xem tasks]    │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

### 3.3. Backend Logic - Recurring Task Manager

**File:** `backend/task_management/recurring_task_manager.py`

```python
# -*- coding: utf-8 -*-
"""
RECURRING TASK MANAGER
======================

Quản lý recurring tasks (tasks lặp lại theo lịch)

Functions:
- create_recurrence(task_id, recurrence_config) -> recurrence_id
- get_recurrence(recurrence_id) -> dict
- update_recurrence(recurrence_id, updates) -> bool
- pause_recurrence(recurrence_id) -> bool
- resume_recurrence(recurrence_id) -> bool
- delete_recurrence(recurrence_id) -> bool
- generate_next_occurrence(recurrence_id) -> task_id
- process_due_recurrences() -> int (số tasks được tạo)
"""

import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

class RecurringTaskManager:
    def __init__(self, db):
        self.db = db

    def create_recurrence(self, task_id: str, recurrence_config: Dict[str, Any]) -> str:
        """
        Tạo recurrence config cho task

        Args:
            task_id: ID của parent task
            recurrence_config: {
                'user_id': str,
                'frequency': str,  # daily/weekly/monthly/custom
                'interval': int,   # 1 = mỗi ngày, 2 = mỗi 2 ngày
                'weekdays': list,  # ["monday", "wednesday", "friday"]
                'day_of_month': int,  # 15 = ngày 15
                'start_date': str,
                'end_date': str,   # NULL = vô hạn
                'max_occurrences': int  # NULL = vô hạn
            }

        Returns:
            recurrence_id

        Algorithm:
            1. Validate config
            2. Calculate next_occurrence_date
            3. Insert into task_recurrence
            4. Update parent task
            5. Return recurrence_id
        """
        try:
            # Validate
            if not recurrence_config.get('frequency'):
                raise ValueError("frequency is required")
            if not recurrence_config.get('start_date'):
                raise ValueError("start_date is required")

            # Generate ID
            recurrence_id = f"recur_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()

            # Calculate next occurrence
            start_date = datetime.fromisoformat(recurrence_config['start_date'])
            next_occurrence = self._calculate_next_occurrence(
                start_date,
                recurrence_config['frequency'],
                recurrence_config.get('interval', 1),
                recurrence_config.get('weekdays'),
                recurrence_config.get('day_of_month')
            )

            # Prepare record
            record = {
                'recurrence_id': recurrence_id,
                'parent_task_id': task_id,
                'user_id': recurrence_config.get('user_id'),
                'frequency': recurrence_config['frequency'],
                'interval': recurrence_config.get('interval', 1),
                'weekdays': json.dumps(recurrence_config.get('weekdays')) if recurrence_config.get('weekdays') else None,
                'day_of_month': recurrence_config.get('day_of_month'),
                'week_of_month': recurrence_config.get('week_of_month'),
                'day_of_week': recurrence_config.get('day_of_week'),
                'custom_pattern': recurrence_config.get('custom_pattern'),
                'start_date': recurrence_config['start_date'],
                'end_date': recurrence_config.get('end_date'),
                'max_occurrences': recurrence_config.get('max_occurrences'),
                'last_generated_date': None,
                'next_occurrence_date': next_occurrence.isoformat() if next_occurrence else None,
                'occurrences_count': 0,
                'is_active': 1,
                'created_at': now,
                'updated_at': now
            }

            # Insert
            with self.db.get_connection() as conn:
                columns = ', '.join(record.keys())
                placeholders = ', '.join(['?' for _ in record])
                query = f"INSERT INTO task_recurrence ({columns}) VALUES ({placeholders})"

                self.db.execute_insert(conn, query, tuple(record.values()))

                # Update parent task
                update_query = """
                    UPDATE tasks
                    SET recurrence_id = ?, is_recurring_instance = 0
                    WHERE task_id = ?
                """
                self.db.execute_update(conn, update_query, (recurrence_id, task_id))

                conn.commit()

            print(f"✅ Recurrence created: {recurrence_id}")
            return recurrence_id

        except Exception as e:
            print(f"❌ Error creating recurrence: {e}")
            raise

    def _calculate_next_occurrence(
        self,
        current_date: datetime,
        frequency: str,
        interval: int,
        weekdays: List[str] = None,
        day_of_month: int = None
    ) -> Optional[datetime]:
        """
        Tính ngày occurrence tiếp theo

        Args:
            current_date: Ngày hiện tại
            frequency: daily/weekly/monthly
            interval: Khoảng cách (1, 2, 3...)
            weekdays: ["monday", "friday"] cho weekly
            day_of_month: 15 cho monthly

        Returns:
            Next occurrence datetime

        Algorithm for weekly:
            1. Lấy ngày hiện tại
            2. Tìm ngày trong tuần tiếp theo trong weekdays
            3. Nếu không có, chuyển sang tuần sau

        Examples:
            - Hàng tuần T2,T4,T6, hiện tại là T3
              → Trả về T4 tuần này

            - Hàng tuần T2,T4,T6, hiện tại là T6
              → Trả về T2 tuần sau

            - Hàng tháng ngày 15, hiện tại là ngày 10
              → Trả về ngày 15 tháng này

            - Hàng tháng ngày 15, hiện tại là ngày 20
              → Trả về ngày 15 tháng sau
        """
        try:
            if frequency == 'daily':
                return current_date + timedelta(days=interval)

            elif frequency == 'weekly':
                if not weekdays:
                    # Default to same day of week
                    return current_date + timedelta(weeks=interval)

                # Map weekdays
                weekday_map = {
                    'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                    'friday': 4, 'saturday': 5, 'sunday': 6
                }
                target_weekdays = sorted([weekday_map[d] for d in weekdays])
                current_weekday = current_date.weekday()

                # Find next weekday in current week
                for target in target_weekdays:
                    if target > current_weekday:
                        days_ahead = target - current_weekday
                        return current_date + timedelta(days=days_ahead)

                # No more occurrences this week, go to next week
                first_target = target_weekdays[0]
                days_ahead = (7 - current_weekday) + first_target
                return current_date + timedelta(days=days_ahead)

            elif frequency == 'monthly':
                if not day_of_month:
                    # Same day next month
                    next_month = current_date.month + interval
                    next_year = current_date.year
                    while next_month > 12:
                        next_month -= 12
                        next_year += 1
                    return current_date.replace(year=next_year, month=next_month)

                # Specific day of month
                if current_date.day < day_of_month:
                    # Same month
                    return current_date.replace(day=day_of_month)
                else:
                    # Next month
                    next_month = current_date.month + interval
                    next_year = current_date.year
                    while next_month > 12:
                        next_month -= 12
                        next_year += 1
                    return current_date.replace(year=next_year, month=next_month, day=day_of_month)

            return None

        except Exception as e:
            print(f"⚠️  Error calculating next occurrence: {e}")
            return None

    def generate_next_occurrence(self, recurrence_id: str) -> Optional[str]:
        """
        Generate task tiếp theo từ recurrence

        Returns:
            task_id của task mới, hoặc None nếu hết recurrence

        Algorithm:
            1. Load recurrence config
            2. Check xem còn tạo được không (max_occurrences, end_date)
            3. Load parent task
            4. Tạo task mới với dates mới
            5. Update recurrence (last_generated, next_occurrence, count)
            6. Return task_id
        """
        try:
            # Load recurrence
            recurrence = self.get_recurrence(recurrence_id)
            if not recurrence or not recurrence['is_active']:
                return None

            # Check limits
            if recurrence['max_occurrences']:
                if recurrence['occurrences_count'] >= recurrence['max_occurrences']:
                    print(f"⚠️  Max occurrences reached for {recurrence_id}")
                    return None

            if recurrence['end_date']:
                end_date = datetime.fromisoformat(recurrence['end_date'])
                next_occ = datetime.fromisoformat(recurrence['next_occurrence_date'])
                if next_occ > end_date:
                    print(f"⚠️  End date reached for {recurrence_id}")
                    return None

            # Load parent task
            with self.db.get_connection() as conn:
                query = "SELECT * FROM tasks WHERE task_id = ?"
                results = self.db.execute_query(conn, query, (recurrence['parent_task_id'],))
                if not results:
                    raise ValueError(f"Parent task not found: {recurrence['parent_task_id']}")
                parent_task = results[0]

            # Calculate new dates
            occurrence_date = datetime.fromisoformat(recurrence['next_occurrence_date'])
            parent_start = datetime.fromisoformat(parent_task['start_date'])
            parent_end = datetime.fromisoformat(parent_task['end_date'])
            duration = parent_end - parent_start

            new_start = occurrence_date
            new_end = new_start + duration

            # Create new task
            from task_management.simple_task_manager import SimpleTaskManager
            task_manager = SimpleTaskManager(self.db)

            new_task_data = {
                'user_id': parent_task['user_id'],
                'title': parent_task['title'],
                'description': parent_task['description'],
                'start_date': new_start.strftime('%Y-%m-%d %H:%M'),
                'end_date': new_end.strftime('%Y-%m-%d %H:%M'),
                'deadline': new_end.strftime('%Y-%m-%d %H:%M'),
                'category': parent_task['category'],
                'priority': parent_task['priority'],
                'parent_task_id': recurrence['parent_task_id'],
                'recurrence_id': recurrence_id,
                'is_recurring_instance': 1
            }

            # Copy notification offsets
            for i in range(1, 9):
                notif_col = f'notif{i}'
                if parent_task.get(notif_col):
                    new_task_data[notif_col] = parent_task[notif_col]

            new_task_id = task_manager.create_task(new_task_data)

            # Calculate next occurrence
            weekdays_str = recurrence.get('weekdays')
            weekdays = json.loads(weekdays_str) if weekdays_str else None

            next_next_occurrence = self._calculate_next_occurrence(
                occurrence_date,
                recurrence['frequency'],
                recurrence['interval'],
                weekdays,
                recurrence.get('day_of_month')
            )

            # Update recurrence
            with self.db.get_connection() as conn:
                update_query = """
                    UPDATE task_recurrence
                    SET last_generated_date = ?,
                        next_occurrence_date = ?,
                        occurrences_count = occurrences_count + 1,
                        updated_at = ?
                    WHERE recurrence_id = ?
                """
                self.db.execute_update(conn, update_query, (
                    occurrence_date.isoformat(),
                    next_next_occurrence.isoformat() if next_next_occurrence else None,
                    datetime.now().isoformat(),
                    recurrence_id
                ))
                conn.commit()

            print(f"✅ Generated occurrence: {new_task_id}")
            return new_task_id

        except Exception as e:
            print(f"❌ Error generating occurrence: {e}")
            return None

    def process_due_recurrences(self) -> int:
        """
        Process tất cả recurrences đến hạn

        Chạy bởi background job/cron

        Returns:
            Số tasks được tạo

        Algorithm:
            1. Query tất cả active recurrences có next_occurrence_date <= now
            2. Với mỗi recurrence:
               - Generate next occurrence
            3. Return count
        """
        try:
            now = datetime.now().isoformat()
            count = 0

            with self.db.get_connection() as conn:
                query = """
                    SELECT recurrence_id
                    FROM task_recurrence
                    WHERE is_active = 1
                    AND next_occurrence_date IS NOT NULL
                    AND next_occurrence_date <= ?
                """
                results = self.db.execute_query(conn, query, (now,))

            for row in results:
                recurrence_id = row['recurrence_id']
                task_id = self.generate_next_occurrence(recurrence_id)
                if task_id:
                    count += 1

            if count > 0:
                print(f"✅ Processed {count} recurring tasks")

            return count

        except Exception as e:
            print(f"❌ Error processing recurrences: {e}")
            return 0

    def get_recurrence(self, recurrence_id: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin recurrence"""
        try:
            with self.db.get_connection() as conn:
                query = "SELECT * FROM task_recurrence WHERE recurrence_id = ?"
                results = self.db.execute_query(conn, query, (recurrence_id,))
                return results[0] if results else None
        except Exception as e:
            print(f"❌ Error getting recurrence: {e}")
            return None

    def pause_recurrence(self, recurrence_id: str) -> bool:
        """Tạm dừng recurrence"""
        try:
            with self.db.get_connection() as conn:
                query = "UPDATE task_recurrence SET is_active = 0, updated_at = ? WHERE recurrence_id = ?"
                self.db.execute_update(conn, query, (datetime.now().isoformat(), recurrence_id))
                conn.commit()
            print(f"✅ Recurrence paused: {recurrence_id}")
            return True
        except Exception as e:
            print(f"❌ Error pausing recurrence: {e}")
            return False

    def resume_recurrence(self, recurrence_id: str) -> bool:
        """Tiếp tục recurrence"""
        try:
            with self.db.get_connection() as conn:
                query = "UPDATE task_recurrence SET is_active = 1, updated_at = ? WHERE recurrence_id = ?"
                self.db.execute_update(conn, query, (datetime.now().isoformat(), recurrence_id))
                conn.commit()
            print(f"✅ Recurrence resumed: {recurrence_id}")
            return True
        except Exception as e:
            print(f"❌ Error resuming recurrence: {e}")
            return False

    def delete_recurrence(self, recurrence_id: str, delete_instances: bool = False) -> bool:
        """
        Xóa recurrence

        Args:
            recurrence_id: ID recurrence
            delete_instances: Có xóa cả các tasks đã tạo không
        """
        try:
            with self.db.get_connection() as conn:
                if delete_instances:
                    # Xóa tất cả tasks được tạo từ recurrence này
                    delete_tasks_query = "DELETE FROM tasks WHERE recurrence_id = ? AND is_recurring_instance = 1"
                    self.db.execute_update(conn, delete_tasks_query, (recurrence_id,))

                # Xóa recurrence
                query = "DELETE FROM task_recurrence WHERE recurrence_id = ?"
                self.db.execute_update(conn, query, (recurrence_id,))
                conn.commit()

            print(f"✅ Recurrence deleted: {recurrence_id}")
            return True
        except Exception as e:
            print(f"❌ Error deleting recurrence: {e}")
            return False


# Background job script
def run_recurrence_processor():
    """
    Script để chạy định kỳ (cron job)

    Cách dùng:
        # Thêm vào crontab chạy mỗi 1 giờ:
        0 * * * * cd /path/to/project && python3 backend/task_management/recurring_task_manager.py
    """
    from core.database_manager import DatabaseManager

    db = DatabaseManager("database/calendar_tools.db")
    manager = RecurringTaskManager(db)

    print(f"[{datetime.now()}] Running recurrence processor...")
    count = manager.process_due_recurrences()
    print(f"[{datetime.now()}] Completed. Created {count} tasks.")

if __name__ == "__main__":
    run_recurrence_processor()
```

---

## 4. TASK DEPENDENCIES FEATURE

### 4.1. Chức năng

**User stories:**
- Là user, tôi muốn set task B phụ thuộc vào task A (B chỉ bắt đầu sau khi A hoàn thành)
- Là user, tôi muốn thấy visual dependency chain
- Hệ thống cảnh báo khi task bị block

**Workflow:**
```
1. User tạo/edit task B
2. Thêm dependency: "Task này phụ thuộc vào..."
3. Chọn task A từ danh sách
4. Save
5. Hiển thị:
   - Task A: "🔒 Task này đang block 3 tasks khác"
   - Task B: "⏳ Chờ hoàn thành: Task A"
6. Khi task A completed → Notification cho owner của task B
```

### 4.2. UI Mockup

**Thêm dependency trong task detail:**
```html
┌──────────────────────────────────────────────────────────────┐
│  📋 TASK: Thiết kế hệ thống Smart Home                       │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ... (các field khác) ...                                    │
│                                                               │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│                                                               │
│  🔗 DEPENDENCIES                                             │
│                                                               │
│  Task này phụ thuộc vào:                                     │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ ✅ Khảo sát công trình Villa Thảo Điền               │    │
│  │    Status: Completed ✓                                │    │
│  │    [🗑️ Xóa dependency]                                │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
│  [+ Thêm dependency]                                         │
│                                                               │
│  Task này đang block:                                        │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ ⏳ Báo giá dự án Villa Thảo Điền                      │    │
│  │    Status: Pending (chờ task này hoàn thành)         │    │
│  │    [👁️ Xem task]                                      │    │
│  ├──────────────────────────────────────────────────────┤    │
│  │ ⏳ Lên lịch thi công                                  │    │
│  │    Status: Pending                                    │    │
│  │    [👁️ Xem task]                                      │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
│  ⚠️ Lưu ý: Hoàn thành task này sẽ mở khóa 2 tasks khác      │
└──────────────────────────────────────────────────────────────┘
```

**Modal thêm dependency:**
```html
┌──────────────────────────────────────────────────────────────┐
│  🔗 THÊM DEPENDENCY                                  [❌ Đóng]│
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Task hiện tại: "Thiết kế hệ thống Smart Home"               │
│                                                               │
│  Chọn task phụ thuộc: *                                      │
│  (Task hiện tại sẽ chỉ bắt đầu sau khi task được chọn        │
│   hoàn thành)                                                 │
│                                                               │
│  🔍 [Tìm kiếm task...]                                       │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ ○ Khảo sát công trình Villa Thảo Điền                │    │
│  │   Project | High | Pending                            │    │
│  │   Deadline: 05/11/2025                                │    │
│  ├──────────────────────────────────────────────────────┤    │
│  │ ○ Họp kick-off dự án                                 │    │
│  │   Meeting | Medium | Completed ✓                      │    │
│  ├──────────────────────────────────────────────────────┤    │
│  │ ○ Thu thập yêu cầu khách hàng                        │    │
│  │   Sales | High | Completed ✓                          │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
│  [💾 Thêm dependency] [❌ Hủy]                               │
└──────────────────────────────────────────────────────────────┘
```

(Tiếp tục phần 2...)

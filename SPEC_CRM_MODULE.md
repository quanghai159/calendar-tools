# SPEC: CRM MODULE - QUẢN LÝ KHÁCH HÀNG

> **Mục đích:** Xây dựng module CRM hoàn chỉnh để quản lý khách hàng, tương tác, kịch bản chăm sóc, báo giá
>
> **Codebase hiện tại:** Python/Flask + SQLite
>
> **Integration:** Liên kết chặt chẽ với Tasks Module

---

## 📋 MỤC LỤC

1. [Database Schema](#1-database-schema)
2. [Customer Management](#2-customer-management)
3. [Customer Interactions](#3-customer-interactions)
4. [Care Scenarios & Automation](#4-care-scenarios--automation)
5. [Message Templates](#5-message-templates)
6. [Quotations](#6-quotations)
7. [Backend Implementation](#7-backend-implementation)
8. [Frontend Implementation](#8-frontend-implementation)
9. [API Endpoints](#9-api-endpoints)
10. [CRM ↔ Tasks Integration](#10-crm--tasks-integration)
11. [Migration Scripts](#11-migration-scripts)

---

## 1. DATABASE SCHEMA

### 1.1. Core Tables

#### A. `customers` - Khách hàng

```sql
CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,               -- "cust_abc123"
    user_id TEXT,                               -- Sales phụ trách

    -- Thông tin cơ bản
    full_name TEXT NOT NULL,
    phone_number TEXT,
    email TEXT,
    company_name TEXT,
    tax_code TEXT,                              -- Mã số thuế

    -- Địa chỉ & vị trí
    address TEXT,
    city TEXT,
    district TEXT,
    ward TEXT,
    google_maps_url TEXT,
    latitude REAL,
    longitude REAL,

    -- Phân loại
    customer_type TEXT DEFAULT 'individual',    -- individual/business/dealer/distributor
    lead_source TEXT,                           -- facebook/zalo/website/referral/exhibition/other
    lead_status TEXT DEFAULT 'new',             -- new/contacted/qualified/proposal/negotiation/won/lost/archived
    priority_level TEXT DEFAULT 'cold',         -- hot/warm/cold

    -- Thông tin kinh doanh
    industry TEXT,                              -- Lĩnh vực: hotel/villa/apartment/office/retail
    project_scale TEXT,                         -- small/medium/large
    estimated_budget REAL,
    expected_close_date TEXT,

    -- Tracking
    assigned_to TEXT,                           -- User phụ trách
    last_contact_date TEXT,
    next_follow_up_date TEXT,
    total_interactions INTEGER DEFAULT 0,
    total_revenue REAL DEFAULT 0,
    total_orders INTEGER DEFAULT 0,

    -- Social & Contact
    facebook_url TEXT,
    zalo_id TEXT,
    telegram_id TEXT,
    website TEXT,

    -- Tags & notes
    tags TEXT,                                  -- JSON array: ["vip", "fast_decision", "price_sensitive"]
    notes TEXT,                                 -- Ghi chú chung

    -- Metadata
    created_at TEXT,
    updated_at TEXT,
    created_by TEXT,

    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (assigned_to) REFERENCES users(user_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

-- Indexes
CREATE INDEX idx_customers_user ON customers(user_id);
CREATE INDEX idx_customers_assigned ON customers(assigned_to);
CREATE INDEX idx_customers_lead_status ON customers(lead_status);
CREATE INDEX idx_customers_priority ON customers(priority_level);
CREATE INDEX idx_customers_phone ON customers(phone_number);
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_next_follow_up ON customers(next_follow_up_date);

-- Full-text search (nếu SQLite hỗ trợ FTS)
-- CREATE VIRTUAL TABLE customers_fts USING fts5(customer_id, full_name, phone_number, email, company_name);
```

**Sample Data:**
```sql
INSERT INTO customers VALUES (
    'cust_001',
    'user_123',
    'Nguyễn Văn A',
    '0909123456',
    'nguyenvana@email.com',
    'Công ty ABC',
    '0123456789',
    '123 Đường XYZ, Phường 1',
    'TP. Hồ Chí Minh',
    'Quận 2',
    'Phường Thảo Điền',
    'https://maps.google.com/?q=10.123,106.456',
    10.123,
    106.456,
    'business',
    'website',
    'qualified',
    'hot',
    'villa',
    'large',
    2500000000,  -- 2.5 tỷ
    '2025-12-31',
    'user_123',
    '2025-11-01 14:30:00',
    '2025-11-05 14:00:00',
    5,  -- 5 interactions
    0,  -- chưa có doanh thu
    0,  -- chưa có orders
    'https://facebook.com/nguyenvana',
    '0909123456',
    NULL,
    'https://company-abc.com',
    '["vip", "fast_decision"]',
    'Khách hàng tiềm năng cao, đã làm việc với nhiều nhà thầu, quyết định nhanh',
    '2025-10-15 10:00:00',
    '2025-11-01 14:30:00',
    'user_admin'
);
```

---

#### B. `customer_interactions` - Lịch sử tương tác

```sql
CREATE TABLE customer_interactions (
    interaction_id TEXT PRIMARY KEY,            -- "int_abc123"
    customer_id TEXT NOT NULL,
    user_id TEXT NOT NULL,                      -- Người tương tác

    interaction_type TEXT NOT NULL,             -- call/email/meeting/zalo/telegram/visit/other
    direction TEXT DEFAULT 'outbound',          -- inbound/outbound

    subject TEXT,
    content TEXT,                               -- Nội dung tương tác
    outcome TEXT,                               -- interested/not_interested/callback/need_more_info/closed/no_answer

    next_action TEXT,                           -- Hành động tiếp theo cần làm
    next_action_date TEXT,

    -- Link to other entities
    related_task_id TEXT,                       -- Task được tạo từ interaction này
    related_quotation_id TEXT,                  -- Báo giá liên quan

    -- Attachments
    attachments TEXT,                           -- JSON array of file paths

    -- Duration (for calls/meetings)
    duration_minutes INTEGER,

    interaction_date TEXT NOT NULL,
    created_at TEXT,

    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (related_task_id) REFERENCES tasks(task_id),
    FOREIGN KEY (related_quotation_id) REFERENCES quotations(quotation_id)
);

-- Indexes
CREATE INDEX idx_interactions_customer ON customer_interactions(customer_id);
CREATE INDEX idx_interactions_user ON customer_interactions(user_id);
CREATE INDEX idx_interactions_date ON customer_interactions(interaction_date);
CREATE INDEX idx_interactions_type ON customer_interactions(interaction_type);
```

**Sample Data:**
```sql
INSERT INTO customer_interactions VALUES (
    'int_001',
    'cust_001',
    'user_123',
    'call',
    'outbound',
    'Gọi điện tư vấn gói Smart Lighting',
    'Đã giới thiệu sản phẩm, khách hàng quan tâm đến tính năng điều khiển từ xa và tích hợp AI. Yêu cầu xem demo.',
    'interested',
    'Hẹn lịch demo tại văn phòng khách hàng',
    '2025-11-05 14:00:00',
    NULL,  -- chưa tạo task
    NULL,  -- chưa có quotation
    NULL,  -- no attachments
    30,  -- 30 minutes
    '2025-11-01 14:30:00',
    '2025-11-01 15:00:00'
);
```

---

#### C. `customer_care_scenarios` - Kịch bản chăm sóc

```sql
CREATE TABLE customer_care_scenarios (
    scenario_id TEXT PRIMARY KEY,               -- "scenario_abc123"
    scenario_name TEXT NOT NULL,
    scenario_description TEXT,

    customer_segment TEXT,                      -- new_lead/warm_lead/hot_lead/existing_customer/lost_customer
    trigger_event TEXT,                         -- customer_created/first_contact/no_response_3days/won_deal

    is_active BOOLEAN DEFAULT 1,
    created_by TEXT,
    created_at TEXT,
    updated_at TEXT,

    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

CREATE INDEX idx_scenarios_segment ON customer_care_scenarios(customer_segment);
CREATE INDEX idx_scenarios_active ON customer_care_scenarios(is_active);
```

**Sample Data:**
```sql
INSERT INTO customer_care_scenarios VALUES (
    'scenario_001',
    'Lead mới từ Facebook',
    'Kịch bản tự động chăm sóc lead mới từ Facebook: Gửi Zalo chào mừng, gọi điện trong 2h, follow up sau 3 ngày',
    'new_lead',
    'customer_created',
    1,
    'admin',
    '2025-11-01 10:00:00',
    '2025-11-01 10:00:00'
);
```

---

#### D. `scenario_steps` - Các bước trong kịch bản

```sql
CREATE TABLE scenario_steps (
    step_id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    step_order INTEGER NOT NULL,

    step_name TEXT NOT NULL,
    step_description TEXT,

    step_type TEXT NOT NULL,                    -- auto_task/auto_notification/auto_message/manual_action

    -- Timing
    delay_days INTEGER DEFAULT 0,
    delay_hours INTEGER DEFAULT 0,
    delay_from TEXT DEFAULT 'previous_step',    -- scenario_start/previous_step/customer_created

    -- Action details
    action_type TEXT,                           -- call/email/zalo/telegram/sms/visit
    template_id TEXT,                           -- Link to message template (nếu auto_message)
    task_template_id TEXT,                      -- Link to task template (nếu auto_task)

    is_required BOOLEAN DEFAULT 1,
    created_at TEXT,

    FOREIGN KEY (scenario_id) REFERENCES customer_care_scenarios(scenario_id) ON DELETE CASCADE,
    FOREIGN KEY (template_id) REFERENCES message_templates(template_id),
    FOREIGN KEY (task_template_id) REFERENCES task_templates(template_id)
);

CREATE INDEX idx_scenario_steps_scenario ON scenario_steps(scenario_id);
CREATE INDEX idx_scenario_steps_order ON scenario_steps(scenario_id, step_order);
```

**Sample Data:**
```sql
-- Step 1: Auto gửi Zalo chào mừng ngay
INSERT INTO scenario_steps VALUES (
    'step_001',
    'scenario_001',
    1,
    'Gửi Zalo chào mừng',
    'Tự động gửi tin nhắn Zalo chào mừng khách hàng mới',
    'auto_message',
    0, 0,  -- Ngay lập tức
    'scenario_start',
    'zalo',
    'tmsg_welcome_001',  -- Template message
    NULL,  -- Không có task template
    1,
    '2025-11-01 10:00:00'
);

-- Step 2: Tạo task gọi điện sau 2h
INSERT INTO scenario_steps VALUES (
    'step_002',
    'scenario_001',
    2,
    'Gọi điện tư vấn',
    'Tạo task nhắc sales gọi điện trong vòng 2 giờ',
    'auto_task',
    0, 2,  -- Sau 2 giờ
    'scenario_start',
    'call',
    NULL,  -- Không có message template
    'tmpl_default_001',  -- Task template "Gọi điện chào khách hàng mới"
    1,
    '2025-11-01 10:00:00'
);

-- Step 3: Follow up sau 3 ngày
INSERT INTO scenario_steps VALUES (
    'step_003',
    'scenario_001',
    3,
    'Follow up sau 3 ngày',
    'Nếu chưa có phản hồi, tự động tạo task follow up',
    'auto_task',
    3, 0,  -- Sau 3 ngày
    'scenario_start',
    'call',
    NULL,
    'tmpl_default_002',  -- Task template "Follow up"
    0,  -- Optional
    '2025-11-01 10:00:00'
);
```

---

#### E. `customer_scenario_tracking` - Tracking kịch bản đang chạy

```sql
CREATE TABLE customer_scenario_tracking (
    tracking_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    scenario_id TEXT NOT NULL,

    current_step_order INTEGER DEFAULT 0,
    scenario_status TEXT DEFAULT 'active',      -- active/paused/completed/cancelled

    started_at TEXT,
    completed_at TEXT,
    last_action_at TEXT,

    created_by TEXT,

    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (scenario_id) REFERENCES customer_care_scenarios(scenario_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

CREATE INDEX idx_tracking_customer ON customer_scenario_tracking(customer_id);
CREATE INDEX idx_tracking_scenario ON customer_scenario_tracking(scenario_id);
CREATE INDEX idx_tracking_status ON customer_scenario_tracking(scenario_status);
```

---

#### F. `message_templates` - Template tin nhắn

```sql
CREATE TABLE message_templates (
    template_id TEXT PRIMARY KEY,               -- "tmsg_abc123"
    user_id TEXT,                               -- NULL = shared template

    template_name TEXT NOT NULL,
    template_description TEXT,

    channel TEXT NOT NULL,                      -- email/zalo/telegram/sms
    category TEXT,                              -- greeting/follow_up/quotation/thank_you/promotion/other

    -- Content
    subject TEXT,                               -- Cho email
    content TEXT NOT NULL,                      -- Nội dung (hỗ trợ variables)

    -- Variables support
    variables_help TEXT,                        -- Help text cho variables: {customer_name}, {product_name}...

    is_shared BOOLEAN DEFAULT 0,
    created_by TEXT,
    usage_count INTEGER DEFAULT 0,

    created_at TEXT,
    updated_at TEXT,

    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

CREATE INDEX idx_message_templates_user ON message_templates(user_id);
CREATE INDEX idx_message_templates_channel ON message_templates(channel);
CREATE INDEX idx_message_templates_category ON message_templates(category);
CREATE INDEX idx_message_templates_shared ON message_templates(is_shared);
```

**Sample Data:**
```sql
INSERT INTO message_templates VALUES (
    'tmsg_welcome_001',
    NULL,  -- Shared
    'Chào mừng khách hàng mới - Zalo',
    'Template chào mừng khách hàng mới qua Zalo',
    'zalo',
    'greeting',
    NULL,  -- Zalo không có subject
    'Xin chào {customer_name},

Cảm ơn bạn đã quan tâm đến sản phẩm nhà thông minh Hunonic!

Chúng tôi chuyên cung cấp giải pháp Smart Home toàn diện cho:
• Biệt thự & Căn hộ cao cấp
• Khách sạn & Resort
• Văn phòng thông minh

Hunonic rất mong được tư vấn miễn phí cho dự án của bạn.

Xin vui lòng cho biết thời gian thuận tiện để chúng tôi liên hệ.

Trân trọng,
Hunonic Smart Home
Hotline: 1900-xxxx',
    'Variables: {customer_name}, {sales_name}, {sales_phone}',
    1,  -- shared
    'admin',
    0,
    '2025-11-01 10:00:00',
    '2025-11-01 10:00:00'
);
```

---

#### G. `quotations` - Báo giá

```sql
CREATE TABLE quotations (
    quotation_id TEXT PRIMARY KEY,              -- "quot_abc123"
    customer_id TEXT NOT NULL,
    user_id TEXT NOT NULL,                      -- Người tạo báo giá

    quotation_number TEXT UNIQUE NOT NULL,      -- "QT-2025-001" (auto-increment)
    title TEXT NOT NULL,
    description TEXT,

    -- Financial
    subtotal REAL DEFAULT 0,
    discount_percent REAL DEFAULT 0,
    discount_amount REAL DEFAULT 0,
    tax_percent REAL DEFAULT 0,                 -- VAT 10%
    tax_amount REAL DEFAULT 0,
    total_amount REAL DEFAULT 0,

    -- Status
    status TEXT DEFAULT 'draft',                -- draft/sent/viewed/accepted/rejected/expired
    valid_until TEXT,

    -- Tracking
    sent_at TEXT,
    viewed_at TEXT,
    accepted_at TEXT,
    rejected_at TEXT,

    notes TEXT,
    terms_and_conditions TEXT,

    created_at TEXT,
    updated_at TEXT,

    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX idx_quotations_customer ON quotations(customer_id);
CREATE INDEX idx_quotations_user ON quotations(user_id);
CREATE INDEX idx_quotations_status ON quotations(status);
CREATE INDEX idx_quotations_number ON quotations(quotation_number);
```

**Sample Data:**
```sql
INSERT INTO quotations VALUES (
    'quot_001',
    'cust_001',
    'user_123',
    'QT-2025-001',
    'Báo giá hệ thống Smart Home - Villa Thảo Điền',
    'Báo giá chi tiết cho hệ thống Smart Home tại Villa Thảo Điền, bao gồm chiếu sáng thông minh, rèm cửa tự động, điều hòa AI',
    2000000000,  -- 2 tỷ subtotal
    5,  -- 5% discount
    100000000,  -- 100tr discount
    10,  -- 10% VAT
    190000000,  -- 190tr VAT
    2090000000,  -- 2.09 tỷ total
    'sent',
    '2025-12-31',
    '2025-11-02 10:00:00',
    '2025-11-02 14:30:00',  -- viewed
    NULL,  -- chưa accept
    NULL,  -- chưa reject
    'Giá đã bao gồm lắp đặt và bảo hành 24 tháng',
    'Điều khoản & điều kiện:\n- Báo giá có hiệu lực 30 ngày\n- Thanh toán: 30% đặt cọc, 40% khi thi công, 30% khi nghiệm thu\n- Bảo hành 24 tháng',
    '2025-11-02 09:00:00',
    '2025-11-02 14:30:00'
);
```

---

#### H. `quotation_items` - Chi tiết báo giá

```sql
CREATE TABLE quotation_items (
    item_id TEXT PRIMARY KEY,
    quotation_id TEXT NOT NULL,

    item_type TEXT DEFAULT 'product',           -- product/service/installation/warranty
    product_name TEXT NOT NULL,
    description TEXT,
    unit TEXT DEFAULT 'cái',

    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    subtotal REAL NOT NULL,

    sort_order INTEGER DEFAULT 0,

    FOREIGN KEY (quotation_id) REFERENCES quotations(quotation_id) ON DELETE CASCADE
);

CREATE INDEX idx_quotation_items_quotation ON quotation_items(quotation_id);
CREATE INDEX idx_quotation_items_order ON quotation_items(quotation_id, sort_order);
```

**Sample Data:**
```sql
INSERT INTO quotation_items VALUES
('item_001', 'quot_001', 'product', 'Công tắc thông minh WiFi', '3 gang, điều khiển từ xa', 'cái', 50, 500000, 25000000, 1),
('item_002', 'quot_001', 'product', 'Gateway Zigbee', 'Hub trung tâm điều khiển', 'cái', 5, 2000000, 10000000, 2),
('item_003', 'quot_001', 'product', 'Motor rèm thông minh', 'Động cơ rèm tự động Somfy', 'bộ', 20, 3000000, 60000000, 3),
('item_004', 'quot_001', 'product', 'Sensor cửa', 'Cảm biến mở/đóng cửa', 'cái', 30, 200000, 6000000, 4),
('item_005', 'quot_001', 'service', 'Lắp đặt & Lập trình', 'Thi công, lắp đặt, lập trình kịch bản', 'gói', 1, 500000000, 500000000, 5),
('item_006', 'quot_001', 'warranty', 'Bảo hành mở rộng', 'Bảo hành 24 tháng + bảo trì định kỳ', 'năm', 2, 50000000, 100000000, 6);
```

---

### 1.2. Summary of Tables

```
CRM MODULE TABLES:
1. customers                    - Thông tin khách hàng
2. customer_interactions        - Lịch sử tương tác
3. customer_care_scenarios      - Kịch bản chăm sóc
4. scenario_steps               - Các bước trong kịch bản
5. customer_scenario_tracking   - Tracking kịch bản đang chạy
6. message_templates            - Template tin nhắn
7. quotations                   - Báo giá
8. quotation_items              - Chi tiết báo giá
```

---

## 2. CUSTOMER MANAGEMENT

### 2.1. UI Mockup - Customer Dashboard

```html
┌──────────────────────────────────────────────────────────────────┐
│  👥 QUẢN LÝ KHÁCH HÀNG                      [+ Thêm KH mới]      │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  📊 TỔNG QUAN                                                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐ │
│  │ 🔥 HOT     │  │ 🟡 WARM    │  │ 🔵 COLD    │  │ ✅ WON     │ │
│  │    24      │  │    67      │  │    143     │  │    89      │ │
│  │  +3 tuần   │  │  -5 tuần   │  │  +12 tuần  │  │  +8 tháng  │ │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘ │
│                                                                   │
│  🔍 [Tìm kiếm: tên, SĐT, email...]    [🔽 Lọc]  [📊 Báo cáo]     │
│                                                                   │
│  ┌─ FILTERS ────────────────────────────────────────────────┐    │
│  │ Status: [All ▼]  Priority: [All ▼]  Source: [All ▼]     │    │
│  │ Assigned: [Me ▼]  Follow-up: [Today ▼]                  │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                   │
│  📋 CẦN FOLLOW HÔM NAY (12)                                       │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │ 🔥 Nguyễn Văn A - Villa Thảo Điền                           ││
│  │    📞 0909123456 | ✉️ nguyenvana@email.com                  ││
│  │    🏢 Công ty ABC | 📍 Q2, TP.HCM                           ││
│  │    💰 Budget: 2.5 tỷ | 📅 Close: Q4/2025                    ││
│  │    ⏰ Follow lúc 14:00 - Gọi tư vấn gói Smart Lighting      ││
│  │    📝 Note: Đã gửi báo giá QT-2025-001                      ││
│  │    Tương tác: 5 lần | Lần cuối: 01/11 14:30                ││
│  │                                                              ││
│  │    [👁️ Xem] [📞 Gọi] [✉️ Email] [💬 Zalo] [💰 Báo giá]      ││
│  ├──────────────────────────────────────────────────────────────┤│
│  │ 🟡 Trần Thị B - Chung cư Vinhomes                           ││
│  │    📞 0901234567 | ✉️ tranthib@email.com                    ││
│  │    📍 Q9, TP.HCM                                            ││
│  │    💰 Budget: 800tr | 📅 Close: Q1/2026                     ││
│  │    ⏰ Follow lúc 16:00 - Gửi catalog sản phẩm               ││
│  │    Tương tác: 2 lần | Lần cuối: 28/10 10:00                ││
│  │                                                              ││
│  │    [👁️ Xem] [📞 Gọi] [✉️ Email] [💬 Zalo] [💰 Báo giá]      ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                   │
│  📋 TẤT CẢ KHÁCH HÀNG (323) - [Show: 25 ▼] [Page 1/13]          │
│                                                                   │
│  [Xuất Excel] [Import khách hàng] [Gửi hàng loạt]               │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2. UI Mockup - Customer Detail

```html
┌──────────────────────────────────────────────────────────────────┐
│  ← Quay lại              👤 NGUYỄN VĂN A         [✏️ Sửa] [🗑️]    │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─ THÔNG TIN CƠ BẢN ──────────────┐  ┌─ TRẠNG THÁI ─────────┐  │
│  │ 📱 0909123456                    │  │ 🔥 HOT               │  │
│  │ ✉️ nguyenvana@email.com          │  │ 💼 Qualified         │  │
│  │ 🏢 Công ty ABC (MST: 0123456789) │  │ 📁 Business          │  │
│  │ 📍 123 Đường XYZ, P.Thảo Điền,   │  │ 👤 Phụ trách: Hải    │  │
│  │    Q2, TP.HCM                    │  │ 📅 Follow: 05/11     │  │
│  │ 🗺️ [Xem Google Maps]             │  │ 💰 Budget: 2.5 tỷ    │  │
│  │                                   │  │ 🎯 Source: Website   │  │
│  │ 🔗 Social:                        │  │ 🏷️ Tags:             │  │
│  │    [Facebook] [Zalo] [Website]   │  │    [VIP]             │  │
│  │                                   │  │    [Fast Decision]   │  │
│  └───────────────────────────────────┘  └──────────────────────┘  │
│                                                                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                   │
│  [📋 Tổng quan] [💬 Tương tác] [💰 Báo giá] [🏗️ Dự án] [📝 Ghi chú]│
│                                                                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                   │
│  🏗️ DỰ ÁN HIỆN TẠI                                               │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │ 🏠 Villa Thảo Điền - Smart Home Automation              │    │
│  │ Quy mô: 500m², 3 tầng | Ngân sách: 2.5 tỷ              │    │
│  │ Đóng dự kiến: Q1/2026                                   │    │
│  │                                                          │    │
│  │ Yêu cầu:                                                │    │
│  │ • Điều khiển chiếu sáng thông minh toàn bộ villa       │    │
│  │ • Rèm cửa tự động cho tất cả phòng                     │    │
│  │ • Điều hòa nhiệt độ AI                                 │    │
│  │ • Camera giám sát & chuông cửa thông minh              │    │
│  │ • Tích hợp điều khiển giọng nói (Google Home)          │    │
│  │                                                          │    │
│  │ [🏗️ Tạo project] [💰 Tạo báo giá]                       │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                   │
│  💬 LỊCH SỬ TƯƠNG TÁC (5)              [+ Thêm tương tác]        │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │ 📞 01/11/2025 14:30 - Gọi điện tư vấn        by Hải     │    │
│  │    Nội dung: Đã giới thiệu sản phẩm, khách quan tâm    │    │
│  │    đến tính năng điều khiển từ xa và tích hợp AI.      │    │
│  │    Yêu cầu xem demo và báo giá chi tiết.               │    │
│  │                                                          │    │
│  │    Kết quả: ✅ Interested                               │    │
│  │    Next: Gửi báo giá QT-2025-001 vào 02/11             │    │
│  │    Duration: 30 phút                                    │    │
│  │                                                          │    │
│  │    → Task: [Gửi báo giá 02/11] (Completed ✓)           │    │
│  │    [✏️ Sửa] [🗑️ Xóa]                                     │    │
│  ├──────────────────────────────────────────────────────────┤    │
│  │ ✉️ 28/10/2025 09:15 - Email giới thiệu      by Hải     │    │
│  │    Đã gửi email giới thiệu công ty và sản phẩm Smart   │    │
│  │    Home. Khách phản hồi trong 2 giờ, quan tâm.         │    │
│  │                                                          │    │
│  │    Kết quả: ✅ Interested                               │    │
│  │    Next: Gọi điện tư vấn chi tiết                      │    │
│  │    [✏️ Sửa] [🗑️ Xóa]                                     │    │
│  ├──────────────────────────────────────────────────────────┤    │
│  │ 🌐 25/10/2025 15:20 - Điền form website     (Inbound)  │    │
│  │    Lead từ website, điền form yêu cầu tư vấn.         │    │
│  │    Nội dung: Cần tư vấn hệ thống nhà thông minh cho    │    │
│  │    villa 500m²                                          │    │
│  │                                                          │    │
│  │    → Auto tạo customer & trigger scenario "Lead mới"    │    │
│  │    [✏️ Sửa] [🗑️ Xóa]                                     │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                   │
│  [Tất cả tương tác] [📥 Export]                                  │
│                                                                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                   │
│  💰 BÁO GIÁ (1)                                                   │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │ 📄 QT-2025-001 - Báo giá hệ thống Smart Home            │    │
│  │    💰 2.09 tỷ (bao gồm VAT) | 📅 02/11/2025             │    │
│  │    Status: ✉️ Sent → 👁️ Viewed (02/11 14:30)            │    │
│  │    Valid until: 31/12/2025                              │    │
│  │                                                          │    │
│  │    [👁️ Xem] [✏️ Sửa] [📤 Gửi lại] [✅ Mark Won]          │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                   │
│  🤖 KỊCH BẢN ĐANG CHẠY                                           │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │ ✅ Lead mới từ Website                                   │    │
│  │    Step 1/3: ✅ Gửi email chào mừng (Done)              │    │
│  │    Step 2/3: ✅ Gọi điện tư vấn (Done)                  │    │
│  │    Step 3/3: ⏳ Follow up sau 3 ngày (Scheduled 05/11)  │    │
│  │                                                          │    │
│  │    [⏸️ Tạm dừng] [❌ Hủy scenario]                       │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                   │
│  📝 GHI CHÚ                                   [✏️ Chỉnh sửa]      │
│  Khách hàng tiềm năng cao, đã làm việc với nhiều nhà thầu,      │
│  quyết định nhanh. Quan tâm đến chất lượng sản phẩm và dịch vụ   │
│  hậu mãi. Budget không phải vấn đề.                              │
│                                                                   │
│  [💾 Lưu ghi chú]                                                │
│                                                                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                   │
│  📊 THỐNG KÊ                                                      │
│  • Tạo lúc: 25/10/2025 15:20 (by System)                        │
│  • Cập nhật: 01/11/2025 14:30 (by Hải)                          │
│  • Tổng tương tác: 5 lần                                         │
│  • Doanh thu: 0đ (chưa có order)                                 │
│  • Conversion probability: 85% (dựa trên AI prediction)          │
│                                                                   │
│  [📞 Gọi ngay] [✉️ Email] [💬 Zalo] [💰 Tạo báo giá] [🏗️ Tạo dự án]│
└──────────────────────────────────────────────────────────────────┘
```

### 2.3. Backend Logic - Customer Manager

**File:** `backend/crm/customer_manager.py`

```python
# -*- coding: utf-8 -*-
"""
CUSTOMER MANAGER
================

Quản lý khách hàng (CRUD operations + search + filters)

Functions:
- create_customer(customer_data) -> customer_id
- get_customer(customer_id) -> dict
- update_customer(customer_id, updates) -> bool
- delete_customer(customer_id) -> bool
- search_customers(query, filters) -> list
- get_customers_by_user(user_id, filters) -> list
- get_customers_need_follow_up(user_id, date) -> list
- assign_customer(customer_id, assigned_to) -> bool
- update_lead_status(customer_id, new_status) -> bool
- update_priority(customer_id, new_priority) -> bool
- add_tag(customer_id, tag) -> bool
- remove_tag(customer_id, tag) -> bool
"""

import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

class CustomerManager:
    def __init__(self, db):
        """
        Args:
            db: DatabaseManager instance
        """
        self.db = db

    def create_customer(self, customer_data: Dict[str, Any]) -> str:
        """
        Tạo khách hàng mới

        Args:
            customer_data: {
                'user_id': str,  # Sales owner
                'full_name': str,
                'phone_number': str,
                'email': str,
                'company_name': str,
                'tax_code': str,
                'address': str,
                'city': str,
                'district': str,
                'ward': str,
                'google_maps_url': str,
                'latitude': float,
                'longitude': float,
                'customer_type': str,  # individual/business/dealer
                'lead_source': str,    # facebook/zalo/website...
                'lead_status': str,    # new/contacted/qualified...
                'priority_level': str, # hot/warm/cold
                'industry': str,
                'project_scale': str,
                'estimated_budget': float,
                'expected_close_date': str,
                'assigned_to': str,  # user_id phụ trách
                'facebook_url': str,
                'zalo_id': str,
                'telegram_id': str,
                'website': str,
                'tags': list,  # ['vip', 'fast_decision']
                'notes': str,
                'created_by': str
            }

        Returns:
            customer_id

        Algorithm:
            1. Validate required fields
            2. Generate customer_id
            3. Process tags (convert to JSON)
            4. Insert into database
            5. Trigger scenario nếu lead_source match
            6. Return customer_id
        """
        try:
            # Validate
            if not customer_data.get('full_name'):
                raise ValueError("full_name is required")

            # Generate ID
            customer_id = f"cust_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()

            # Process tags
            tags = customer_data.get('tags', [])
            tags_json = json.dumps(tags) if tags else None

            # Prepare record
            record = {
                'customer_id': customer_id,
                'user_id': customer_data.get('user_id'),
                'full_name': customer_data['full_name'],
                'phone_number': customer_data.get('phone_number'),
                'email': customer_data.get('email'),
                'company_name': customer_data.get('company_name'),
                'tax_code': customer_data.get('tax_code'),
                'address': customer_data.get('address'),
                'city': customer_data.get('city'),
                'district': customer_data.get('district'),
                'ward': customer_data.get('ward'),
                'google_maps_url': customer_data.get('google_maps_url'),
                'latitude': customer_data.get('latitude'),
                'longitude': customer_data.get('longitude'),
                'customer_type': customer_data.get('customer_type', 'individual'),
                'lead_source': customer_data.get('lead_source'),
                'lead_status': customer_data.get('lead_status', 'new'),
                'priority_level': customer_data.get('priority_level', 'cold'),
                'industry': customer_data.get('industry'),
                'project_scale': customer_data.get('project_scale'),
                'estimated_budget': customer_data.get('estimated_budget'),
                'expected_close_date': customer_data.get('expected_close_date'),
                'assigned_to': customer_data.get('assigned_to') or customer_data.get('user_id'),
                'last_contact_date': None,
                'next_follow_up_date': customer_data.get('next_follow_up_date'),
                'total_interactions': 0,
                'total_revenue': 0,
                'total_orders': 0,
                'facebook_url': customer_data.get('facebook_url'),
                'zalo_id': customer_data.get('zalo_id'),
                'telegram_id': customer_data.get('telegram_id'),
                'website': customer_data.get('website'),
                'tags': tags_json,
                'notes': customer_data.get('notes'),
                'created_at': now,
                'updated_at': now,
                'created_by': customer_data.get('created_by')
            }

            # Insert
            with self.db.get_connection() as conn:
                columns = ', '.join(record.keys())
                placeholders = ', '.join(['?' for _ in record])
                query = f"INSERT INTO customers ({columns}) VALUES ({placeholders})"

                self.db.execute_insert(conn, query, tuple(record.values()))
                conn.commit()

            print(f"✅ Customer created: {customer_id}")

            # Trigger scenario
            self._trigger_scenario_if_match(customer_id, customer_data.get('lead_source'))

            return customer_id

        except Exception as e:
            print(f"❌ Error creating customer: {e}")
            raise

    def _trigger_scenario_if_match(self, customer_id: str, lead_source: str):
        """
        Tự động trigger scenario nếu lead_source match

        Example:
            Lead từ Facebook → Trigger scenario "Lead mới từ Facebook"
        """
        try:
            if not lead_source:
                return

            from crm.scenario_manager import ScenarioManager
            scenario_manager = ScenarioManager(self.db)

            # Tìm scenario match với lead_source
            with self.db.get_connection() as conn:
                query = """
                    SELECT scenario_id
                    FROM customer_care_scenarios
                    WHERE is_active = 1
                    AND trigger_event = 'customer_created'
                    AND customer_segment = 'new_lead'
                """
                scenarios = self.db.execute_query(conn, query)

                for scenario in scenarios:
                    scenario_manager.start_scenario(customer_id, scenario['scenario_id'])
                    print(f"✅ Started scenario {scenario['scenario_id']} for customer {customer_id}")

        except Exception as e:
            print(f"⚠️  Error triggering scenario: {e}")

    def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin khách hàng

        Returns:
            dict with customer info + parsed tags
        """
        try:
            with self.db.get_connection() as conn:
                query = """
                    SELECT c.*,
                           u1.display_name as assigned_to_name,
                           u2.display_name as created_by_name
                    FROM customers c
                    LEFT JOIN users u1 ON c.assigned_to = u1.user_id
                    LEFT JOIN users u2 ON c.created_by = u2.user_id
                    WHERE c.customer_id = ?
                """
                results = self.db.execute_query(conn, query, (customer_id,))

                if results:
                    customer = results[0]

                    # Parse tags
                    if customer['tags']:
                        customer['tags'] = json.loads(customer['tags'])
                    else:
                        customer['tags'] = []

                    return customer

                return None

        except Exception as e:
            print(f"❌ Error getting customer: {e}")
            return None

    def update_customer(self, customer_id: str, updates: Dict[str, Any]) -> bool:
        """
        Cập nhật thông tin khách hàng

        Args:
            customer_id: ID customer
            updates: Dict các field cần update

        Returns:
            True nếu thành công
        """
        try:
            allowed_fields = [
                'full_name', 'phone_number', 'email', 'company_name', 'tax_code',
                'address', 'city', 'district', 'ward',
                'google_maps_url', 'latitude', 'longitude',
                'customer_type', 'lead_source', 'lead_status', 'priority_level',
                'industry', 'project_scale', 'estimated_budget', 'expected_close_date',
                'assigned_to', 'next_follow_up_date',
                'facebook_url', 'zalo_id', 'telegram_id', 'website',
                'tags', 'notes'
            ]

            set_strs = []
            params = []

            for field in allowed_fields:
                if field in updates:
                    value = updates[field]

                    # Process tags
                    if field == 'tags' and isinstance(value, list):
                        value = json.dumps(value)

                    set_strs.append(f"{field} = ?")
                    params.append(value)

            if not set_strs:
                return False

            set_strs.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(customer_id)

            with self.db.get_connection() as conn:
                query = f"UPDATE customers SET {', '.join(set_strs)} WHERE customer_id = ?"
                self.db.execute_update(conn, query, tuple(params))
                conn.commit()

            print(f"✅ Customer updated: {customer_id}")
            return True

        except Exception as e:
            print(f"❌ Error updating customer: {e}")
            return False

    def delete_customer(self, customer_id: str) -> bool:
        """Xóa khách hàng (CASCADE sẽ xóa interactions, quotations...)"""
        try:
            with self.db.get_connection() as conn:
                query = "DELETE FROM customers WHERE customer_id = ?"
                self.db.execute_update(conn, query, (customer_id,))
                conn.commit()

            print(f"✅ Customer deleted: {customer_id}")
            return True

        except Exception as e:
            print(f"❌ Error deleting customer: {e}")
            return False

    def search_customers(
        self,
        query: str = None,
        filters: Dict[str, Any] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Tìm kiếm & lọc khách hàng

        Args:
            query: Tìm theo tên, SĐT, email, công ty
            filters: {
                'user_id': str,         # Customers của user này
                'assigned_to': str,     # Được assign cho user này
                'lead_status': str,     # new/contacted/qualified...
                'priority_level': str,  # hot/warm/cold
                'lead_source': str,     # facebook/zalo...
                'customer_type': str,   # individual/business
                'tags': list,           # ['vip', 'fast_decision']
                'created_from': str,    # Tạo từ ngày
                'created_to': str       # Tạo đến ngày
            }
            limit: Số lượng tối đa
            offset: Skip bao nhiêu records

        Returns:
            List of customers
        """
        try:
            with self.db.get_connection() as conn:
                conditions = []
                params = []

                # Search query
                if query:
                    conditions.append("""
                        (full_name LIKE ? OR
                         phone_number LIKE ? OR
                         email LIKE ? OR
                         company_name LIKE ?)
                    """)
                    search_param = f"%{query}%"
                    params.extend([search_param, search_param, search_param, search_param])

                # Filters
                if filters:
                    if filters.get('user_id'):
                        conditions.append("user_id = ?")
                        params.append(filters['user_id'])

                    if filters.get('assigned_to'):
                        conditions.append("assigned_to = ?")
                        params.append(filters['assigned_to'])

                    if filters.get('lead_status'):
                        conditions.append("lead_status = ?")
                        params.append(filters['lead_status'])

                    if filters.get('priority_level'):
                        conditions.append("priority_level = ?")
                        params.append(filters['priority_level'])

                    if filters.get('lead_source'):
                        conditions.append("lead_source = ?")
                        params.append(filters['lead_source'])

                    if filters.get('customer_type'):
                        conditions.append("customer_type = ?")
                        params.append(filters['customer_type'])

                    if filters.get('tags'):
                        # Search trong JSON tags
                        for tag in filters['tags']:
                            conditions.append("tags LIKE ?")
                            params.append(f'%"{tag}"%')

                    if filters.get('created_from'):
                        conditions.append("created_at >= ?")
                        params.append(filters['created_from'])

                    if filters.get('created_to'):
                        conditions.append("created_at <= ?")
                        params.append(filters['created_to'])

                # Build query
                where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

                query_sql = f"""
                    SELECT c.*,
                           u.display_name as assigned_to_name
                    FROM customers c
                    LEFT JOIN users u ON c.assigned_to = u.user_id
                    {where_clause}
                    ORDER BY c.updated_at DESC
                    LIMIT ? OFFSET ?
                """

                params.extend([limit, offset])

                results = self.db.execute_query(conn, query_sql, tuple(params))

                # Parse tags for each customer
                for customer in results:
                    if customer['tags']:
                        customer['tags'] = json.loads(customer['tags'])
                    else:
                        customer['tags'] = []

                return results

        except Exception as e:
            print(f"❌ Error searching customers: {e}")
            return []

    def get_customers_need_follow_up(
        self,
        user_id: str = None,
        date: str = None
    ) -> List[Dict[str, Any]]:
        """
        Lấy danh sách customers cần follow up

        Args:
            user_id: Nếu cung cấp, chỉ lấy customers của user này
            date: Ngày cần follow (default = hôm nay)

        Returns:
            List of customers cần follow up

        Algorithm:
            1. Nếu date = None → date = today
            2. Query customers có next_follow_up_date = date
            3. Order by priority_level (hot > warm > cold)
            4. Return results
        """
        try:
            if date is None:
                date = datetime.now().strftime('%Y-%m-%d')

            with self.db.get_connection() as conn:
                conditions = [
                    "DATE(next_follow_up_date) = ?",
                    "lead_status NOT IN ('won', 'lost', 'archived')"
                ]
                params = [date]

                if user_id:
                    conditions.append("(user_id = ? OR assigned_to = ?)")
                    params.extend([user_id, user_id])

                where_clause = " WHERE " + " AND ".join(conditions)

                query = f"""
                    SELECT c.*,
                           u.display_name as assigned_to_name
                    FROM customers c
                    LEFT JOIN users u ON c.assigned_to = u.user_id
                    {where_clause}
                    ORDER BY
                        CASE priority_level
                            WHEN 'hot' THEN 1
                            WHEN 'warm' THEN 2
                            WHEN 'cold' THEN 3
                            ELSE 4
                        END,
                        next_follow_up_date ASC
                """

                results = self.db.execute_query(conn, query, tuple(params))

                # Parse tags
                for customer in results:
                    if customer['tags']:
                        customer['tags'] = json.loads(customer['tags'])
                    else:
                        customer['tags'] = []

                return results

        except Exception as e:
            print(f"❌ Error getting follow-up customers: {e}")
            return []

    def assign_customer(self, customer_id: str, assigned_to: str) -> bool:
        """Assign customer cho user khác"""
        try:
            with self.db.get_connection() as conn:
                query = "UPDATE customers SET assigned_to = ?, updated_at = ? WHERE customer_id = ?"
                self.db.execute_update(conn, query, (assigned_to, datetime.now().isoformat(), customer_id))
                conn.commit()

            print(f"✅ Customer {customer_id} assigned to {assigned_to}")
            return True

        except Exception as e:
            print(f"❌ Error assigning customer: {e}")
            return False

    def update_lead_status(self, customer_id: str, new_status: str) -> bool:
        """
        Cập nhật lead status

        Statuses: new → contacted → qualified → proposal → negotiation → won/lost
        """
        try:
            with self.db.get_connection() as conn:
                query = "UPDATE customers SET lead_status = ?, updated_at = ? WHERE customer_id = ?"
                self.db.execute_update(conn, query, (new_status, datetime.now().isoformat(), customer_id))
                conn.commit()

            print(f"✅ Customer {customer_id} status updated to {new_status}")

            # Nếu won → Tạo notification celebration
            if new_status == 'won':
                self._notify_won_deal(customer_id)

            return True

        except Exception as e:
            print(f"❌ Error updating lead status: {e}")
            return False

    def _notify_won_deal(self, customer_id: str):
        """Gửi notification khi won deal"""
        try:
            customer = self.get_customer(customer_id)
            if not customer:
                return

            message = f"🎉 Chúc mừng! Bạn đã chốt deal với khách hàng: {customer['full_name']}"

            from notifications.telegram_notifier import TelegramNotifier
            from utils.config_loader import ConfigLoader

            config = ConfigLoader.load_config()
            notifier = TelegramNotifier(config)

            # Gửi cho assigned user
            with self.db.get_connection() as conn:
                query = "SELECT telegram_user_id FROM users WHERE user_id = ?"
                user = self.db.execute_query(conn, query, (customer['assigned_to'],))

                if user and user[0].get('telegram_user_id'):
                    notifier.send_notification(user[0]['telegram_user_id'], message)

        except Exception as e:
            print(f"⚠️  Error notifying won deal: {e}")

    def update_priority(self, customer_id: str, new_priority: str) -> bool:
        """Cập nhật priority level (hot/warm/cold)"""
        try:
            with self.db.get_connection() as conn:
                query = "UPDATE customers SET priority_level = ?, updated_at = ? WHERE customer_id = ?"
                self.db.execute_update(conn, query, (new_priority, datetime.now().isoformat(), customer_id))
                conn.commit()

            print(f"✅ Customer {customer_id} priority updated to {new_priority}")
            return True

        except Exception as e:
            print(f"❌ Error updating priority: {e}")
            return False

    def add_tag(self, customer_id: str, tag: str) -> bool:
        """Thêm tag cho customer"""
        try:
            customer = self.get_customer(customer_id)
            if not customer:
                return False

            tags = customer['tags']
            if tag not in tags:
                tags.append(tag)
                return self.update_customer(customer_id, {'tags': tags})

            return True

        except Exception as e:
            print(f"❌ Error adding tag: {e}")
            return False

    def remove_tag(self, customer_id: str, tag: str) -> bool:
        """Xóa tag khỏi customer"""
        try:
            customer = self.get_customer(customer_id)
            if not customer:
                return False

            tags = customer['tags']
            if tag in tags:
                tags.remove(tag)
                return self.update_customer(customer_id, {'tags': tags})

            return True

        except Exception as e:
            print(f"❌ Error removing tag: {e}")
            return False


# Test function
def test_customer_manager():
    """Test CustomerManager"""
    from core.database_manager import DatabaseManager

    db = DatabaseManager("test_customers.db")
    manager = CustomerManager(db)

    # Test create
    customer_data = {
        'user_id': 'user_123',
        'full_name': 'Nguyễn Văn A',
        'phone_number': '0909123456',
        'email': 'test@example.com',
        'company_name': 'Test Company',
        'customer_type': 'business',
        'lead_source': 'website',
        'lead_status': 'new',
        'priority_level': 'hot',
        'assigned_to': 'user_123',
        'tags': ['vip', 'test'],
        'notes': 'Test customer',
        'created_by': 'admin'
    }

    customer_id = manager.create_customer(customer_data)
    print(f"✅ Created customer: {customer_id}")

    # Test get
    customer = manager.get_customer(customer_id)
    print(f"✅ Got customer: {customer['full_name']}")
    print(f"   Tags: {customer['tags']}")

    # Test update
    manager.update_customer(customer_id, {'priority_level': 'warm'})
    print(f"✅ Updated priority")

    # Test search
    results = manager.search_customers(query='Nguyễn')
    print(f"✅ Search results: {len(results)}")

    # Test tags
    manager.add_tag(customer_id, 'fast_decision')
    manager.remove_tag(customer_id, 'test')
    customer = manager.get_customer(customer_id)
    print(f"✅ Updated tags: {customer['tags']}")

    # Cleanup
    import os
    os.remove("test_customers.db")
    print("✅ Test passed!")

if __name__ == "__main__":
    test_customer_manager()
```

---

(File này quá dài, tôi sẽ tạo phần 2 cho phần còn lại...)

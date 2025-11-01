# HUNONIC MARKETING TOOLS - IMPLEMENTATION GUIDE

> **Hướng dẫn triển khai chi tiết cho AI Code Generator**

---

## 📚 DANH SÁCH FILES SPEC

### 1. Task Module Enhancement
- `SPEC_TASK_ENHANCEMENT.md` - Database schema, Templates, Recurring Tasks (Part 1)
- `SPEC_TASK_ENHANCEMENT_PART2.md` - Dependencies, Checklists, API endpoints, Migration scripts (Part 2)

### 2. CRM Module
- `SPEC_CRM_MODULE.md` - Database schema, Customer Management (Part 1)
- `SPEC_CRM_MODULE_PART2.md` - Interactions, Scenarios, Templates (Part 2)

---

## 🚀 THỨ TỰ TRIỂN KHAI ĐỀ XUẤT

### PHASE 1: TASK ENHANCEMENTS (Week 1-2)

#### Step 1.1: Database Migration
```bash
# Đọc file và thực hiện:
SPEC_TASK_ENHANCEMENT.md → Section 1 (Database Schema)
SPEC_TASK_ENHANCEMENT_PART2.md → Section 9 (Migration Scripts)

# Tạo files:
- migrations/010_task_enhancements.py
- migrations/011_seed_task_templates.py

# Chạy migrations:
python3 migrations/010_task_enhancements.py
python3 migrations/011_seed_task_templates.py
```

#### Step 1.2: Backend - Task Templates
```bash
# Đọc và implement:
SPEC_TASK_ENHANCEMENT.md → Section 2 (Task Templates Feature)

# Tạo file:
- backend/task_management/task_template_manager.py

# Test:
python3 backend/task_management/task_template_manager.py
```

#### Step 1.3: Backend - Recurring Tasks
```bash
# Đọc và implement:
SPEC_TASK_ENHANCEMENT.md → Section 3 (Recurring Tasks Feature)

# Tạo file:
- backend/task_management/recurring_task_manager.py

# Setup cron job:
0 * * * * cd /path/to/project && python3 backend/task_management/recurring_task_manager.py
```

#### Step 1.4: Backend - Task Dependencies
```bash
# Đọc và implement:
SPEC_TASK_ENHANCEMENT_PART2.md → Section 4 (Task Dependencies)

# Tạo file:
- backend/task_management/task_dependency_manager.py

# Modify existing:
- backend/task_management/simple_task_manager.py (thêm dependency notification)
```

#### Step 1.5: Backend - Task Checklists
```bash
# Đọc và implement:
SPEC_TASK_ENHANCEMENT_PART2.md → Section 5 (Task Checklists)

# Tạo file:
- backend/task_management/task_checklist_manager.py
```

#### Step 1.6: Frontend Routes & Templates
```bash
# Đọc và implement:
SPEC_TASK_ENHANCEMENT_PART2.md → Section 7 (Frontend Implementation)

# Modify file:
- frontend/app.py (thêm routes mới)

# Tạo templates:
- frontend/templates/tasks/task_templates.html
- frontend/templates/tasks/create_template.html
- frontend/templates/tasks/edit_template.html
- frontend/templates/tasks/create_from_template.html
- frontend/templates/tasks/recurring_tasks.html

# Modify templates:
- frontend/templates/tasks/task_detail.html (thêm dependencies & checklists sections)
```

---

### PHASE 2: CRM MODULE (Week 3-5)

#### Step 2.1: Database Migration
```bash
# Đọc file và thực hiện:
SPEC_CRM_MODULE.md → Section 1 (Database Schema)

# Tạo file:
- migrations/012_crm_module.py

# Chạy migration:
python3 migrations/012_crm_module.py
```

#### Step 2.2: Backend - Customer Management
```bash
# Đọc và implement:
SPEC_CRM_MODULE.md → Section 2 (Customer Management)

# Tạo file:
- backend/crm/customer_manager.py

# Test:
python3 backend/crm/customer_manager.py
```

#### Step 2.3: Backend - Interactions
```bash
# Đọc và implement:
SPEC_CRM_MODULE_PART2.md → Section 3 (Customer Interactions)

# Tạo file:
- backend/crm/interaction_manager.py
```

#### Step 2.4: Backend - Scenarios
```bash
# Đọc và implement:
SPEC_CRM_MODULE_PART2.md → Section 4 (Care Scenarios & Automation)

# Tạo file:
- backend/crm/scenario_manager.py

# Setup cron job:
0 * * * * cd /path/to/project && python3 backend/crm/scenario_manager.py
```

#### Step 2.5: Backend - Message Templates
```bash
# Đọc và implement:
SPEC_CRM_MODULE_PART2.md → Section 5 (Message Templates)

# Tạo file:
- backend/crm/template_manager.py
```

#### Step 2.6: Backend - Quotations
```bash
# Đọc file CRM_MODULE_PART2 (nếu có phần Quotations)

# Tạo file:
- backend/crm/quotation_manager.py
```

#### Step 2.7: Frontend CRM
```bash
# Tạo routes trong:
- frontend/app.py

# Tạo templates:
- frontend/templates/crm/customers_dashboard.html
- frontend/templates/crm/customer_detail.html
- frontend/templates/crm/create_customer.html
- frontend/templates/crm/scenarios.html
- frontend/templates/crm/templates.html
- frontend/templates/crm/quotations.html
- frontend/templates/crm/create_quotation.html
```

---

### PHASE 3: INTEGRATION (Week 6)

#### Step 3.1: Tasks ↔ CRM Integration
```bash
# Modifications cần thiết:
1. Khi tạo customer → Auto tạo task follow-up
2. Khi tạo interaction → Option tạo related task
3. Task detail → Show customer info nếu linked
4. Customer detail → Show related tasks

# Files cần modify:
- backend/crm/customer_manager.py
- backend/crm/interaction_manager.py
- frontend/templates/tasks/task_detail.html
- frontend/templates/crm/customer_detail.html
```

---

## 📋 CHECKLIST TRIỂN KHAI

### Pre-deployment
```
□ Backup database hiện tại
□ Test migrations trên database copy
□ Review tất cả backend code
□ Test tất cả manager classes
□ Setup cron jobs (recurring_task_manager, scenario_manager)
```

### Backend
```
□ task_template_manager.py
□ recurring_task_manager.py
□ task_dependency_manager.py
□ task_checklist_manager.py
□ customer_manager.py
□ interaction_manager.py
□ scenario_manager.py
□ template_manager.py
□ quotation_manager.py
```

### Frontend Routes
```
□ Task Templates routes
□ Recurring Tasks routes
□ Task Dependencies API endpoints
□ Task Checklists API endpoints
□ Customer CRUD routes
□ Customer search/filter routes
□ Interaction routes
□ Scenario routes
□ Message Template routes
□ Quotation routes
```

### Frontend Templates
```
□ tasks/task_templates.html
□ tasks/create_template.html
□ tasks/recurring_tasks.html
□ tasks/task_detail.html (updated)
□ crm/customers_dashboard.html
□ crm/customer_detail.html
□ crm/create_customer.html
□ crm/scenarios.html
□ crm/templates.html
□ crm/quotations.html
```

### Migrations
```
□ 010_task_enhancements.py
□ 011_seed_task_templates.py
□ 012_crm_module.py
□ 013_seed_crm_data.py (optional)
```

### Cron Jobs
```
□ Recurring Task Processor (mỗi giờ)
□ Scenario Processor (mỗi giờ)
```

### Testing
```
□ Test Task Templates: Create, Use, Update, Delete
□ Test Recurring Tasks: Daily, Weekly, Monthly patterns
□ Test Dependencies: Add, Circular detection, Notifications
□ Test Checklists: CRUD, Toggle, Progress
□ Test Customer CRUD
□ Test Customer Search/Filter
□ Test Interactions
□ Test Scenarios: Auto-trigger, Steps execution
□ Test Message Templates
□ Test Quotations
□ Test Integration: Customer → Task linkage
```

---

## 🔧 TROUBLESHOOTING

### Lỗi thường gặp

#### 1. Migration lỗi "table already exists"
```python
# Solution: Thêm IF NOT EXISTS
CREATE TABLE IF NOT EXISTS task_templates (...)
```

#### 2. Circular import trong managers
```python
# Solution: Import trong function thay vì top-level
def some_function():
    from other_module import OtherManager
    manager = OtherManager(self.db)
```

#### 3. JSON serialization lỗi
```python
# Solution: Kiểm tra trước khi json.loads()
if field_value:
    data = json.loads(field_value)
else:
    data = []
```

#### 4. Datetime format không khớp
```python
# Solution: Consistent format
datetime.now().isoformat()  # "2025-11-01T14:30:00.123456"
datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
```

---

## 📊 TESTING PLAN

### Unit Tests

#### Task Module
```python
# test_task_template_manager.py
def test_create_template():
    # Test tạo template với đầy đủ fields
    pass

def test_use_template_with_variables():
    # Test variable replacement
    pass

def test_notification_offset_calculation():
    # Test tính notification times từ offsets
    pass

# test_recurring_task_manager.py
def test_weekly_recurrence():
    # Test weekly pattern với multiple weekdays
    pass

def test_monthly_recurrence():
    # Test monthly pattern
    pass

def test_next_occurrence_calculation():
    # Test thuật toán tính next occurrence
    pass

# test_task_dependency_manager.py
def test_circular_dependency_detection():
    # Test phát hiện circular dependency
    pass

def test_dependency_chain():
    # Test lấy full dependency chain
    pass

# test_task_checklist_manager.py
def test_checklist_progress():
    # Test tính progress percentage
    pass
```

#### CRM Module
```python
# test_customer_manager.py
def test_create_customer():
    pass

def test_search_customers():
    # Test search + filters
    pass

def test_tags_management():
    # Test add/remove tags
    pass

# test_interaction_manager.py
def test_create_interaction_updates_customer():
    # Test side effects
    pass

# test_scenario_manager.py
def test_scenario_execution():
    # Test full scenario flow
    pass

def test_step_delay_calculation():
    pass

# test_template_manager.py
def test_template_variable_replacement():
    pass
```

### Integration Tests
```python
def test_customer_to_task_flow():
    # Tạo customer → Trigger scenario → Tạo task
    pass

def test_interaction_with_task():
    # Tạo interaction + task cùng lúc
    pass

def test_quotation_with_customer():
    # Tạo quotation → Link to customer
    pass
```

---

## 📝 DOCUMENTATION NOTES

### Code Comments
- Tất cả functions phải có docstring rõ ràng
- Algorithm phức tạp phải có comment giải thích
- Edge cases phải được document

### API Documentation
- Mỗi endpoint phải có description
- Request/Response format examples
- Error codes & messages

### User Guide
- Screenshots cho mỗi feature mới
- Step-by-step tutorials
- FAQs

---

## 🎯 SUCCESS CRITERIA

### Functional Requirements
✅ User có thể tạo và sử dụng task templates
✅ Recurring tasks tự động generate đúng lịch
✅ Task dependencies được enforce (không circular)
✅ Checklists hiển thị progress chính xác
✅ Customer CRUD hoạt động đầy đủ
✅ Interactions được log đầy đủ
✅ Scenarios tự động execute theo đúng timeline
✅ Message templates render đúng variables
✅ Quotations tính toán chính xác

### Performance Requirements
✅ Search customers < 500ms với 10k records
✅ Load customer detail < 200ms
✅ Create task from template < 1s
✅ Scenario processor hoàn thành trong 5 minutes (1000 customers)

### Security Requirements
✅ Permissions được check đúng
✅ User chỉ thấy customers được assign
✅ Templates private không leak ra ngoài

---

## 🚀 DEPLOYMENT STEPS

### 1. Staging Environment
```bash
# Backup
pg_dump calendar_tools > backup_$(date +%Y%m%d).sql

# Deploy code
git pull origin develop
pip install -r requirements.txt

# Run migrations
python3 migrations/run_all_migrations.py

# Test
python3 -m pytest tests/

# Setup cron jobs
crontab -e
# Add:
# 0 * * * * cd /path && python3 backend/task_management/recurring_task_manager.py
# 0 * * * * cd /path && python3 backend/crm/scenario_manager.py
```

### 2. Production Deployment
```bash
# Same steps as staging
# + Monitor logs for first 24h
# + Be ready to rollback if issues
```

---

## 📞 SUPPORT

Nếu gặp vấn đề trong quá trình implement, check lại:
1. Database schema có đúng không (PRAGMA table_info)
2. Foreign keys có được tạo không
3. Indexes có được tạo không
4. Cron jobs có đang chạy không (check logs)
5. Permissions có đủ không

---

**END OF IMPLEMENTATION GUIDE**

**Tạo bởi:** Claude Code Agent
**Ngày:** 01/11/2025
**Version:** 1.0

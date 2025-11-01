# 📚 HUNONIC MARKETING TOOLS - DOCUMENTATION

> **Tài liệu đầy đủ cho việc phát triển Hunonic Marketing Tools**
>
> **Mục đích:** Copy các file spec này sang AI khác để viết code

---

## 🎯 TỔNG QUAN

Dự án phát triển **Hunonic Marketing Tools** từ hệ thống Calendar Tools hiện tại thành nền tảng quản lý toàn diện cho đại lý/NPP, bao gồm:

1. **Task Management Enhancement** - Nâng cấp quản lý tác vụ
2. **CRM Module** - Quản lý khách hàng
3. **Project Management** - Quản lý công trình (sẽ phát triển sau)
4. **E-commerce Integration** - Tích hợp Shopee/TikTok (sẽ phát triển sau)

---

## 📁 CẤU TRÚC FILES

### 1. TASK MODULE ENHANCEMENT

#### File: `SPEC_TASK_ENHANCEMENT.md`
**Nội dung:**
- Database schema cho 4 bảng mới:
  - `task_templates` - Mẫu tác vụ
  - `task_recurrence` - Tác vụ lặp lại
  - `task_dependencies` - Phụ thuộc giữa tasks
  - `task_checklists` - Checklist trong task
- Backend implementation:
  - `TaskTemplateManager` - Quản lý templates
  - `RecurringTaskManager` - Quản lý recurring tasks
- UI Mockups chi tiết
- Sample data

#### File: `SPEC_TASK_ENHANCEMENT_PART2.md`
**Nội dung:**
- Backend implementation (tiếp):
  - `TaskDependencyManager` - Quản lý dependencies
  - `TaskChecklistManager` - Quản lý checklists
- Frontend Routes & API Endpoints đầy đủ
- Migration Scripts chi tiết
- Testing & Deployment checklist

**Tính năng chính:**
- ✅ Task Templates với variable support
- ✅ Recurring Tasks (daily/weekly/monthly/custom)
- ✅ Task Dependencies với circular detection
- ✅ Task Checklists với progress tracking

---

### 2. CRM MODULE

#### File: `SPEC_CRM_MODULE.md`
**Nội dung:**
- Database schema cho 8 bảng:
  - `customers` - Khách hàng (30+ fields)
  - `customer_interactions` - Lịch sử tương tác
  - `customer_care_scenarios` - Kịch bản chăm sóc
  - `scenario_steps` - Các bước trong kịch bản
  - `customer_scenario_tracking` - Tracking kịch bản đang chạy
  - `message_templates` - Template tin nhắn
  - `quotations` - Báo giá
  - `quotation_items` - Chi tiết báo giá
- Backend implementation:
  - `CustomerManager` - CRUD, Search, Filter, Tags
- UI Mockups:
  - Customer Dashboard
  - Customer Detail (cực kỳ chi tiết)
- Sample data đầy đủ

#### File: `SPEC_CRM_MODULE_PART2.md`
**Nội dung:**
- Backend implementation (tiếp):
  - `InteractionManager` - Quản lý tương tác
  - `ScenarioManager` - Automation workflows
  - `TemplateManager` - Message templates
  - `QuotationManager` - Báo giá (nếu có)
- Scenario automation logic chi tiết
- Integration với Telegram/Zalo/Email notifications

**Tính năng chính:**
- ✅ Customer Management đầy đủ (30+ fields)
- ✅ Lead tracking & prioritization (Hot/Warm/Cold)
- ✅ Interaction history với multi-channel
- ✅ Automated care scenarios (trigger-based)
- ✅ Message templates với variables
- ✅ Quotation management với items
- ✅ Integration với Tasks (customer → auto create follow-up task)

---

### 3. IMPLEMENTATION GUIDE

#### File: `IMPLEMENTATION_GUIDE.md`
**Nội dung:**
- Thứ tự triển khai từng bước (Step-by-step)
- PHASE 1: Task Enhancements (Week 1-2)
- PHASE 2: CRM Module (Week 3-5)
- PHASE 3: Integration (Week 6)
- Deployment checklist đầy đủ
- Testing plan
- Troubleshooting common issues

---

## 🚀 CÁCH SỬ DỤNG VỚI AI CODE GENERATOR

### Bước 1: Copy toàn bộ nội dung file SPEC

Ví dụ muốn implement Task Templates:

```
1. Mở file: SPEC_TASK_ENHANCEMENT.md
2. Copy toàn bộ Section 1 (Database Schema) → Paste vào AI
3. Copy toàn bộ Section 2 (Task Templates Feature) → Paste vào AI
4. Yêu cầu AI: "Hãy implement code Python theo spec này"
```

### Bước 2: Request AI viết code

**Example prompt cho AI:**

```
Tôi có một dự án Python/Flask + SQLite.

Đây là database schema tôi cần tạo:
[PASTE Section 1 - Database Schema]

Đây là business logic tôi cần implement:
[PASTE Section 2 - Task Templates Feature]

Hãy viết code Python hoàn chỉnh cho:
1. Migration script để tạo bảng task_templates
2. Class TaskTemplateManager với đầy đủ methods như trong spec
3. Test functions để verify code hoạt động đúng

Lưu ý:
- Sử dụng cùng coding style với file hiện có
- Thêm đầy đủ docstrings và comments
- Error handling cẩn thận
- Follow đúng algorithm mô tả trong spec
```

### Bước 3: Implement từng module tuần tự

**Thứ tự đề xuất:**

1. **Task Templates** (dễ nhất - bắt đầu từ đây)
   - Copy: `SPEC_TASK_ENHANCEMENT.md` Section 1, 2
   - Output: `backend/task_management/task_template_manager.py`

2. **Recurring Tasks**
   - Copy: `SPEC_TASK_ENHANCEMENT.md` Section 3
   - Output: `backend/task_management/recurring_task_manager.py`

3. **Task Dependencies**
   - Copy: `SPEC_TASK_ENHANCEMENT_PART2.md` Section 4
   - Output: `backend/task_management/task_dependency_manager.py`

4. **Task Checklists**
   - Copy: `SPEC_TASK_ENHANCEMENT_PART2.md` Section 5
   - Output: `backend/task_management/task_checklist_manager.py`

5. **Customer Management**
   - Copy: `SPEC_CRM_MODULE.md` Section 1, 2
   - Output: `backend/crm/customer_manager.py`

6. **Interactions**
   - Copy: `SPEC_CRM_MODULE_PART2.md` Section 3
   - Output: `backend/crm/interaction_manager.py`

7. **Scenarios**
   - Copy: `SPEC_CRM_MODULE_PART2.md` Section 4
   - Output: `backend/crm/scenario_manager.py`

8. **Templates**
   - Copy: `SPEC_CRM_MODULE_PART2.md` Section 5
   - Output: `backend/crm/template_manager.py`

---

## 💡 TIPS KHI LÀM VIỆC VỚI AI

### 1. Chia nhỏ tasks
❌ **KHÔNG NÊN:** Copy toàn bộ spec vào một lần và yêu cầu AI viết hết
✅ **NÊN:** Chia thành từng function/method nhỏ, verify từng bước

### 2. Verify logic trước khi integrate
```python
# Test function riêng trước
def test_task_template_manager():
    manager = TaskTemplateManager(db)
    # Test từng method
    ...

if __name__ == "__main__":
    test_task_template_manager()
```

### 3. Check database schema
```bash
# Sau khi chạy migration, verify:
sqlite3 database/calendar_tools.db
.schema task_templates
.exit
```

### 4. Incremental development
```
Phase 1.1: Database only
Phase 1.2: Backend manager (CRUD only)
Phase 1.3: Backend manager (advanced features)
Phase 1.4: Frontend routes
Phase 1.5: Frontend UI
Phase 1.6: Integration testing
```

---

## 📊 TÍNH NĂNG OVERVIEW

### Task Module Enhancement

| Feature | File Spec | Complexity | Priority |
|---------|-----------|------------|----------|
| Task Templates | `SPEC_TASK_ENHANCEMENT.md` Section 2 | ⭐⭐ | HIGH |
| Recurring Tasks | `SPEC_TASK_ENHANCEMENT.md` Section 3 | ⭐⭐⭐ | HIGH |
| Task Dependencies | `SPEC_TASK_ENHANCEMENT_PART2.md` Section 4 | ⭐⭐⭐⭐ | MEDIUM |
| Task Checklists | `SPEC_TASK_ENHANCEMENT_PART2.md` Section 5 | ⭐⭐ | MEDIUM |

### CRM Module

| Feature | File Spec | Complexity | Priority |
|---------|-----------|------------|----------|
| Customer CRUD | `SPEC_CRM_MODULE.md` Section 2 | ⭐⭐ | HIGH |
| Customer Search/Filter | `SPEC_CRM_MODULE.md` Section 2 | ⭐⭐⭐ | HIGH |
| Interactions | `SPEC_CRM_MODULE_PART2.md` Section 3 | ⭐⭐ | HIGH |
| Care Scenarios | `SPEC_CRM_MODULE_PART2.md` Section 4 | ⭐⭐⭐⭐⭐ | MEDIUM |
| Message Templates | `SPEC_CRM_MODULE_PART2.md` Section 5 | ⭐⭐ | MEDIUM |
| Quotations | `SPEC_CRM_MODULE_PART2.md` Section 6 | ⭐⭐⭐ | LOW |

---

## 🎨 UI/UX MOCKUPS

Tất cả mockups được viết bằng ASCII art trong spec files, rất dễ hiểu cho AI.

**Ví dụ:**
- Customer Dashboard → `SPEC_CRM_MODULE.md` Section 2.1
- Customer Detail → `SPEC_CRM_MODULE.md` Section 2.2
- Task Templates List → `SPEC_TASK_ENHANCEMENT.md` Section 2.2
- Create Task from Template → `SPEC_TASK_ENHANCEMENT.md` Section 2.2

AI có thể convert các mockups này sang HTML/CSS/JavaScript.

---

## 🔗 INTEGRATION POINTS

### Tasks ↔ CRM
```python
# Khi tạo customer → Auto tạo follow-up task
def create_customer(customer_data):
    customer_id = # ... create customer

    # Trigger scenario
    if customer_data['lead_source'] == 'website':
        scenario_manager.start_scenario(customer_id, 'scenario_website_lead')
        # Scenario sẽ auto tạo task: "Gọi điện cho khách trong 2h"
```

### Tasks ↔ Notifications
```python
# Khi task completed → Notify dependent tasks
def update_task_status(task_id, status):
    # ... update status

    if status == 'completed':
        # Notify tasks đang chờ task này
        dependency_manager.notify_unblocked_tasks(task_id)
```

### CRM ↔ Notifications
```python
# Scenario auto gửi messages
def execute_scenario_step(customer_id, step):
    if step['step_type'] == 'auto_message':
        # Send Zalo/Telegram/Email từ template
        template_manager.use_template(
            step['template_id'],
            customer_id
        )
```

---

## 📈 EXPECTED OUTCOMES

Sau khi implement xong:

### User Experience
✅ Sales dễ dàng quản lý hàng trăm khách hàng
✅ Không bỏ lỡ follow-up nào nhờ automation
✅ Tạo tasks nhanh chóng từ templates
✅ Tracking đầy đủ lịch sử tương tác khách hàng
✅ Báo cáo chi tiết, dễ xuất Excel

### Business Value
✅ Tăng conversion rate nhờ follow-up đúng lúc
✅ Giảm thời gian training nhân viên mới (có templates)
✅ Tăng năng suất sales team (automation)
✅ Quản lý công trình chặt chẽ hơn
✅ Tích hợp bán hàng online/offline trên một nền tảng

---

## ⚠️ LƯU Ý QUAN TRỌNG

### 1. Database Compatibility
- Tất cả spec được viết cho **SQLite**
- Nếu dùng PostgreSQL/MySQL, cần modify:
  - TEXT → VARCHAR(...)
  - BOOLEAN → TINYINT hoặc BOOL
  - JSON handling khác

### 2. Dependencies
```bash
# Đảm bảo đã cài:
pip install flask==3.0.0
pip install python-telegram-bot==20.7
pip install pyrebase4==4.9.0
# ... xem đầy đủ trong requirements.txt
```

### 3. Configuration
- Cần config Telegram Bot Token
- Cần config Zalo OA credentials
- Cần config Email SMTP
- Xem file `config/config.json`

### 4. Permissions
- Tất cả features mới cần thêm permissions
- Ví dụ: `calendar-tools:customer.view`, `calendar-tools:customer.create`
- Seed trong migration

---

## 🤝 COLLABORATION

### Nếu làm việc theo team

**Backend Developer:**
- Đọc: `SPEC_*.md` → Implement managers
- Test: Viết test functions
- Commit: Từng manager một

**Frontend Developer:**
- Đọc: UI Mockups trong spec
- Implement: HTML templates + routes
- Integrate: Gọi API endpoints

**QA/Tester:**
- Đọc: Testing sections trong `IMPLEMENTATION_GUIDE.md`
- Test: Từng feature theo checklist
- Report: Bugs qua issue tracker

---

## 📞 SUPPORT & QUESTIONS

Nếu có câu hỏi khi implement:

1. **Check lại spec:** 99% câu hỏi đã có answer trong spec
2. **Xem sample data:** Hiểu flow qua sample data
3. **Đọc algorithm comments:** Mỗi function đều có algorithm mô tả
4. **Test với data nhỏ:** Tạo test database, test với 2-3 records trước

---

## 🎯 QUICK START

**Muốn bắt đầu ngay?**

### Option 1: Task Templates (Đơn giản nhất)
```bash
# 1. Copy spec
cat SPEC_TASK_ENHANCEMENT.md | grep -A 200 "task_templates"

# 2. Paste vào AI, yêu cầu:
"Viết code Python cho TaskTemplateManager"

# 3. Run test
python3 backend/task_management/task_template_manager.py

# 4. Nếu OK → Integrate vào app.py
```

### Option 2: Customer Management (Quan trọng nhất)
```bash
# 1. Copy spec
cat SPEC_CRM_MODULE.md | grep -A 500 "customers"

# 2. Paste vào AI
"Viết migration script + CustomerManager class"

# 3. Test CRUD operations
python3 backend/crm/customer_manager.py

# 4. Build UI
```

---

## 📚 ADDITIONAL RESOURCES

### Related Files
- `database/calendar_tools.db` - Database hiện tại
- `backend/task_management/simple_task_manager.py` - Task manager hiện có
- `frontend/app.py` - Flask routes hiện có
- `migrations/` - Migration scripts hiện có

### External References
- Flask Documentation: https://flask.palletsprojects.com/
- SQLite Documentation: https://www.sqlite.org/docs.html
- Python Telegram Bot: https://python-telegram-bot.org/

---

## ✅ CHECKLIST HOÀN THÀNH

Sau khi implement xong tất cả:

### Backend
- [ ] 4 Task enhancement managers
- [ ] 5 CRM managers
- [ ] All migrations run successfully
- [ ] All tests pass

### Frontend
- [ ] Task Templates UI
- [ ] Recurring Tasks UI
- [ ] Customer Dashboard
- [ ] Customer Detail
- [ ] Scenarios UI

### Integration
- [ ] Customer → Task linking works
- [ ] Scenarios trigger correctly
- [ ] Notifications send properly
- [ ] Permissions enforce correctly

### Deployment
- [ ] Staging environment tested
- [ ] Cron jobs setup
- [ ] Backup strategy in place
- [ ] Documentation updated
- [ ] Production deployed

---

**🎉 Chúc bạn implement thành công!**

Nếu cần hỗ trợ thêm, hãy đọc lại các file spec - chúng đã được viết CỰC KỲ CHI TIẾT để AI có thể hiểu và code ngay.

---

**Version:** 1.0
**Last Updated:** 01/11/2025
**Author:** Claude Code Agent
**License:** Private - Hunonic Internal Use Only

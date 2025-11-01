# HƯỚNG DẪN MIGRATION UI SANG ADMINLTE 3

## Tổng quan

Dự án hiện tại đang dùng:
- ✅ Flask + Jinja2 templates (server-side rendering)
- ✅ Bootstrap 5.1.3 + custom CSS
- ✅ Font Awesome 6.0

Sau khi migration sẽ dùng:
- ✅ Flask + Jinja2 templates (giữ nguyên)
- ✅ AdminLTE 3 (professional admin template)
- ✅ Bootstrap 4 (AdminLTE base)
- ✅ Font Awesome 6.0 (giữ nguyên)
- ✅ Hunonic custom theme (màu xanh #01af32)

---

## Phần 1: Các file đã tạo sẵn (đã hoàn thành)

### 1. Base Template mới: `base_adminlte.html`
**Vị trí**: `frontend/templates/base_adminlte.html`

**Chức năng**:
- Sidebar menu với cấu trúc phân cấp
- Top navbar với user dropdown
- Content wrapper với breadcrumb
- Footer
- Flash messages tự động
- Responsive layout

**Cấu trúc blocks**:
```jinja2
{% block title %}{% endblock %}          - Tiêu đề trang
{% block page_title %}{% endblock %}     - H1 trong content header
{% block breadcrumb %}{% endblock %}     - Breadcrumb navigation
{% block content %}{% endblock %}        - Nội dung chính
{% block extra_css %}{% endblock %}      - CSS riêng của trang
{% block extra_js %}{% endblock %}       - JS riêng của trang
```

### 2. Hunonic Theme CSS: `hunonic-theme.css`
**Vị trí**: `frontend/static/css/hunonic-theme.css`

**Tùy chỉnh**:
- Màu chủ đạo: `#01af32` (Hunonic green)
- Sidebar: Dark theme với Hunonic branding
- Buttons: Primary buttons màu xanh Hunonic
- Cards: Border-top màu xanh
- Forms: Focus state màu xanh
- Status badges: Pending/Completed/Overdue
- Priority badges: High/Medium/Low

### 3. Dashboard mẫu: `index_adminlte.html`
**Vị trí**: `frontend/templates/index_adminlte.html`

**Components đã dùng**:
- Small boxes (stat cards)
- Info boxes
- Cards với header/footer
- Badges
- Buttons

---

## Phần 2: Cách migrate từng trang

### Bước 1: Chuyển đổi base template

**File cũ**:
```jinja2
{% extends "base.html" %}
{% block title %}Tiêu đề{% endblock %}
{% block content %}
  <!-- Nội dung -->
{% endblock %}
```

**File mới**:
```jinja2
{% extends "base_adminlte.html" %}
{% block title %}Tiêu đề{% endblock %}
{% block page_title %}Tiêu đề Trang{% endblock %}

{% block breadcrumb %}
<li class="breadcrumb-item"><a href="/">Trang chủ</a></li>
<li class="breadcrumb-item active">Tiêu đề</li>
{% endblock %}

{% block content %}
  <!-- Nội dung -->
{% endblock %}
```

### Bước 2: Chuyển đổi components

#### A. Tables (ví dụ: tasks_list.html)

**Cũ** (Bootstrap 5 basic):
```html
<table class="table table-striped">
  <thead>
    <tr><th>Cột 1</th></tr>
  </thead>
  <tbody>
    <tr><td>Data</td></tr>
  </tbody>
</table>
```

**Mới** (AdminLTE DataTable):
```html
<div class="card">
  <div class="card-header">
    <h3 class="card-title">Danh sách</h3>
    <div class="card-tools">
      <button class="btn btn-sm btn-primary">
        <i class="fas fa-plus"></i> Thêm mới
      </button>
    </div>
  </div>
  <div class="card-body">
    <table id="myTable" class="table table-bordered table-hover">
      <thead>
        <tr><th>Cột 1</th></tr>
      </thead>
      <tbody>
        <tr><td>Data</td></tr>
      </tbody>
    </table>
  </div>
</div>

<!-- Thêm vào extra_js -->
{% block extra_js %}
<link rel="stylesheet" href="https://cdn.datatables.net/1.11.5/css/dataTables.bootstrap4.min.css">
<script src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>
<script src="https://cdn.datatables.net/1.11.5/js/dataTables.bootstrap4.min.js"></script>
<script>
  $(document).ready(function() {
    $('#myTable').DataTable({
      "language": {
        "url": "//cdn.datatables.net/plug-ins/1.11.5/i18n/vi.json"
      }
    });
  });
</script>
{% endblock %}
```

#### B. Forms (ví dụ: create_task.html)

**Cũ**:
```html
<form>
  <div class="mb-3">
    <label>Tiêu đề</label>
    <input type="text" class="form-control">
  </div>
</form>
```

**Mới**:
```html
<div class="card card-primary">
  <div class="card-header">
    <h3 class="card-title">Tạo Task Mới</h3>
  </div>
  <form method="POST">
    <div class="card-body">
      <div class="form-group">
        <label for="title">Tiêu đề</label>
        <input type="text" class="form-control" id="title" name="title" placeholder="Nhập tiêu đề">
      </div>
    </div>
    <div class="card-footer">
      <button type="submit" class="btn btn-primary">
        <i class="fas fa-save"></i> Lưu
      </button>
      <a href="/" class="btn btn-default">
        <i class="fas fa-times"></i> Hủy
      </a>
    </div>
  </form>
</div>
```

#### C. Stat Cards (Dashboard)

**Mới** (Small Boxes):
```html
<div class="row">
  <div class="col-lg-3 col-6">
    <div class="small-box bg-primary">
      <div class="inner">
        <h3>150</h3>
        <p>Tasks hoàn thành</p>
      </div>
      <div class="icon">
        <i class="fas fa-tasks"></i>
      </div>
      <a href="#" class="small-box-footer">
        Xem thêm <i class="fas fa-arrow-circle-right"></i>
      </a>
    </div>
  </div>
</div>
```

#### D. Alert Messages

**Cũ**:
```html
<div class="alert alert-success">Thành công!</div>
```

**Mới** (với icon):
```html
<div class="alert alert-success alert-dismissible">
  <button type="button" class="close" data-dismiss="alert">&times;</button>
  <h5><i class="icon fas fa-check"></i> Thành công!</h5>
  Thao tác đã được thực hiện.
</div>
```

#### E. Buttons

**Cũ**:
```html
<button class="btn btn-primary">Click me</button>
```

**Mới** (với icon):
```html
<button class="btn btn-primary">
  <i class="fas fa-save"></i> Lưu
</button>
<button class="btn btn-outline-primary">
  <i class="fas fa-edit"></i> Sửa
</button>
```

---

## Phần 3: Danh sách trang cần migrate

### Ưu tiên cao (Core pages)

1. **index.html** → **index_adminlte.html** ✅ (Đã làm mẫu)
2. **tasks_list.html** → Cần migrate
3. **create_simple_task.html** → Cần migrate
4. **task_detail.html** → Cần migrate
5. **report_tasks.html** → Cần migrate

### Ưu tiên trung bình (Secondary pages)

6. **calendar_tools_home.html** → Cần migrate
7. **profile_settings.html** → Cần migrate
8. **admin_users.html** → Cần migrate
9. **admin_groups.html** → Cần migrate

### Ưu tiên thấp (Auth pages - giữ đơn giản)

10. **login.html** → Có thể dùng AdminLTE login template
11. **register.html** → Có thể dùng AdminLTE register template

---

## Phần 4: Quy trình migration từng trang

### Template để migrate nhanh:

```bash
# Bước 1: Copy file gốc
cp frontend/templates/ten_trang.html frontend/templates/ten_trang_adminlte.html

# Bước 2: Sửa extends
# Đổi: {% extends "base.html" %}
# Thành: {% extends "base_adminlte.html" %}

# Bước 3: Thêm blocks mới
# - page_title
# - breadcrumb

# Bước 4: Wrap content vào cards
# - Đổi <div class="container"> thành cards
# - Thêm card-header, card-body, card-footer

# Bước 5: Cập nhật buttons
# - Thêm icons vào buttons
# - Đổi class me-2 (BS5) thành mr-2 (BS4)

# Bước 6: Test
# - Chạy Flask app
# - Kiểm tra responsive
# - Kiểm tra màu sắc Hunonic

# Bước 7: Update route trong app.py
# Đổi render_template('ten_trang.html')
# Thành render_template('ten_trang_adminlte.html')
```

---

## Phần 5: AdminLTE Components nên dùng

### 1. Cards (dùng nhiều nhất)
```html
<div class="card card-primary card-outline">
  <div class="card-header">
    <h3 class="card-title">Title</h3>
    <div class="card-tools">
      <!-- Buttons -->
    </div>
  </div>
  <div class="card-body">
    <!-- Content -->
  </div>
  <div class="card-footer">
    <!-- Footer actions -->
  </div>
</div>
```

### 2. Info Boxes (stats nhỏ)
```html
<div class="info-box">
  <span class="info-box-icon bg-primary"><i class="fas fa-tasks"></i></span>
  <div class="info-box-content">
    <span class="info-box-text">Tasks</span>
    <span class="info-box-number">150</span>
  </div>
</div>
```

### 3. DataTables (tables có search/sort)
- Docs: https://datatables.net/
- CDN đã có trong hướng dẫn trên
- Hỗ trợ tiếng Việt

### 4. Charts (nếu cần báo cáo)
- ChartJS: https://www.chartjs.org/
```html
<canvas id="myChart"></canvas>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
  const ctx = document.getElementById('myChart').getContext('2d');
  new Chart(ctx, { /* config */ });
</script>
```

### 5. Toastr (notifications đẹp hơn alert())
```html
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/toastr.js/latest/toastr.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/toastr.js/latest/toastr.min.js"></script>
<script>
  toastr.success('Lưu thành công!');
  toastr.error('Có lỗi xảy ra!');
</script>
```

---

## Phần 6: Cập nhật Flask routes

### File: `frontend/app.py`

**Đã cập nhật**:
```python
@app.route('/')
def index():
    return render_template('index_adminlte.html')  # ✅ Đã đổi
```

**Cần cập nhật**:
```python
@app.route('/tasks')
def view_tasks():
    # return render_template('tasks_list.html')  # ❌ Cũ
    return render_template('tasks_list_adminlte.html')  # ✅ Mới

@app.route('/create_task')
def create_simple_task():
    # return render_template('create_simple_task.html')  # ❌ Cũ
    return render_template('create_simple_task_adminlte.html')  # ✅ Mới

# ... tương tự cho các routes khác
```

---

## Phần 7: Checklist Migration

### Phase 1: Core Setup (✅ Hoàn thành)
- [x] Tạo `base_adminlte.html`
- [x] Tạo `hunonic-theme.css`
- [x] Tạo `index_adminlte.html` (mẫu)
- [x] Update route `/` trong app.py

### Phase 2: Task Management Pages (Cần làm)
- [ ] Migrate `tasks_list.html`
  - [ ] Wrap table vào card
  - [ ] Thêm DataTables
  - [ ] Update inline editing
  - [ ] Test save/delete/test buttons
- [ ] Migrate `create_simple_task.html`
  - [ ] Form trong card
  - [ ] Datetime pickers
  - [ ] Validation styling
- [ ] Migrate `task_detail.html`
  - [ ] Detail view trong card
  - [ ] Action buttons
  - [ ] Comments section
- [ ] Migrate `report_tasks.html`
  - [ ] Charts với ChartJS
  - [ ] Filter form trong card
  - [ ] Export buttons

### Phase 3: Admin Pages (Cần làm)
- [ ] Migrate `admin_users.html`
- [ ] Migrate `admin_groups.html`
- [ ] Migrate `admin_*_matrix.html` pages

### Phase 4: Settings & Auth (Cần làm)
- [ ] Migrate `profile_settings.html`
- [ ] Migrate `login.html` (optional: dùng AdminLTE template)
- [ ] Migrate `register.html` (optional)

### Phase 5: Testing & Cleanup
- [ ] Test toàn bộ pages trên desktop
- [ ] Test responsive trên mobile
- [ ] Test các chức năng CRUD
- [ ] Test notification systems
- [ ] Remove old templates (sau khi confirm mọi thứ OK)
- [ ] Remove `base.html` và `style.css` cũ

---

## Phần 8: Tips & Best Practices

### 1. Bootstrap 4 vs 5 differences
AdminLTE dùng Bootstrap 4, project cũ dùng Bootstrap 5:

| Bootstrap 5 | Bootstrap 4 | Note |
|-------------|-------------|------|
| `ms-2, me-2` | `ml-2, mr-2` | Margin left/right |
| `start-0, end-0` | `left-0, right-0` | Position |
| `data-bs-toggle` | `data-toggle` | Data attributes |
| `btn-close` | `close` | Close button |

### 2. Giữ nguyên logic backend
- **KHÔNG** cần sửa Python code
- **KHÔNG** cần sửa database
- **CHỈ** sửa HTML templates và CSS

### 3. Test từng trang
Sau khi migrate mỗi trang:
```bash
# Chạy Flask
python3 frontend/app.py

# Test checklist:
# ✓ Layout hiển thị đúng
# ✓ Sidebar menu hoạt động
# ✓ Buttons có icons
# ✓ Forms submit được
# ✓ CRUD operations hoạt động
# ✓ Flash messages hiển thị
# ✓ Responsive trên mobile
# ✓ Màu Hunonic đúng (#01af32)
```

### 4. Tùy chỉnh màu Hunonic
Nếu cần thêm màu:
```css
/* Thêm vào hunonic-theme.css */
.my-custom-class {
    background-color: var(--hunonic-green);
    color: white;
}
```

### 5. Sidebar menu cần cập nhật
Khi thêm trang mới, update menu trong `base_adminlte.html`:
```html
<li class="nav-item">
  <a href="{{ url_for('new_page') }}" class="nav-link">
    <i class="nav-icon fas fa-icon"></i>
    <p>Trang Mới</p>
  </a>
</li>
```

---

## Phần 9: Tài liệu tham khảo

### AdminLTE 3
- Docs: https://adminlte.io/docs/3.2/
- Demo: https://adminlte.io/themes/v3/
- Components: https://adminlte.io/themes/v3/pages/UI/general.html
- GitHub: https://github.com/ColorlibHQ/AdminLTE

### DataTables
- Docs: https://datatables.net/
- Examples: https://datatables.net/examples/

### ChartJS
- Docs: https://www.chartjs.org/docs/latest/
- Examples: https://www.chartjs.org/docs/latest/samples/

### Font Awesome
- Icons: https://fontawesome.com/icons
- Search icons: https://fontawesome.com/search

---

## Phần 10: Timeline ước tính

### Nếu làm full-time (8h/ngày):
- **Week 1**: Core task pages (tasks_list, create, detail, report) - 3-4 ngày
- **Week 2**: Admin pages + Settings - 2-3 ngày
- **Week 3**: Testing + Bug fixes - 2 ngày

**Tổng: 2-3 tuần**

### Nếu làm part-time (2h/ngày):
- **Week 1-2**: Core task pages
- **Week 3-4**: Admin pages + Settings
- **Week 5**: Testing + Bug fixes

**Tổng: 5-6 tuần**

---

## Phần 11: Các lỗi thường gặp & Cách fix

### Lỗi 1: Sidebar không collapse
**Nguyên nhân**: Thiếu jQuery hoặc AdminLTE JS
**Fix**: Kiểm tra trong `base_adminlte.html` có đầy đủ scripts:
```html
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.0/dist/js/bootstrap.bundle.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/admin-lte@3.2/dist/js/adminlte.min.js"></script>
```

### Lỗi 2: DataTable không hiển thị
**Nguyên nhân**: Chưa load DataTables JS/CSS
**Fix**: Thêm vào `extra_js` block (xem hướng dẫn Part 2)

### Lỗi 3: Màu Hunonic không hiển thị
**Nguyên nhân**: CSS load sai thứ tự
**Fix**: Đảm bảo `hunonic-theme.css` load sau AdminLTE CSS

### Lỗi 4: Layout bị vỡ trên mobile
**Nguyên nhân**: Chưa responsive
**Fix**: Dùng AdminLTE grid classes:
```html
<div class="col-lg-6 col-md-12">...</div>
```

---

## KẾT LUẬN

Migration sang AdminLTE 3 là giải pháp TỐI ƯU vì:
- ✅ Không thay đổi kiến trúc (vẫn Flask + Jinja2)
- ✅ Không cần học React/Vue
- ✅ 1000+ components sẵn dùng
- ✅ Responsive mặc định
- ✅ Cộng đồng lớn, tài liệu đầy đủ
- ✅ Professional UI ngay lập tức
- ✅ Dễ tùy chỉnh theo Hunonic brand

**KHÔNG nên dùng MUI** vì:
- ❌ Cần React (thay đổi toàn bộ kiến trúc)
- ❌ Tốn 2-3 tháng refactor
- ❌ Phức tạp hơn rất nhiều
- ❌ Không phù hợp với Flask templates

---

**Bắt đầu từ đâu?**

1. Review các file đã tạo:
   - `base_adminlte.html`
   - `hunonic-theme.css`
   - `index_adminlte.html`

2. Migrate trang đầu tiên: `tasks_list.html`
   - Copy file thành `tasks_list_adminlte.html`
   - Theo template trong Part 2
   - Update route trong `app.py`
   - Test kỹ

3. Lặp lại cho các trang khác theo checklist Phase 2, 3, 4

**Cần hỗ trợ gì thêm?**
- Migrate specific page?
- Giải thích component nào?
- Fix lỗi cụ thể?

Cứ hỏi nhé! 🚀

#!/bin/bash

echo "🧹 Bắt đầu cleanup templates cũ..."

TEMPLATES_DIR="frontend/templates"

FILES_TO_DELETE=(
    "403.html"
    "admin_group_matrix.html"
    "admin_group_members_matrix.html"
    "admin_group_tools_matrix.html"
    "admin_groups.html"
    "admin_user_matrix.html"
    "admin_user_tools_matrix.html"
    "admin_users.html"
    "calendar_tools_home.html"
    "create_simple_task.html"
    "create_task.html"
    "login.html"
    "profile_settings.html"
    "register.html"
    "report_tasks.html"
    "task_detail.html"
    "tasks_list.html"
    "user_report.html"
)

DELETED_COUNT=0
NOT_FOUND_COUNT=0

for file in "${FILES_TO_DELETE[@]}"; do
    filepath="${TEMPLATES_DIR}/${file}"
    if [ -f "$filepath" ]; then
        rm "$filepath"
        echo "✅ Đã xóa: $filepath"
        ((DELETED_COUNT++))
    else
        echo "⚠️  Không tìm thấy: $filepath"
        ((NOT_FOUND_COUNT++))
    fi
done

echo ""
echo "📊 Kết quả:"
echo "   - Đã xóa: $DELETED_COUNT files"
echo "   - Không tìm thấy: $NOT_FOUND_COUNT files"
echo ""
echo "✅ Cleanup hoàn tất!"

#!/bin/bash

echo "🧹 Cleanup CSS files..."

# Backup style.css trước khi xóa
if [ -f "frontend/static/css/style.css" ]; then
    echo "📦 Backup style.css..."
    cp frontend/static/css/style.css frontend/static/css/style.css.backup
fi

# Xóa các phần CSS đã được thay thế bằng AdminLTE
# Giữ lại chỉ CSS variables nếu cần

cat > frontend/static/css/style.css << 'EOF'
/* Hunonic Branding CSS Variables - Keep for consistency */
:root {
    --primary-color: #01af32;
    --primary-dark: #018a28;
    --primary-light: #4ecb71;
    --secondary-color: #ff6b35;
    --secondary-dark: #e55a2b;
    --accent-color: #4ecdc4;
    --background-color: #f8fff9;
    --text-color: #333;
    --text-light: #666;
    --border-color: #e0f0e0;
    --shadow-color: rgba(1, 175, 50, 0.1);
    --gradient-primary: linear-gradient(135deg, #01af32, #4ecb71);
    --gradient-secondary: linear-gradient(135deg, #ff6b35, #ff8c5a);
}

/* All other styles moved to AdminLTE custom CSS and page-specific CSS files */
EOF

echo "✅ CSS cleanup completed!"
echo "📝 style.css.backup created for reference"
#!/bin/bash

# Cleanup and Backup Script
# Xóa backup cũ và backup lại với .gitignore

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "${YELLOW}Cleaning up old backups...${NC}"

# Xóa backup cũ
rm -rf /Users/AmyNguyen/Desktop/backup-repos
rm -f /Users/AmyNguyen/Desktop/multi_backup.log

echo "${GREEN}Old backups cleaned up!${NC}"

# Tạo .gitignore cho calendar-tools nếu chưa có
if [ ! -f "/Users/AmyNguyen/Desktop/Cursor AI MKT/calendar-tools/.gitignore" ]; then
    echo "${YELLOW}Creating .gitignore for calendar-tools...${NC}"
    cat > "/Users/AmyNguyen/Desktop/Cursor AI MKT/calendar-tools/.gitignore" << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Database files
*.db
*.sqlite
*.sqlite3
database/*.db

# Logs
*.log
logs/
*.log.*

# Environment variables
.env
.venv
env/
venv/

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Temporary files
*.tmp
*.temp
*.bak
*.backup

# Node modules (if any)
node_modules/

# Backup directories
backup-repos/
backup-*/

# Test files
test_*.py
*_test.py

# Config files with sensitive data
config/google_credentials.json
config/*.key
config/*.pem

# Runtime files
*.pid
*.sock
EOF
    echo "${GREEN}.gitignore created for calendar-tools!${NC}"
fi

# Tạo .gitignore cho hunonic-banner-tools nếu chưa có
if [ ! -f "/Users/AmyNguyen/Desktop/Cursor AI MKT/hunonic-banner-tools/.gitignore" ]; then
    echo "${YELLOW}Creating .gitignore for hunonic-banner-tools...${NC}"
    cat > "/Users/AmyNguyen/Desktop/Cursor AI MKT/hunonic-banner-tools/.gitignore" << 'EOF'
# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Build outputs
dist/
build/
out/

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
*.log
logs/

# Temporary files
*.tmp
*.temp
*.bak
*.backup

# Cache
.cache/
.parcel-cache/

# Runtime files
*.pid
*.sock
EOF
    echo "${GREEN}.gitignore created for hunonic-banner-tools!${NC}"
fi

echo "${YELLOW}Starting clean backup...${NC}"

# Chạy backup
./multi_project_backup.sh backup

echo "${GREEN}Clean backup completed!${NC}"
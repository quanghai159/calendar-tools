#!/bin/bash
# restore_pre_migration.sh
# Restore từ pre-migration backup

set -e

PROJECT_DIR="/Users/AmyNguyen/Desktop/Cursor AI MKT/calendar-tools"
BACKUP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GIT_TAG=$(grep "Git Tag:" "$BACKUP_DIR/BACKUP_INFO.txt" | cut -d' ' -f3)

cd "$PROJECT_DIR"

echo "🔄 Restoring from Pre-Migration Backup..."
echo "📁 Backup Directory: $BACKUP_DIR"
echo "🏷️  Git Tag: $GIT_TAG"
echo ""

read -p "⚠️  This will overwrite current code. Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Restore cancelled"
    exit 1
fi

# 1. Restore code from Git tag
echo "📦 Step 1: Restoring code from Git tag..."
git fetch origin
git checkout "$GIT_TAG"
echo "✅ Code restored"

# 2. Restore database
echo ""
echo "💾 Step 2: Restoring database..."
if [ -f "$BACKUP_DIR/calendar_tools.db.backup" ]; then
    cp "$BACKUP_DIR/calendar_tools.db.backup" "database/calendar_tools.db"
    echo "✅ Database restored"
else
    echo "⚠️  Database backup not found"
fi

echo ""
echo "✅ Restore completed!"
echo "📋 You are now on Git tag: $GIT_TAG"
echo "💡 To create a new branch: git checkout -b restore-branch"

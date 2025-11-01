#!/bin/bash
# pre_migration_backup.sh
# Backup trước khi migrate sang AdminLTE

set -e  # Exit on error

PROJECT_DIR="/Users/AmyNguyen/Desktop/Cursor AI MKT/calendar-tools"
BACKUP_DIR="$PROJECT_DIR/pre-migration-backup-$(date +%Y%m%d-%H%M%S)"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
GIT_TAG="pre-adminlte-migration-$(date +%Y%m%d-%H%M%S)"

cd "$PROJECT_DIR"

echo "🔄 Starting Pre-Migration Backup..."
echo "📁 Project: $PROJECT_DIR"
echo "📅 Timestamp: $TIMESTAMP"
echo "🏷️  Git Tag: $GIT_TAG"
echo ""

# 1. Kiểm tra Git status
echo "📋 Step 1: Checking Git status..."
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Warning: You have uncommitted changes!"
    echo "   Files:"
    git status --short
    read -p "   Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Backup cancelled"
        exit 1
    fi
fi

# 2. Commit mọi thay đổi hiện tại (nếu có)
echo ""
echo "📝 Step 2: Committing current changes..."
git add -A
if [ -n "$(git diff --staged)" ]; then
    git commit -m "Pre-migration backup: Save current state before AdminLTE migration - $TIMESTAMP"
    echo "✅ Changes committed"
else
    echo "✅ No changes to commit"
fi

# 3. Tạo Git tag
echo ""
echo "🏷️  Step 3: Creating Git tag..."
git tag -a "$GIT_TAG" -m "Pre-migration backup point before AdminLTE migration - $TIMESTAMP"
echo "✅ Tag created: $GIT_TAG"

# 4. Push code + tag lên GitHub
echo ""
echo "🚀 Step 4: Pushing to GitHub..."
git push origin main
git push origin "$GIT_TAG"
echo "✅ Code pushed to GitHub with tag"

# 5. Backup database
echo ""
echo "💾 Step 5: Backing up database..."
mkdir -p "$BACKUP_DIR"
DB_PATH="database/calendar_tools.db"
if [ -f "$DB_PATH" ]; then
    DB_BACKUP="$BACKUP_DIR/calendar_tools.db.backup"
    cp "$DB_PATH" "$DB_BACKUP"
    echo "✅ Database backed up: $DB_BACKUP"
    
    # Get database size
    DB_SIZE=$(du -h "$DB_BACKUP" | cut -f1)
    echo "   Database size: $DB_SIZE"
else
    echo "⚠️  Database not found: $DB_PATH"
fi

# 6. Tạo backup info file
echo ""
echo "📄 Step 6: Creating backup info..."
cat > "$BACKUP_DIR/BACKUP_INFO.txt" <<EOF
PRE-MIGRATION BACKUP INFORMATION
================================
Backup Date: $TIMESTAMP
Git Tag: $GIT_TAG
Project: calendar-tools
Purpose: Backup before AdminLTE migration

RESTORE INSTRUCTIONS:
=====================

1. Restore from Git Tag:
   git checkout $GIT_TAG
   git checkout -b restore-$GIT_TAG

2. Restore Database:
   cp $BACKUP_DIR/calendar_tools.db.backup database/calendar_tools.db

3. Restore Code from GitHub:
   git fetch origin
   git checkout $GIT_TAG

4. Full Restore Script:
   Run: ./restore_pre_migration.sh
EOF

echo "✅ Backup info created"

# 7. Tạo restore script
echo ""
echo "📝 Step 7: Creating restore script..."
cat > "$BACKUP_DIR/restore_pre_migration.sh" <<'RESTORE_SCRIPT'
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
RESTORE_SCRIPT

chmod +x "$BACKUP_DIR/restore_pre_migration.sh"
echo "✅ Restore script created"

# 8. Summary
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ PRE-MIGRATION BACKUP COMPLETED!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "📋 Backup Summary:"
echo "   Git Tag: $GIT_TAG"
echo "   Backup Directory: $BACKUP_DIR"
echo "   Database Backup: $BACKUP_DIR/calendar_tools.db.backup"
echo "   Restore Script: $BACKUP_DIR/restore_pre_migration.sh"
echo ""
echo "🔍 Verify backup:"
echo "   git tag -l | grep pre-adminlte"
echo "   ls -lh $BACKUP_DIR"
echo ""
echo "📖 To restore:"
echo "   cd $BACKUP_DIR"
echo "   ./restore_pre_migration.sh"
echo ""
echo "🎯 You can now safely proceed with AdminLTE migration!"
echo ""

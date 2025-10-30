#!/bin/bash

# Multi-Project Auto Backup Script
# Backup multiple projects to their respective GitHub repositories

# Configuration
LOG_FILE="/Users/AmyNguyen/Desktop/multi_backup.log"
BACKUP_DIR="/Users/AmyNguyen/Desktop/backup-repos"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to backup single project
backup_project() {
    local project_name="$1"
    local source_dir="$2"
    local git_url="$3"
    local backup_repo_dir="$BACKUP_DIR/$project_name"
    
    log "${BLUE}Backing up $project_name...${NC}"
    
    # Create backup directory if not exists
    if [ ! -d "$backup_repo_dir" ]; then
        log "Creating backup directory: $backup_repo_dir"
        mkdir -p "$backup_repo_dir"
        cd "$backup_repo_dir"
        git init
        git branch -M main  # Thêm dòng này
        git remote add origin "$git_url"
    else
        cd "$backup_repo_dir"
    fi
    
    # Copy files (exclude common unwanted files)
rsync -av --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='.DS_Store' --exclude='node_modules' --exclude='*.log' --exclude='*.tmp' --exclude='.env' --exclude='database/*.db' --exclude='backup-repos' --exclude='test_*.py' --exclude='*_test.py' "$source_dir/" "$backup_repo_dir/"
    
    # Add all files
    git add .
    
    # Check if there are changes
    if git diff --staged --quiet; then
        log "${YELLOW}No changes to commit for $project_name${NC}"
        return 0
    fi
    
    # Commit with timestamp
    COMMIT_MSG="Auto backup $(date '+%Y-%m-%d %H:%M:%S') - $project_name"
    git commit -m "$COMMIT_MSG"
    
    # Push to GitHub
    log "Pushing $project_name to GitHub..."
    if git push origin main; then
        log "${GREEN}Backup $project_name completed successfully!${NC}"
        return 0
    else
        log "${RED}Backup $project_name failed!${NC}"
        return 1
    fi
}

# Function to backup all projects
backup_all_projects() {
    log "${YELLOW}Starting multi-project backup...${NC}"
    
    # Project configurations (array format)
    PROJECTS=(
        "hunonic-banner-tools|/Users/AmyNguyen/Desktop/Cursor AI MKT/hunonic-banner-tools|https://github.com/quanghai159/hunonic-banner-tools.git"
        "calendar-tools|/Users/AmyNguyen/Desktop/Cursor AI MKT/calendar-tools|https://github.com/quanghai159/calendar-tools.git"
    )
    
    local success_count=0
    local total_count=${#PROJECTS[@]}
    
    # Backup each project
    for project_info in "${PROJECTS[@]}"; do
        IFS='|' read -r project_name source_dir git_url <<< "$project_info"
        
        if [ -d "$source_dir" ]; then
            if backup_project "$project_name" "$source_dir" "$git_url"; then
                ((success_count++))
            fi
        else
            log "${RED}Source directory not found: $source_dir${NC}"
        fi
    done
    
    log "${GREEN}Multi-project backup completed: $success_count/$total_count projects successful${NC}"
}

# Function to run continuous backup
run_continuous() {
    log "${GREEN}Starting continuous multi-project backup (every 30 minutes)...${NC}"
    log "Press Ctrl+C to stop"
    
    while true; do
        backup_all_projects
        log "Waiting 30 minutes for next backup..."
        sleep 1800  # 30 minutes
    done
}

# Function to add new project
add_project() {
    local project_name="$1"
    local source_dir="$2"
    local git_url="$3"
    
    log "${YELLOW}Adding new project: $project_name${NC}"
    
    # Add to PROJECTS array (this would need to be done manually in the script)
    log "To add this project permanently, edit the PROJECTS array in the script:"
    log "[\"$project_name\"]=\"$source_dir|$git_url\""
    
    # Test backup
    if [ -d "$source_dir" ]; then
        backup_project "$project_name" "$source_dir" "$git_url"
    else
        log "${RED}Source directory not found: $source_dir${NC}"
    fi
}

# Main script
case "$1" in
    "backup")
        backup_all_projects
        ;;
    "run")
        run_continuous
        ;;
    "add")
        if [ $# -ne 4 ]; then
            echo "Usage: $0 add <project_name> <source_dir> <git_url>"
            exit 1
        fi
        add_project "$2" "$3" "$4"
        ;;
    "status")
        log "${BLUE}Multi-Project Backup Status:${NC}"
        log "Backup directory: $BACKUP_DIR"
        log "Log file: $LOG_FILE"
        log "Configured projects:"
        log "  - hunonic-banner-tools: /Users/AmyNguyen/Desktop/Cursor AI MKT/hunonic-banner-tools"
        log "  - calendar-tools: /Users/AmyNguyen/Desktop/Cursor AI MKT/calendar-tools"
        ;;
    *)
        echo "Usage: $0 {backup|run|add|status}"
        echo "  backup - Run single backup for all projects"
        echo "  run    - Run continuous backup every 30 minutes"
        echo "  add    - Add new project (usage: $0 add <name> <source_dir> <git_url>)"
        echo "  status - Show configuration status"
        exit 1
        ;;
esac
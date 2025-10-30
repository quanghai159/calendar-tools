#!/bin/bash

# Advanced Multi-Project Auto Backup Script
# Uses JSON configuration and supports parallel backups

# Configuration
CONFIG_FILE="projects_config.json"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_PATH="$SCRIPT_DIR/$CONFIG_FILE"

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

# Function to read config
read_config() {
    if [ ! -f "$CONFIG_PATH" ]; then
        log "${RED}Config file not found: $CONFIG_PATH${NC}"
        exit 1
    fi
    
    # Read configuration using jq
    BACKUP_DIR=$(jq -r '.backup_dir' "$CONFIG_PATH")
    LOG_FILE=$(jq -r '.log_file' "$CONFIG_PATH")
    BACKUP_INTERVAL=$(jq -r '.backup_interval' "$CONFIG_PATH")
    
    # Create directories
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$(dirname "$LOG_FILE")"
}

# Function to backup single project (parallel)
backup_project_parallel() {
    local project_name="$1"
    local source_dir="$2"
    local git_url="$3"
    local backup_repo_dir="$BACKUP_DIR/$project_name"
    
    {
        log "${BLUE}[$project_name] Starting backup...${NC}"
        
        # Create backup directory if not exists
        if [ ! -d "$backup_repo_dir" ]; then
            mkdir -p "$backup_repo_dir"
            cd "$backup_repo_dir"
            git init
            git remote add origin "$git_url"
        else
            cd "$backup_repo_dir"
        fi
        
        # Copy files
        rsync -av --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='.DS_Store' --exclude='node_modules' --exclude='*.log' --exclude='*.tmp' --exclude='.env' --exclude='database/*.db' "$source_dir/" "$backup_repo_dir/"
        
        # Git operations
        git add .
        
        if git diff --staged --quiet; then
            log "${YELLOW}[$project_name] No changes to commit${NC}"
            echo "SUCCESS:$project_name:No changes"
        else
            COMMIT_MSG="Auto backup $(date '+%Y-%m-%d %H:%M:%S') - $project_name"
            git commit -m "$COMMIT_MSG"
            
            if git push origin main; then
                log "${GREEN}[$project_name] Backup completed successfully!${NC}"
                echo "SUCCESS:$project_name:Backup completed"
            else
                log "${RED}[$project_name] Backup failed!${NC}"
                echo "FAILED:$project_name:Push failed"
            fi
        fi
    } &
}

# Function to backup all projects in parallel
backup_all_projects_parallel() {
    log "${YELLOW}Starting parallel multi-project backup...${NC}"
    
    # Get enabled projects
    local enabled_projects=()
    while IFS= read -r project_name; do
        enabled_projects+=("$project_name")
    done < <(jq -r '.projects | to_entries[] | select(.value.enabled == true) | .key' "$CONFIG_PATH")
    
    # Start parallel backups
    local pids=()
    for project_name in "${enabled_projects[@]}"; do
        source_dir=$(jq -r ".projects.$project_name.source_dir" "$CONFIG_PATH")
        git_url=$(jq -r ".projects.$project_name.git_url" "$CONFIG_PATH")
        
        if [ -d "$source_dir" ]; then
            backup_project_parallel "$project_name" "$source_dir" "$git_url"
            pids+=($!)
        else
            log "${RED}Source directory not found: $source_dir${NC}"
        fi
    done
    
    # Wait for all backups to complete
    local success_count=0
    local total_count=${#pids[@]}
    
    for pid in "${pids[@]}"; do
        wait $pid
        if [ $? -eq 0 ]; then
            ((success_count++))
        fi
    done
    
    log "${GREEN}Parallel backup completed: $success_count/$total_count projects successful${NC}"
}

# Function to add new project
add_new_project() {
    local project_name="$1"
    local source_dir="$2"
    local git_url="$3"
    local description="$4"
    
    log "${YELLOW}Adding new project: $project_name${NC}"
    
    # Add to config file
    jq --arg name "$project_name" --arg source "$source_dir" --arg url "$git_url" --arg desc "$description" \
        '.projects[$name] = {
            "source_dir": $source,
            "git_url": $url,
            "enabled": true,
            "description": $desc
        }' "$CONFIG_PATH" > tmp_config.json && mv tmp_config.json "$CONFIG_PATH"
    
    log "${GREEN}Project $project_name added to configuration${NC}"
    
    # Test backup
    if [ -d "$source_dir" ]; then
        backup_project_parallel "$project_name" "$source_dir" "$git_url"
    else
        log "${RED}Source directory not found: $source_dir${NC}"
    fi
}

# Function to run continuous backup
run_continuous() {
    log "${GREEN}Starting continuous parallel multi-project backup (every $((BACKUP_INTERVAL/60)) minutes)...${NC}"
    log "Press Ctrl+C to stop"
    
    while true; do
        backup_all_projects_parallel
        log "Waiting $((BACKUP_INTERVAL/60)) minutes for next backup..."
        sleep $BACKUP_INTERVAL
    done
}

# Main script
read_config

case "$1" in
    "backup")
        backup_all_projects_parallel
        ;;
    "run")
        run_continuous
        ;;
    "add")
        if [ $# -ne 5 ]; then
            echo "Usage: $0 add <project_name> <source_dir> <git_url> <description>"
            exit 1
        fi
        add_new_project "$2" "$3" "$4" "$5"
        ;;
    "status")
        log "${BLUE}Multi-Project Backup Configuration:${NC}"
        log "Backup directory: $BACKUP_DIR"
        log "Log file: $LOG_FILE"
        log "Interval: $((BACKUP_INTERVAL/60)) minutes"
        log "Enabled projects:"
        jq -r '.projects | to_entries[] | select(.value.enabled == true) | "  - \(.key): \(.value.description)"' "$CONFIG_PATH"
        ;;
    *)
        echo "Usage: $0 {backup|run|add|status}"
        echo "  backup - Run single parallel backup for all projects"
        echo "  run    - Run continuous parallel backup"
        echo "  add    - Add new project (usage: $0 add <name> <source_dir> <git_url> <description>)"
        echo "  status - Show configuration status"
        exit 1
        ;;
esac
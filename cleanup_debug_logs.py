#!/usr/bin/env python3
"""
Script để cleanup debug logs trong datetime-picker.js và task-actions.js
Thay thế console.log bằng debugLog() với categories phù hợp
"""

import re
import os
import shutil
from datetime import datetime

# Files cần xử lý
FILES = [
    'frontend/static/js/datetime-picker.js',
    'frontend/static/js/task-actions.js'
]

# Patterns để replace (theo thứ tự ưu tiên)
REPLACEMENTS = [
    # 1. INIT category
    {
        'pattern': r"console\.log\(('🔍 DEBUG initializeDateTimePickers[^']*')\)",
        'replace': r"debugLog('init', \1)",
        'category': 'INIT'
    },
    {
        'pattern': r"console\.log\((`\s*- Found.*?datetime inputs`)\)",
        'replace': r"debugLog('init', \1)",
        'category': 'INIT'
    },
    {
        'pattern': r"console\.log\('  - Processing input.*?'\)",
        'replace': r"debugLog('init', '  - Processing input ' + arguments[0])",
        'category': 'INIT'
    },
    
    # 2. SETUP category
    {
        'pattern': r"console\.log\(('🔍 DEBUG setupInputEvents[^']*')\)",
        'replace': r"debugLog('setup', \1)",
        'category': 'SETUP'
    },
    {
        'pattern': r"console\.log\('  - (Input|Wrapper|Popup|Adding event).*?'\)",
        'replace': r"debugLog('setup', '\1')",
        'category': 'SETUP'
    },
    
    # 3. EVENTS category
    {
        'pattern': r"console\.log\('🔍 DEBUG: Input (clicked|mousedown|touchstart|focus|double-click) event fired'\)",
        'replace': r"debugLog('events', '🔍 DEBUG: Input \1 event fired')",
        'category': 'EVENTS'
    },
    
    # 4. POPUP category
    {
        'pattern': r"console\.log\(('🔍 DEBUG (showPopup|hidePopup|positionPopup|closePopup)[^']*')\)",
        'replace': r"debugLog('popup', \1)",
        'category': 'POPUP'
    },
    
    # 5. OFFSET category
    {
        'pattern': r"console\.log\(('🔍 DEBUG showReferenceNote[^']*')\)",
        'replace': r"debugLog('offset', \1)",
        'category': 'OFFSET'
    },
    {
        'pattern': r"console\.log\('  - (Param|Formatted offset)[^']*'\)",
        'replace': r"debugLog('offset', '\1')",
        'category': 'OFFSET'
    },
    
    # 6. Task Actions - specific patterns
    {
        'pattern': r"console\.log\('🔍 DEBUG (addNewTaskRow|duplicateRow|saveRow)[^']*'\)",
        'replace': r"debugLog('init', '🔍 DEBUG \1')",
        'category': 'TASK_ACTIONS'
    },
    
    # 7. Generic console.log (catch-all)
    {
        'pattern': r"console\.log\(([^)]+)\)",
        'replace': r"debugLog('init', \1)",
        'category': 'GENERIC'
    },
    
    # 8. console.error → debugError
    {
        'pattern': r"console\.error\(([^)]+)\)",
        'replace': r"debugError(\1)",
        'category': 'ERROR'
    }
]

def backup_file(filepath):
    """Backup file với timestamp"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{filepath}.backup.{timestamp}"
    shutil.copy2(filepath, backup_path)
    print(f"✅ Backed up: {backup_path}")
    return backup_path

def process_file(filepath):
    """Process một file"""
    print(f"\n{'='*60}")
    print(f"Processing: {filepath}")
    print(f"{'='*60}")
    
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return
    
    # Backup
    backup_path = backup_file(filepath)
    
    # Read file
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    stats = {}
    
    # Apply replacements
    for replacement in REPLACEMENTS:
        pattern = replacement['pattern']
        replace = replacement['replace']
        category = replacement['category']
        
        # Count matches before replace
        matches = re.findall(pattern, content)
        count = len(matches)
        
        if count > 0:
            content = re.sub(pattern, replace, content)
            stats[category] = stats.get(category, 0) + count
            print(f"  {category:15} : {count:3} replacements")
    
    # Write back if changed
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        total = sum(stats.values())
        print(f"\n✅ Total replacements: {total}")
        print(f"✅ File updated: {filepath}")
    else:
        print("\n⚠️  No changes made")
    
    return stats

def main():
    """Main function"""
    print("🧹 CLEANUP DEBUG LOGS")
    print("=" * 60)
    
    base_dir = os.getcwd()
    print(f"Working directory: {base_dir}\n")
    
    all_stats = {}
    
    for filepath in FILES:
        full_path = os.path.join(base_dir, filepath)
        stats = process_file(full_path)
        
        if stats:
            for category, count in stats.items():
                all_stats[category] = all_stats.get(category, 0) + count
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 SUMMARY")
    print(f"{'='*60}")
    
    if all_stats:
        for category, count in sorted(all_stats.items()):
            print(f"  {category:15} : {count:3} total replacements")
        
        grand_total = sum(all_stats.values())
        print(f"\n  {'GRAND TOTAL':15} : {grand_total:3} replacements")
    else:
        print("  No replacements made")
    
    print("\n✅ Done!")
    print("\n💡 Next steps:")
    print("  1. Review changes: git diff frontend/static/js/")
    print("  2. Test in browser")
    print("  3. If OK, commit changes")
    print("  4. If not OK, restore from backup")

if __name__ == '__main__':
    main()
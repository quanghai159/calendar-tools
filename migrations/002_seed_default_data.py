# -*- coding: utf-8 -*-
"""
Migration 002: Seed default data (groups, tools, permissions)
"""

import sqlite3
from datetime import datetime

# Default groups data
DEFAULT_GROUPS = [
    {
        'group_id': 'super_admin',
        'group_name': 'Super Administrator',
        'description': 'Full system access - can manage everything',
        'level': 100,
        'is_system': True
    },
    {
        'group_id': 'admin',
        'group_name': 'Administrator',
        'description': 'Administrative access - can manage users and tools',
        'level': 80,
        'is_system': True
    },
    {
        'group_id': 'manager',
        'group_name': 'Manager',
        'description': 'Management access - can view and manage team data',
        'level': 50,
        'is_system': True
    },
    {
        'group_id': 'marketing',
        'group_name': 'Marketing Team',
        'description': 'Marketing team members',
        'level': 30,
        'is_system': False
    },
    {
        'group_id': 'user',
        'group_name': 'User',
        'description': 'Regular user - basic access',
        'level': 10,
        'is_system': True
    }
]

# Default tools data
DEFAULT_TOOLS = [
    {
        'tool_id': 'calendar-tools',
        'tool_name': 'Calendar Tools',
        'description': 'Quan ly lich lam viec thong minh voi thong bao tu dong',
        'port': 5000,
        'base_url': 'http://localhost:5000',
        'icon': 'fas fa-calendar-alt',
        'is_active': True
    }
]

# Default permissions for calendar-tools
DEFAULT_CALENDAR_TOOLS_PERMISSIONS = [
    # Task permissions
    {'key': 'task.create', 'name': 'Create Task', 'category': 'task', 'description': 'Tao task moi'},
    {'key': 'task.view', 'name': 'View Tasks', 'category': 'task', 'description': 'Xem danh sach tasks'},
    {'key': 'task.view_all', 'name': 'View All Tasks', 'category': 'task', 'description': 'Xem tat ca tasks'},
    {'key': 'task.edit', 'name': 'Edit Task', 'category': 'task', 'description': 'Chinh sua task'},
    {'key': 'task.edit_all', 'name': 'Edit All Tasks', 'category': 'task', 'description': 'Chinh sua tat ca tasks'},
    {'key': 'task.delete', 'name': 'Delete Task', 'category': 'task', 'description': 'Xoa task'},
    {'key': 'task.delete_all', 'name': 'Delete All Tasks', 'category': 'task', 'description': 'Xoa tat ca tasks'},
    
    # Notification permissions
    {'key': 'notification.view', 'name': 'View Notifications', 'category': 'notification', 'description': 'Xem notifications'},
    {'key': 'notification.send', 'name': 'Send Notification', 'category': 'notification', 'description': 'Gui thong bao'},
    {'key': 'notification.manage', 'name': 'Manage Notifications', 'category': 'notification', 'description': 'Quan ly notifications'},
    {'key': 'notification.test', 'name': 'Test Notifications', 'category': 'notification', 'description': 'Test gui thong bao'},
]

# Group permissions mapping
GROUP_PERMISSIONS_MAP = {
    'super_admin': ['*'],
    'admin': ['calendar-tools:*'],
    'manager': [
        'calendar-tools:task.view_all',
        'calendar-tools:task.create',
        'calendar-tools:task.edit',
        'calendar-tools:notification.manage',
        'calendar-tools:notification.view',
    ],
    'user': [
        'calendar-tools:task.view',
        'calendar-tools:task.create',
        'calendar-tools:notification.send',
        'calendar-tools:notification.view',
    ]
}

# Group tool access mapping
GROUP_TOOL_ACCESS_MAP = {
    'super_admin': ['calendar-tools'],
    'admin': ['calendar-tools'],
    'manager': ['calendar-tools'],
    'marketing': ['calendar-tools'],
    'user': ['calendar-tools'],
}

def seed_groups(cursor):
    """Seed default groups"""
    print("\n📋 Seeding default groups...")
    
    for group in DEFAULT_GROUPS:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO user_groups 
                (group_id, group_name, description, level, is_system, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                group['group_id'],
                group['group_name'],
                group['description'],
                group['level'],
                group['is_system'],
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            print(f"   ✅ Group: {group['group_name']}")
        except sqlite3.IntegrityError:
            print(f"   ⚠️  Group {group['group_id']} already exists, skipping")

def seed_tools(cursor):
    """Seed default tools"""
    print("\n📋 Seeding default tools...")
    
    for tool in DEFAULT_TOOLS:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO tools 
                (tool_id, tool_name, description, port, base_url, icon, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tool['tool_id'],
                tool['tool_name'],
                tool['description'],
                tool['port'],
                tool['base_url'],
                tool['icon'],
                tool['is_active'],
                datetime.now().isoformat()
            ))
            print(f"   ✅ Tool: {tool['tool_name']}")
        except sqlite3.IntegrityError:
            print(f"   ⚠️  Tool {tool['tool_id']} already exists, skipping")

def seed_permissions(cursor, tool_id):
    """Seed permissions for a tool"""
    print(f"\n📋 Seeding permissions for tool: {tool_id}...")
    
    if tool_id == 'calendar-tools':
        permissions = DEFAULT_CALENDAR_TOOLS_PERMISSIONS
    else:
        permissions = []
    
    for perm in permissions:
        permission_id = f"{tool_id}:{perm['key']}"
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO permissions 
                (permission_id, tool_id, permission_key, permission_name, description, category, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                permission_id,
                tool_id,
                perm['key'],
                perm['name'],
                perm['description'],
                perm['category'],
                datetime.now().isoformat()
            ))
            print(f"   ✅ Permission: {permission_id}")
        except sqlite3.IntegrityError:
            print(f"   ⚠️  Permission {permission_id} already exists, skipping")

def seed_group_permissions(cursor):
    """Seed group permissions"""
    print("\n📋 Seeding group permissions...")
    
    for group_id, permissions in GROUP_PERMISSIONS_MAP.items():
        if permissions == ['*']:
            # Super admin: get all permissions
            cursor.execute("SELECT permission_id FROM permissions")
            all_perms = [row[0] for row in cursor.fetchall()]
            permissions = all_perms
        elif permissions and len(permissions) > 0 and permissions[0].endswith(':*'):
            # Admin: get all permissions for specific tool
            tool_id = permissions[0].replace(':*', '')
            cursor.execute("SELECT permission_id FROM permissions WHERE tool_id = ?", (tool_id,))
            all_perms = [row[0] for row in cursor.fetchall()]
            permissions = all_perms
        
        for permission_id in permissions:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO group_permissions 
                    (group_id, permission_id, granted_at)
                    VALUES (?, ?, ?)
                """, (
                    group_id,
                    permission_id,
                    datetime.now().isoformat()
                ))
            except sqlite3.IntegrityError:
                pass
    
    print("   ✅ Group permissions seeded")

def seed_group_tool_access(cursor):
    """Seed group tool access"""
    print("\n📋 Seeding group tool access...")
    
    for group_id, tools in GROUP_TOOL_ACCESS_MAP.items():
        for tool_id in tools:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO group_tool_access 
                    (group_id, tool_id, granted_at)
                    VALUES (?, ?, ?)
                """, (
                    group_id,
                    tool_id,
                    datetime.now().isoformat()
                ))
            except sqlite3.IntegrityError:
                pass
    
    print("   ✅ Group tool access seeded")

def seed_default_data(database_path: str = "database/calendar_tools.db"):
    """Chay seed default data"""
    
    print("=" * 60)
    print("PHASE 2: SEED DEFAULT DATA")
    print("=" * 60)
    
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    
    try:
        seed_groups(cursor)
        seed_tools(cursor)
        
        # Seed permissions for each tool
        for tool in DEFAULT_TOOLS:
            seed_permissions(cursor, tool['tool_id'])
        
        seed_group_permissions(cursor)
        seed_group_tool_access(cursor)
        
        conn.commit()
        
        print("\n" + "=" * 60)
        print("✅ SEED DATA HOAN TAT!")
        print("=" * 60)
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Loi seed data: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    import os
    import sys
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)
    
    try:
        from backend.utils.config_loader import ConfigLoader
        config = ConfigLoader("config/config.json")
        db_path = config.get_value('database.path', 'database/calendar_tools.db')
    except:
        db_path = "database/calendar_tools.db"
    
    seed_default_data(db_path)
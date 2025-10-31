# check_database_integrity.py
# -*- coding: utf-8 -*-
"""
Script kiểm tra dữ liệu trong database và so sánh với frontend
"""
import sqlite3
import json
import os
from pathlib import Path

# Lấy đường dẫn database từ config
config_path = Path(__file__).parent / "config" / "config.json"
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

db_path = config['database']['path']
if not os.path.isabs(db_path):
    db_path = Path(__file__).parent / db_path

print(f"📂 Database path: {db_path}")
print(f"📂 Database exists: {os.path.exists(db_path)}\n")

if not os.path.exists(db_path):
    print("❌ Database không tồn tại!")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

print("=" * 80)
print("📊 KIỂM TRA DỮ LIỆU DATABASE")
print("=" * 80)

# 1. Users
print("\n👤 BẢNG USERS:")
users = conn.execute("SELECT * FROM users").fetchall()
print(f"  Tổng số users: {len(users)}")
for u in users:
    display_name = u['display_name'] or ''
    email = u['email'] or ''
    phone = u['phone_number'] or ''
    print(f"  - user_id: {u['user_id']}")
    print(f"    display_name: '{display_name}'")
    print(f"    email: '{email}'")
    print(f"    phone_number: '{phone}'")

# 2. User Groups
print("\n👥 BẢNG USER_GROUPS:")
groups = conn.execute("SELECT * FROM user_groups").fetchall()
print(f"  Tổng số groups: {len(groups)}")
for g in groups:
    print(f"  - group_id: {g['group_id']}, group_name: '{g['group_name']}'")

# 3. User Group Memberships
print("\n🔗 BẢNG USER_GROUP_MEMBERSHIPS:")
memberships = conn.execute("""
    SELECT m.*, 
           COALESCE(u.display_name, u.email, u.phone_number, m.user_id) AS user_label
    FROM user_group_memberships m
    LEFT JOIN users u ON u.user_id = m.user_id
    ORDER BY m.group_id, user_label
""").fetchall()
print(f"  Tổng số memberships: {len(memberships)}")
group_members = {}
for m in memberships:
    group_id = m['group_id']
    if group_id not in group_members:
        group_members[group_id] = []
    group_members[group_id].append({
        'user_id': m['user_id'],
        'label': m['user_label']
    })

for group_id, members in group_members.items():
    group_name = conn.execute("SELECT group_name FROM user_groups WHERE group_id=?", (group_id,)).fetchone()
    group_name = group_name['group_name'] if group_name else 'N/A'
    print(f"  - Group '{group_name}' ({group_id}):")
    for mem in members:
        print(f"      • {mem['user_id']} ({mem['label']})")

# 4. User Permissions
print("\n🔐 BẢNG USER_PERMISSIONS (quyền trực tiếp của user):")
user_perms = conn.execute("""
    SELECT up.*, 
           COALESCE(u.display_name, u.email, u.phone_number, up.user_id) AS user_label
    FROM user_permissions up
    LEFT JOIN users u ON u.user_id = up.user_id
    ORDER BY up.user_id, up.permission_id
""").fetchall()
print(f"  Tổng số user permissions: {len(user_perms)}")
user_perm_map = {}
for up in user_perms:
    user_id = up['user_id']
    if user_id not in user_perm_map:
        user_perm_map[user_id] = []
    user_perm_map[user_id].append(up['permission_id'])

for user_id, perms in user_perm_map.items():
    user_label = user_perms[0]['user_label'] if user_perms and user_perms[0]['user_id'] == user_id else user_id
    print(f"  - User {user_id} ({user_label}):")
    for perm in perms:
        print(f"      • {perm}")

# 5. Group Permissions
print("\n🔐 BẢNG GROUP_PERMISSIONS:")
group_perms = conn.execute("""
    SELECT gp.*, g.group_name
    FROM group_permissions gp
    JOIN user_groups g ON g.group_id = gp.group_id
    ORDER BY gp.group_id, gp.permission_id
""").fetchall()
print(f"  Tổng số group permissions: {len(group_perms)}")
group_perm_map = {}
for gp in group_perms:
    group_id = gp['group_id']
    if group_id not in group_perm_map:
        group_perm_map[group_id] = []
    group_perm_map[group_id].append(gp['permission_id'])

for group_id, perms in group_perm_map.items():
    group_name = conn.execute("SELECT group_name FROM user_groups WHERE group_id=?", (group_id,)).fetchone()
    group_name = group_name['group_name'] if group_name else 'N/A'
    print(f"  - Group '{group_name}' ({group_id}):")
    for perm in perms:
        print(f"      • {perm}")

# 6. User Tool Access
print("\n🛠️ BẢNG USER_TOOL_ACCESS:")
user_tools = conn.execute("""
    SELECT uta.*, 
           COALESCE(u.display_name, u.email, u.phone_number, uta.user_id) AS user_label,
           t.tool_name
    FROM user_tool_access uta
    LEFT JOIN users u ON u.user_id = uta.user_id
    LEFT JOIN tools t ON t.tool_id = uta.tool_id
    ORDER BY uta.user_id, uta.tool_id
""").fetchall()
print(f"  Tổng số user tool access: {len(user_tools)}")
user_tool_map = {}
for ut in user_tools:
    user_id = ut['user_id']
    if user_id not in user_tool_map:
        user_tool_map[user_id] = []
    user_tool_map[user_id].append(ut['tool_id'])

for user_id, tools in user_tool_map.items():
    user_label = user_tools[0]['user_label'] if user_tools and user_tools[0]['user_id'] == user_id else user_id
    print(f"  - User {user_id} ({user_label}):")
    for tool in tools:
        print(f"      • {tool}")

# 7. Group Tool Access
print("\n🛠️ BẢNG GROUP_TOOL_ACCESS:")
group_tools = conn.execute("""
    SELECT gta.*, g.group_name, t.tool_name
    FROM group_tool_access gta
    JOIN user_groups g ON g.group_id = gta.group_id
    LEFT JOIN tools t ON t.tool_id = gta.tool_id
    ORDER BY gta.group_id, gta.tool_id
""").fetchall()
print(f"  Tổng số group tool access: {len(group_tools)}")
group_tool_map = {}
for gt in group_tools:
    group_id = gt['group_id']
    if group_id not in group_tool_map:
        group_tool_map[group_id] = []
    group_tool_map[group_id].append(gt['tool_id'])

for group_id, tools in group_tool_map.items():
    group_name = conn.execute("SELECT group_name FROM user_groups WHERE group_id=?", (group_id,)).fetchone()
    group_name = group_name['group_name'] if group_name else 'N/A'
    print(f"  - Group '{group_name}' ({group_id}):")
    for tool in tools:
        print(f"      • {tool}")

# 8. User Settings (một số key quan trọng)
print("\n⚙️ BẢNG USER_SETTINGS (một số key quan trọng):")
important_keys = ['telegram_user_id', 'display_name', 'phone_number', 'email_alt']
settings = conn.execute("""
    SELECT us.*, 
           COALESCE(u.display_name, u.email, u.phone_number, us.user_id) AS user_label
    FROM user_settings us
    LEFT JOIN users u ON u.user_id = us.user_id
    WHERE us.setting_key IN ('telegram_user_id', 'display_name', 'phone_number', 'email_alt')
    ORDER BY us.user_id, us.setting_key, us.tool_id
""").fetchall()
print(f"  Tổng số settings (các key quan trọng): {len(settings)}")
for s in settings[:20]:  # Hiển thị 20 đầu tiên
    tool_id = s['tool_id'] or '(global)'
    print(f"  - User {s['user_id']} ({s['user_label']}): {s['setting_key']} = '{s['setting_value']}' [tool: {tool_id}]")

print("\n" + "=" * 80)
print("✅ Hoàn tất kiểm tra!")
print("=" * 80)

conn.close()
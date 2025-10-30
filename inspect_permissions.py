import sqlite3, sys

db = 'database/calendar_tools.db'
uid = sys.argv[1] if len(sys.argv) > 1 else None
if not uid:
    print("Usage: python3 inspect_permissions.py <USER_ID>")
    sys.exit(1)

conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print(f"== USER: {uid}")

print("\n-- Groups --")
for r in cur.execute("""
  SELECT ug.group_id, ug.group_name
  FROM user_group_memberships ugm
  JOIN user_groups ug ON ugm.group_id = ug.group_id
  WHERE ugm.user_id = ?
""", (uid,)):
  print(f"  {r['group_id']} - {r['group_name']}")

print("\n-- Direct Tool Access --")
for r in cur.execute("""
  SELECT uta.tool_id, t.tool_name
  FROM user_tool_access uta
  LEFT JOIN tools t ON uta.tool_id = t.tool_id
  WHERE uta.user_id = ?
""", (uid,)):
  print(f"  {r['tool_id']} - {r['tool_name'] or ''}")

print("\n-- Group Tool Access --")
for r in cur.execute("""
  SELECT gta.tool_id, t.tool_name, gta.group_id
  FROM group_tool_access gta
  LEFT JOIN tools t ON gta.tool_id = t.tool_id
  WHERE gta.group_id IN (
    SELECT group_id FROM user_group_memberships WHERE user_id = ?
  )
""", (uid,)):
  print(f"  {r['tool_id']} - {r['tool_name'] or ''} (via group {r['group_id']})")

print("\n-- Direct Permissions --")
for r in cur.execute("""
  SELECT up.permission_id, p.permission_name
  FROM user_permissions up
  JOIN permissions p ON up.permission_id = p.permission_id
  WHERE up.user_id = ?
""", (uid,)):
  print(f"  {r['permission_id']} - {r['permission_name']}")

print("\n-- Group Permissions --")
for r in cur.execute("""
  SELECT gp.permission_id, p.permission_name, gp.group_id
  FROM group_permissions gp
  JOIN permissions p ON gp.permission_id = p.permission_id
  WHERE gp.group_id IN (
    SELECT group_id FROM user_group_memberships WHERE user_id = ?
  )
""", (uid,)):
  print(f"  {r['permission_id']} - {r['permission_name']} (via group {r['group_id']})")

print("\n-- Effective Permissions (names) --")
for r in cur.execute("""
  SELECT DISTINCT p.permission_name
  FROM permissions p
  WHERE p.permission_id IN (
    SELECT permission_id FROM user_permissions WHERE user_id = ?
    UNION
    SELECT permission_id FROM group_permissions 
    WHERE group_id IN (SELECT group_id FROM user_group_memberships WHERE user_id = ?)
  )
  ORDER BY p.permission_name
""", (uid, uid)):
  print(f"  {r['permission_name']}")

conn.close()
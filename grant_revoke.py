import sqlite3, sys

db = 'database/calendar_tools.db'
conn = sqlite3.connect(db)
cur = conn.cursor()

action = sys.argv[1] if len(sys.argv) > 1 else None

def done():
    conn.commit(); conn.close()

if action == 'grant_group':
    # usage: python3 grant_revoke.py grant_group <user_id> <group_id>
    _, _, uid, gid = sys.argv
    cur.execute("INSERT OR IGNORE INTO user_group_memberships (user_id, group_id) VALUES (?,?)", (uid, gid))
    print(f"Granted group {gid} to {uid}")
elif action == 'revoke_group':
    # usage: python3 grant_revoke.py revoke_group <user_id> <group_id>
    _, _, uid, gid = sys.argv
    cur.execute("DELETE FROM user_group_memberships WHERE user_id=? AND group_id=?", (uid, gid))
    print(f"Revoked group {gid} from {uid}")
elif action == 'grant_tool':
    # usage: python3 grant_revoke.py grant_tool <user_id> <tool_id>
    _, _, uid, tid = sys.argv
    cur.execute("INSERT OR IGNORE INTO tools (tool_id, tool_name) VALUES (?,?)", (tid, tid.replace('-', ' ').title()))
    cur.execute("INSERT OR IGNORE INTO user_tool_access (user_id, tool_id) VALUES (?,?)", (uid, tid))
    print(f"Granted tool {tid} to {uid}")
elif action == 'revoke_tool':
    # usage: python3 grant_revoke.py revoke_tool <user_id> <tool_id>
    _, _, uid, tid = sys.argv
    cur.execute("DELETE FROM user_tool_access WHERE user_id=? AND tool_id=?", (uid, tid))
    print(f"Revoked tool {tid} from {uid}")
elif action == 'grant_perm':
    # usage: python3 grant_revoke.py grant_perm <user_id> <permission_name>
    _, _, uid, pname = sys.argv
    row = cur.execute("SELECT permission_id FROM permissions WHERE permission_id=?", (pname,)).fetchone()
    if not row:
        print("Permission not found. Add in permissions table first."); done(); sys.exit(1)
    pid = row[0]
    cur.execute("INSERT OR IGNORE INTO user_permissions (user_id, permission_id) VALUES (?,?)", (uid, pid))
    print(f"Granted perm {pname} to {uid}")
elif action == 'revoke_perm':
    # usage: python3 grant_revoke.py revoke_perm <user_id> <permission_name>
    _, _, uid, pname = sys.argv
    row = cur.execute("SELECT permission_id FROM permissions WHERE permission_id=?", (pname,)).fetchone()
    if row:
        pid = row[0]
        cur.execute("DELETE FROM user_permissions WHERE user_id=? AND permission_id=?", (uid, pid))
        print(f"Revoked perm {pname} from {uid}")
    else:
        print("Permission not found.")
else:
    print("Usage:")
    print("  python3 grant_revoke.py grant_group <user_id> <group_id>")
    print("  python3 grant_revoke.py revoke_group <user_id> <group_id>")
    print("  python3 grant_revoke.py grant_tool <user_id> <tool_id>")
    print("  python3 grant_revoke.py revoke_tool <user_id> <tool_id>")
    print("  python3 grant_revoke.py grant_perm <user_id> <permission_name>")
    print("  python3 grant_revoke.py revoke_perm <user_id> <permission_name>")

done()
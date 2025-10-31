import sqlite3
DB = "database/calendar_tools.db"

cols = [f"notif{i}" for i in range(1,9)]

def col_exists(cur, table, col):
    cur.execute(f"PRAGMA table_info({table})")
    return any(r[1] == col for r in cur.fetchall())

with sqlite3.connect(DB) as conn:
    cur = conn.cursor()
    for c in cols:
        if not col_exists(cur, "tasks", c):
            cur.execute(f"ALTER TABLE tasks ADD COLUMN {c} TEXT")
    conn.commit()
print("✅ Added notif1..notif8 if missing")
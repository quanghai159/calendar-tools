import sqlite3

# Kết nối database
conn = sqlite3.connect('database/calendar_tools.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Kiểm tra dữ liệu trong user_settings
print("=== Tất cả settings ===")
cursor.execute("SELECT user_id, tool_id, setting_key, setting_value FROM user_settings WHERE user_id = 'CL54mVGb6HVjKwDFtnOZquuF8ax2'")
rows = cursor.fetchall()
for row in rows:
    print(f"user_id={row['user_id']}, tool_id={row['tool_id']}, key={row['setting_key']}, value={row['setting_value']}")

print("\n=== Global settings (tool_id IS NULL) ===")
cursor.execute("SELECT setting_key, setting_value FROM user_settings WHERE user_id = ? AND tool_id IS NULL", ('CL54mVGb6HVjKwDFtnOZquuF8ax2',))
rows = cursor.fetchall()
for row in rows:
    print(f"key={row['setting_key']}, value={row['setting_value']}")

print("\n=== Calendar tools settings ===")
cursor.execute("SELECT setting_key, setting_value FROM user_settings WHERE user_id = ? AND tool_id = ?", ('CL54mVGb6HVjKwDFtnOZquuF8ax2', 'calendar-tools'))
rows = cursor.fetchall()
for row in rows:
    print(f"key={row['setting_key']}, value={row['setting_value']}")

conn.close()
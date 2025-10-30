import sqlite3

conn = sqlite3.connect('database/calendar_tools.db')
cursor = conn.cursor()

print("=== Kiểm tra sau khi lưu ===")
cursor.execute("""
    SELECT setting_key, setting_value, tool_id 
    FROM user_settings 
    WHERE user_id = 'CL54mVGb6HVjKwDFtnOZquuF8ax2' 
    AND setting_key = 'telegram_user_id'
    ORDER BY updated_at DESC
    LIMIT 5
""")
rows = cursor.fetchall()
for row in rows:
    print(f"key={row[0]}, value={row[1]}, tool_id={row[2]}")

print("\n=== Kiểm tra với tool_id IS NULL ===")
cursor.execute("""
    SELECT setting_key, setting_value 
    FROM user_settings 
    WHERE user_id = 'CL54mVGb6HVjKwDFtnOZquuF8ax2' 
    AND setting_key = 'telegram_user_id'
    AND tool_id IS NULL
""")
rows = cursor.fetchall()
for row in rows:
    print(f"key={row[0]}, value={row[1]}")

conn.close()
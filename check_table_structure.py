import sqlite3

conn = sqlite3.connect('database/calendar_tools.db')
cursor = conn.cursor()

# Kiểm tra cấu trúc bảng user_settings
cursor.execute("PRAGMA table_info(user_settings)")
columns = cursor.fetchall()
print("Cấu trúc bảng user_settings:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

conn.close()
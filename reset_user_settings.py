import sqlite3

conn = sqlite3.connect('database/calendar_tools.db')
cursor = conn.cursor()

print("Xóa toàn bộ bảng user_settings...")
cursor.execute("DELETE FROM user_settings")
deleted_count = cursor.rowcount
print(f"Đã xóa {deleted_count} bản ghi")

conn.commit()
conn.close()

print("Reset hoàn tất! Bây giờ hãy thử lưu settings mới.")
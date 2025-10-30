import sqlite3

# Kết nối database
conn = sqlite3.connect('database/calendar_tools.db')
cursor = conn.cursor()

print("Dọn dẹp database...")

# Xóa tất cả bản ghi cũ với tool_id = 'None'
cursor.execute("DELETE FROM user_settings WHERE tool_id = 'None'")
deleted_count = cursor.rowcount
print(f"Đã xóa {deleted_count} bản ghi cũ")

# Xóa các bản ghi trùng lặp dựa trên user_id, tool_id, setting_key
# Chỉ giữ lại bản ghi có updated_at mới nhất
cursor.execute("""
    DELETE FROM user_settings 
    WHERE rowid NOT IN (
        SELECT MAX(rowid) 
        FROM user_settings 
        GROUP BY user_id, tool_id, setting_key
    )
""")
duplicate_count = cursor.rowcount
print(f"Đã xóa {duplicate_count} bản ghi trùng lặp")

conn.commit()
conn.close()

print("Dọn dẹp hoàn tất!")
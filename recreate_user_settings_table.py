import sqlite3

conn = sqlite3.connect('database/calendar_tools.db')
cursor = conn.cursor()

print("Tạo lại bảng user_settings với constraint đúng...")

# Backup dữ liệu hiện tại
cursor.execute("CREATE TABLE user_settings_backup AS SELECT * FROM user_settings")
print("Đã backup dữ liệu")

# Xóa bảng cũ
cursor.execute("DROP TABLE user_settings")
print("Đã xóa bảng cũ")

# Tạo bảng mới với unique constraint
cursor.execute("""
CREATE TABLE user_settings (
    user_id TEXT NOT NULL,
    tool_id TEXT,
    setting_key TEXT NOT NULL,
    setting_value TEXT,
    setting_type TEXT DEFAULT 'string',
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, tool_id, setting_key)
)
""")
print("Đã tạo bảng mới")

# Restore dữ liệu (chỉ lấy bản ghi mới nhất cho mỗi combination)
cursor.execute("""
INSERT INTO user_settings 
SELECT user_id, tool_id, setting_key, setting_value, setting_type, description, updated_at
FROM user_settings_backup
WHERE rowid IN (
    SELECT MAX(rowid) 
    FROM user_settings_backup 
    GROUP BY user_id, tool_id, setting_key
)
""")
print("Đã restore dữ liệu")

# Xóa bảng backup
cursor.execute("DROP TABLE user_settings_backup")
print("Đã xóa bảng backup")

conn.commit()
conn.close()

print("Hoàn tất!")
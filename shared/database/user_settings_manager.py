# -*- coding: utf-8 -*-
import sqlite3
from typing import Any, Dict, Optional

class UserSettingsManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_setting(self, user_id: str, setting_key: str, tool_id: Optional[str] = None, default: Any = None) -> Any:
        print(f"🔍 Debug: get_setting(user_id={user_id}, key={setting_key}, tool_id={tool_id})")
        with self._conn() as conn:
            if tool_id is None:
                # Tìm global settings (tool_id IS NULL hoặc 'None')
                row = conn.execute(
                    "SELECT setting_value FROM user_settings WHERE user_id = ? AND setting_key = ? AND (tool_id IS NULL OR tool_id = 'None') ORDER BY updated_at DESC LIMIT 1",
                    (user_id, setting_key)
                ).fetchone()
                print(f"🔍 Debug: Found global setting: {row}")
            else:
                # Tìm tool-specific settings
                row = conn.execute(
                    "SELECT setting_value FROM user_settings WHERE user_id = ? AND setting_key = ? AND tool_id = ?",
                    (user_id, setting_key, tool_id)
                ).fetchone()
                print(f"🔍 Debug: Found tool setting: {row}")
            
            result = row["setting_value"] if row and row["setting_value"] is not None else default
            print(f"🔍 Debug: Final result: {result}")
            return result

    def set_setting(self, user_id: str, setting_key: str, setting_value: Any, tool_id: Optional[str] = None, setting_type: str = 'string', description: str = None) -> None:
        print(f"🔍 Debug: set_setting(user_id={user_id}, key={setting_key}, value={setting_value}, tool_id={tool_id})")
        with self._conn() as conn:
            # Xử lý tool_id: None -> NULL, string -> string
            db_tool_id = None if tool_id is None else tool_id
            
            conn.execute(
                """
                INSERT INTO user_settings (user_id, tool_id, setting_key, setting_value, setting_type, description, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id, tool_id, setting_key) DO UPDATE SET
                    setting_value = excluded.setting_value,
                    setting_type = excluded.setting_type,
                    description = excluded.description,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (user_id, db_tool_id, setting_key, str(setting_value), setting_type, description)
            )
            conn.commit()
            print(f"🔍 Debug: Setting saved with tool_id={db_tool_id}")

    def get_all_settings(self, user_id: str, tool_id: Optional[str] = None) -> Dict[str, Any]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT setting_key, setting_value FROM user_settings WHERE user_id = ? AND (tool_id IS ? OR tool_id = ?)",
                (user_id, None if tool_id is None else None, tool_id)
            ).fetchall()
            return {r["setting_key"]: r["setting_value"] for r in rows}
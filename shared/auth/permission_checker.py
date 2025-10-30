# -*- coding: utf-8 -*-
from typing import List, Optional
import sqlite3

class PermissionChecker:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_user_groups(self, user_id: str) -> List[str]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT group_id FROM user_group_memberships WHERE user_id = ?",
                (user_id,)
            ).fetchall()
            return [r["group_id"] for r in rows]

    def has_tool_access(self, user_id: str, tool_id: str) -> bool:
        with self._conn() as conn:
            # quyền trực tiếp
            row = conn.execute(
                "SELECT 1 FROM user_tool_access WHERE user_id = ? AND tool_id = ?",
                (user_id, tool_id)
            ).fetchone()
            if row:
                return True
            # quyền qua group
            groups = self.get_user_groups(user_id)
            if not groups:
                return False
            q = """
            SELECT 1 FROM group_tool_access
            WHERE group_id IN ({placeholders}) AND tool_id = ?
            LIMIT 1
            """.format(placeholders=",".join(["?"]*len(groups)))
            row = conn.execute(q, (*groups, tool_id)).fetchone()
            return bool(row)

    def has_permission(self, user_id: str, permission_id: str) -> bool:
        with self._conn() as conn:
            # quyền trực tiếp
            row = conn.execute(
                "SELECT 1 FROM user_permissions WHERE user_id = ? AND permission_id = ?",
                (user_id, permission_id)
            ).fetchone()
            if row:
                return True
            # quyền qua group
            groups = self.get_user_groups(user_id)
            if not groups:
                return False
            q = """
            SELECT 1 FROM group_permissions
            WHERE group_id IN ({placeholders}) AND permission_id = ?
            LIMIT 1
            """.format(placeholders=",".join(["?"]*len(groups)))
            row = conn.execute(q, (*groups, permission_id)).fetchone()
            return bool(row)

    def get_user_permissions(self, user_id: str, tool_id: Optional[str] = None) -> List[str]:
        with self._conn() as conn:
            # trực tiếp
            direct = conn.execute(
                "SELECT permission_id FROM user_permissions WHERE user_id = ?",
                (user_id,)
            ).fetchall()
            direct_ids = [r["permission_id"] for r in direct]
            # qua group
            groups = self.get_user_groups(user_id)
            group_ids: List[str] = []
            if groups:
                q = """
                SELECT gp.permission_id
                FROM group_permissions gp
                WHERE gp.group_id IN ({placeholders})
                """.format(placeholders=",".join(["?"]*len(groups)))
                rows = conn.execute(q, (*groups,)).fetchall()
                group_ids = [r["permission_id"] for r in rows]
            merged = set(direct_ids) | set(group_ids)
            if tool_id:
                merged = {pid for pid in merged if pid.startswith(f"{tool_id}:")}
            return sorted(merged)
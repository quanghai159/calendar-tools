# -*- coding: utf-8 -*-
from functools import wraps
from flask import session, redirect, url_for, flash, current_app, abort
from shared.auth.permission_checker import PermissionChecker

def _checker() -> PermissionChecker:
    db_path = current_app.config.get("DB_PATH", "database/calendar_tools.db")
    return PermissionChecker(db_path)

def require_login(f):
    @wraps(f)
    def _wrap(*args, **kwargs):
        if 'user_id' not in session:
            flash('Vui lòng đăng nhập', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return _wrap

def require_tool_access(tool_id: str):
    def decorator(f):
        @wraps(f)
        @require_login
        def _wrap(*args, **kwargs):
            user_id = session.get('user_id')
            if not _checker().has_tool_access(user_id, tool_id):
                abort(403)
                flash('Bạn không có quyền truy cập công cụ này', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return _wrap
    return decorator

def require_permission(permission_id: str):
    def decorator(f):
        @wraps(f)
        @require_login
        def _wrap(*args, **kwargs):
            user_id = session.get('user_id')
            if not _checker().has_permission(user_id, permission_id):
                abort(403)
                flash('Bạn không có quyền thực hiện hành động này', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return _wrap
    return decorator
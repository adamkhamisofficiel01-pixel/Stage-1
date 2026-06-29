"""
Authorization decorators layered on top of Flask-Login's
@login_required.

- @admin_required          -> only role == 'admin'
- @privilege_required(...)  -> admin, OR 'accessall', OR one of the
                               listed privileges
"""

from functools import wraps
from flask import abort
from flask_login import current_user


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return wrapper


def privilege_required(*privileges):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            if not current_user.has_privilege(*privileges):
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator

from functools import wraps

from flask import abort, current_app
from flask_login import current_user


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()  # manda para /login
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)

    return wrapped
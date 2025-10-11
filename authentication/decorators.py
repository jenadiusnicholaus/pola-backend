from functools import wraps
from django.core.exceptions import PermissionDenied

def permission_required(permission_codename):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if request.user.has_permission(permission_codename):
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return wrapped
    return decorator

def role_required(role_name):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if request.user.has_role(role_name):
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return wrapped
    return decorator

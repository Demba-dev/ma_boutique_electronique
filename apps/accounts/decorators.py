from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(allowed_roles, redirect_to='accounts:home'):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                messages.error(request, "Accès refusé.")
                return redirect(redirect_to)
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def admin_required(view_func):
    return role_required(['admin'])(view_func)

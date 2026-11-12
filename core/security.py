from functools import wraps

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse


def client_ip(request):
    if settings.TRUST_PROXY:
        ip = request.META.get("HTTP_X_REAL_IP")
        if ip:
            return ip.strip()
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


def allow(key, limit, window):
    k = "thr:" + key
    n = cache.get(k, 0)
    if n >= limit:
        return False
    cache.add(k, 0, window)
    try:
        cache.incr(k)
    except ValueError:
        cache.set(k, 1, window)
    return True


def throttled(scope, limit=30, window=60):
    def deco(view):
        @wraps(view)
        def inner(request, *a, **kw):
            if request.method == "POST" or scope.startswith("api"):
                if not allow(f"{scope}:{client_ip(request)}", limit, window):
                    return HttpResponse("Trop de requêtes. Réessayez dans quelques minutes.", status=429)
            return view(request, *a, **kw)
        return inner
    return deco


def is_owner(user, request=None):
    if not (user and user.is_authenticated and user.is_active and user.is_superuser and user.is_staff):
        return False
    if not settings.OWNER_EMAIL or user.email.lower() != settings.OWNER_EMAIL:
        return False
    if settings.ADMIN_ALLOWED_IPS and request is not None and client_ip(request) not in settings.ADMIN_ALLOWED_IPS:
        return False
    return True

from django.conf import settings
from django.views.defaults import page_not_found

from .security import is_owner


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        resp = self.get_response(request)
        style = "'self'" if settings.USE_COMPILED_CSS else "'self' 'unsafe-inline'"
        script = "'self'" if settings.USE_COMPILED_CSS else "'self' https://cdn.tailwindcss.com"
        csp = (
            f"default-src 'self'; script-src {script}; style-src {style}; "
            "img-src 'self' data: https://loremflickr.com https://*.staticflickr.com; "
            "font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; "
            "form-action 'self'; frame-ancestors 'none'"
        )
        if not settings.DEBUG:
            csp += "; upgrade-insecure-requests"
        resp.headers.setdefault("Content-Security-Policy", csp)
        resp.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()")
        resp.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
        if request.user.is_authenticated:
            resp.headers["Cache-Control"] = "private, no-store"
        return resp


class AdminShieldMiddleware:
    """Tout ce qui se trouve sous l'adresse secrete est introuvable (404) sauf pour le proprietaire."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        prefix = f"/{settings.ADMIN_PATH}/"
        if request.path.startswith(prefix) or request.path == prefix.rstrip("/"):
            if not is_owner(request.user, request):
                return page_not_found(request, None)
        return self.get_response(request)

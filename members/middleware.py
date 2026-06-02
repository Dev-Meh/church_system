"""Security middleware: cache control, HTTP security headers."""

from django.conf import settings


def add_private_no_cache_headers(response):
    """Tell browsers not to store this response in history/cache."""
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response


class PreventAuthenticatedPageCacheMiddleware:
    """
    Authenticated HTML pages must not be cached so Back after logout
    triggers a fresh request (session check → redirect to login).

    Login/auth pages must not be cached either — stale CSRF tokens cause
    "Ombi halijaidhinishwa" when the user submits an old tab.
    """

    _NO_CACHE_PREFIXES = (
        settings.LOGIN_URL.rstrip("/"),
        "/members/register",
        "/members/password-reset",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def _should_not_cache(self, request):
        if getattr(request, "user", None) and request.user.is_authenticated:
            return True
        path = (request.path or "").rstrip("/") or "/"
        login_path = settings.LOGIN_URL.rstrip("/") or "/"
        if path == login_path or path.startswith(f"{login_path}/"):
            return True
        for prefix in self._NO_CACHE_PREFIXES:
            p = prefix.rstrip("/")
            if p and (path == p or path.startswith(f"{p}/")):
                return True
        return False

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code != 200:
            return response
        content_type = (response.get("Content-Type") or "").lower()
        if "text/html" not in content_type:
            return response
        if not self._should_not_cache(request):
            return response
        return add_private_no_cache_headers(response)


class SecurityHeadersMiddleware:
    """Extra HTTP headers (CSP, Permissions-Policy, HSTS companion headers)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if getattr(settings, "SECURITY_HEADERS_ENABLED", True):
            self._apply_headers(response, request)
        return response

    def _apply_headers(self, response, request):
        is_secure = request.is_secure()
        path = request.path or ""

        response.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        response.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        # Public posters/files must load on the marketing site (may be another port in dev).
        if path.startswith("/media/") or path.startswith("/static/"):
            response.setdefault("Cross-Origin-Resource-Policy", "cross-origin")
        else:
            response.setdefault("Cross-Origin-Resource-Policy", "same-origin")

        csp = getattr(settings, "CONTENT_SECURITY_POLICY", None)
        if csp:
            response.setdefault("Content-Security-Policy", csp)

        return response

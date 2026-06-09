"""Security middleware: cache control, HTTP security headers, admin hardening."""

from django.conf import settings
from django.http import HttpResponse, HttpResponseNotFound


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


class AdminSecurityMiddleware:
    """
    Harden Django admin against internet scanning:
    - Hide default /admin/ URL (404)
    - Optional IP allowlist for the secret ADMIN_URL
    - Brute-force rate limit on admin login POST
    """

    _DEFAULT_ADMIN_PREFIXES = ("/admin", "/admin/")

    def __init__(self, get_response):
        self.get_response = get_response
        admin_url = getattr(settings, "ADMIN_URL", "admin/").strip("/")
        self._admin_prefix = f"/{admin_url}/" if admin_url else "/admin/"
        self._allowed_ips = getattr(settings, "ADMIN_ALLOWED_IPS", None) or set()

    def _normalize_path(self, path):
        if not path:
            return "/"
        if not path.startswith("/"):
            path = f"/{path}"
        if path != "/" and not path.endswith("/"):
            path = f"{path}/"
        return path

    def _is_default_admin_probe(self, path):
        normalized = self._normalize_path(path).rstrip("/") or "/"
        for prefix in self._DEFAULT_ADMIN_PREFIXES:
            probe = prefix.rstrip("/") or "/"
            if normalized == probe or normalized.startswith(f"{probe}/"):
                custom = self._admin_prefix.rstrip("/")
                if custom == probe:
                    return False
                return True
        return False

    def _is_admin_area(self, path):
        normalized = self._normalize_path(path)
        return normalized.startswith(self._admin_prefix)

    def _is_admin_login(self, path):
        normalized = self._normalize_path(path)
        login_path = self._admin_prefix.rstrip("/") or "/"
        return normalized.rstrip("/") == login_path

    def _client_ip_allowed(self, request):
        if not self._allowed_ips:
            return True
        from .security import get_client_ip

        client_ip = get_client_ip(request)
        if client_ip in self._allowed_ips:
            return True
        if client_ip == "127.0.0.1" and "127.0.0.1" in self._allowed_ips:
            return True
        return False

    def __call__(self, request):
        path = request.path or "/"

        if self._is_default_admin_probe(path):
            return HttpResponseNotFound()

        if self._is_admin_area(path):
            if not self._client_ip_allowed(request):
                return HttpResponseNotFound()

            if request.method == "POST" and self._is_admin_login(path):
                from .security import is_rate_limited, rate_limit_message

                username = (request.POST.get("username") or "").strip()
                blocked, _retry = is_rate_limited("admin", request, username or None)
                if blocked:
                    return HttpResponse(rate_limit_message("admin", _retry), status=429)

        response = self.get_response(request)

        if (
            request.method == "POST"
            and self._is_admin_login(path)
            and self._is_admin_area(path)
        ):
            from .security import clear_rate_limit, record_rate_limit_failure

            username = (request.POST.get("username") or "").strip()
            if getattr(request, "user", None) and request.user.is_authenticated:
                clear_rate_limit("admin", request, username or None)
            elif username:
                record_rate_limit_failure("admin", request, username)

        return response


class SecurityHeadersMiddleware:
    """Extra HTTP headers (CSP, Permissions-Policy) and hide server/framework fingerprints."""

    _FINGERPRINT_HEADERS = (
        "Server",
        "X-Powered-By",
        "X-AspNet-Version",
        "X-AspNetMvc-Version",
        "X-Runtime",
        "X-Version",
        "X-Generator",
        "X-Django-Request-ID",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if getattr(settings, "HIDE_TECH_STACK", True):
            self._hide_fingerprint(response)
        if getattr(settings, "SECURITY_HEADERS_ENABLED", True):
            self._apply_headers(response, request)
        return response

    def _hide_fingerprint(self, response):
        for header in self._FINGERPRINT_HEADERS:
            if header in response:
                del response[header]
        signature = getattr(settings, "SERVER_SIGNATURE", "")
        if signature:
            response["Server"] = signature

    def _apply_headers(self, response, request):
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

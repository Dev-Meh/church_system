"""Rate limiting and client identification for auth endpoints."""

from django.conf import settings
from django.core.cache import cache


def get_client_ip(request):
    """Best-effort client IP (respects X-Forwarded-For behind Nginx)."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _cache_key(scope, identifier):
    return f"security:{scope}:{identifier}"


def _max_attempts(scope):
    if scope == "login":
        return getattr(settings, "LOGIN_RATE_LIMIT_ATTEMPTS", 5)
    if scope == "password_reset":
        return getattr(settings, "PASSWORD_RESET_RATE_LIMIT_ATTEMPTS", 3)
    if scope == "register":
        return getattr(settings, "REGISTER_RATE_LIMIT_ATTEMPTS", 5)
    return 5


def _lockout_seconds(scope):
    if scope == "login":
        return getattr(settings, "LOGIN_RATE_LIMIT_LOCKOUT", 900)
    if scope == "password_reset":
        return getattr(settings, "PASSWORD_RESET_RATE_LIMIT_WINDOW", 3600)
    if scope == "register":
        return getattr(settings, "REGISTER_RATE_LIMIT_WINDOW", 3600)
    return 900


def is_rate_limited(scope, request, username=None):
    """
    Return (blocked: bool, retry_after_seconds: int).
    Limits by IP and optionally username (login).
    """
    ip = get_client_ip(request)
    lockout = _lockout_seconds(scope)
    maximum = _max_attempts(scope)
    keys = [_cache_key(scope, f"ip:{ip}")]
    if username:
        keys.append(_cache_key(scope, f"user:{username.strip().lower()[:150]}"))

    worst = 0
    for key in keys:
        count = cache.get(key) or 0
        if count >= maximum:
            ttl = cache.ttl(key) if hasattr(cache, "ttl") else None
            worst = max(worst, ttl if ttl and ttl > 0 else lockout)
            return True, worst
    return False, 0


def record_rate_limit_failure(scope, request, username=None):
    ip = get_client_ip(request)
    lockout = _lockout_seconds(scope)
    keys = [_cache_key(scope, f"ip:{ip}")]
    if username:
        keys.append(_cache_key(scope, f"user:{username.strip().lower()[:150]}"))

    for key in keys:
        if cache.get(key) is None:
            cache.set(key, 1, lockout)
        else:
            try:
                cache.incr(key)
            except ValueError:
                cache.set(key, 1, lockout)


def clear_rate_limit(scope, request, username=None):
    ip = get_client_ip(request)
    keys = [_cache_key(scope, f"ip:{ip}")]
    if username:
        keys.append(_cache_key(scope, f"user:{username.strip().lower()[:150]}"))
    cache.delete_many(keys)


def rate_limit_message(scope, retry_seconds):
    minutes = max(1, (retry_seconds + 59) // 60)
    if scope == "login":
        return (
            f"Majaribio mengi ya kuingia. Subiri dakika {minutes} kisha jaribu tena."
        )
    if scope == "password_reset":
        return (
            f"Maombi mengi ya kubadili nenosiri. Subiri dakika {minutes} kisha jaribu tena."
        )
    return f"Maombi mengi. Subiri dakika {minutes} kisha jaribu tena."

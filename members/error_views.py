"""Generic error pages — no framework or stack details."""

from django.shortcuts import render


def _error_response(request, template, status):
    return render(request, template, status=status)


def page_not_found(request, exception=None):
    return _error_response(request, 'errors/not_found.html', 404)


def server_error(request):
    return _error_response(request, 'errors/server_error.html', 500)


def permission_denied(request, exception=None):
    return _error_response(request, 'errors/forbidden.html', 403)

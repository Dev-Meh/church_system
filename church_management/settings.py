"""
Django settings for church_management project.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

_INSECURE_DEV_SECRET = 'django-insecure-y5==$h6-5!)y&dreww3-hfq9bjg_wb%fb9hh2io0mqarxo2=-f'
SECRET_KEY = os.getenv('SECRET_KEY', _INSECURE_DEV_SECRET)

DEBUG = os.getenv('DEBUG', 'True') == 'True'

if not DEBUG:
    if SECRET_KEY in (_INSECURE_DEV_SECRET, '', 'your-secret-key-here', 'badilisha-na-token-refu-random'):
        raise ImproperlyConfigured(
            'Set a strong unique SECRET_KEY in .env before running with DEBUG=False.'
        )
    if 'runserver' in sys.argv and os.getenv('ALLOW_INSECURE_RUNSERVER') != '1':
        raise ImproperlyConfigured(
            'Do not use runserver in production. Use gunicorn + DEBUG=False.'
        )

_allowed_hosts = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1')
ALLOWED_HOSTS = [h.strip() for h in _allowed_hosts.split(',') if h.strip()]

_csrf_origins = os.getenv('CSRF_TRUSTED_ORIGINS', '')
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_origins.split(',') if o.strip()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',  # NEW: Django REST Framework
    'rest_framework.authtoken',  # NEW: Token Authentication
    'members',
    'events',
    'donations',
    'prayers',
    'sermons',
    'communications',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'members.middleware.SecurityHeadersMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'members.middleware.PreventAuthenticatedPageCacheMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'church_management.urls'

# ✅ FIXED: Only ONE TEMPLATES setting
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # 👈 global templates folder
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'members.context_processors.language_context',
                'members.context_processors.church_permissions_context',
                'members.context_processors.app_shell_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'church_management.wsgi.application'

_db_engine = os.getenv('DB_ENGINE', 'django.db.backends.sqlite3')
if _db_engine == 'django.db.backends.sqlite3':
    _db_name = BASE_DIR / os.getenv('DB_NAME', 'db.sqlite3')
else:
    _db_name = os.getenv('DB_NAME', 'church')

DATABASES = {
    'default': {
        'ENGINE': _db_engine,
        'NAME': _db_name,
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', '12345'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},    # minimum 8 characters
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en'

LANGUAGES = [
    ('en', 'English'),
    ('sw', 'Kiswahili'),
]

TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
_static_dir = BASE_DIR / 'static'
STATICFILES_DIRS = [_static_dir] if _static_dir.is_dir() else []
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Serve uploaded files via Django when True (local dev, or if Nginx /media is not set up).
# Production: prefer Nginx alias; set SERVE_MEDIA_FILES=True as fallback.
SERVE_MEDIA_FILES = os.getenv('SERVE_MEDIA_FILES', 'True' if DEBUG else 'False') == 'True'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'members.ChurchUser'

# ── LOGIN / LOGOUT ──────────────────────────────
# Njia ya kuingia (si "/members/login/" wazi). Badilisha kwenye production.
LOGIN_URL_PATH = os.getenv('LOGIN_URL_PATH', 'phm-kuingia-a8f2/').strip().lstrip('/')
if LOGIN_URL_PATH and not LOGIN_URL_PATH.endswith('/'):
    LOGIN_URL_PATH = f'{LOGIN_URL_PATH}/'
LOGIN_URL = f'/{LOGIN_URL_PATH}'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = LOGIN_URL

# Email (password reset) — console in development
EMAIL_BACKEND = os.getenv(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend',
)
EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'PHM-ARCC <noreply@phm-arcc.local>')

# ── ADMIN URL (badilisha kwenye production) ─────
ADMIN_URL = os.getenv('ADMIN_URL', 'admin/').strip()
if ADMIN_URL and not ADMIN_URL.endswith('/'):
    ADMIN_URL = f'{ADMIN_URL}/'

# ── SESSION SECURITY ────────────────────────────
SESSION_COOKIE_AGE = int(os.getenv('SESSION_COOKIE_AGE', '1800'))
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_NAME = os.getenv('SESSION_COOKIE_NAME', 'phmarcc_sessionid')

# ── CSRF PROTECTION ─────────────────────────────
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = os.getenv('CSRF_COOKIE_SAMESITE', 'Lax')
CSRF_FAILURE_VIEW = 'members.views.csrf_failure'
CSRF_USE_SESSIONS = False

# ── CLICKJACKING / MIME SNIFFING ────────────────
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True

# ── UPLOAD LIMITS ───────────────────────────────
DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.getenv('DATA_UPLOAD_MAX_MEMORY_SIZE', str(5 * 1024 * 1024)))
FILE_UPLOAD_MAX_MEMORY_SIZE = int(os.getenv('FILE_UPLOAD_MAX_MEMORY_SIZE', str(5 * 1024 * 1024)))

# ── AUTH RATE LIMITS (brute-force protection) ───
LOGIN_RATE_LIMIT_ATTEMPTS = int(os.getenv('LOGIN_RATE_LIMIT_ATTEMPTS', '5'))
LOGIN_RATE_LIMIT_LOCKOUT = int(os.getenv('LOGIN_RATE_LIMIT_LOCKOUT', '900'))
PASSWORD_RESET_RATE_LIMIT_ATTEMPTS = int(os.getenv('PASSWORD_RESET_RATE_LIMIT_ATTEMPTS', '3'))
PASSWORD_RESET_RATE_LIMIT_WINDOW = int(os.getenv('PASSWORD_RESET_RATE_LIMIT_WINDOW', '3600'))
REGISTER_RATE_LIMIT_ATTEMPTS = int(os.getenv('REGISTER_RATE_LIMIT_ATTEMPTS', '5'))
REGISTER_RATE_LIMIT_WINDOW = int(os.getenv('REGISTER_RATE_LIMIT_WINDOW', '3600'))

# ── HTTP SECURITY HEADERS ───────────────────────
SECURITY_HEADERS_ENABLED = os.getenv('SECURITY_HEADERS_ENABLED', 'True') == 'True'
CONTENT_SECURITY_POLICY = os.getenv(
    'CONTENT_SECURITY_POLICY',
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
    "font-src 'self' https://cdnjs.cloudflare.com; "
    "img-src 'self' data: blob:; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'",
)
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    # Default False = HTTP (IP) hadi SSL imewashwa; weka True kwenye .env baada ya Certbot
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False') == 'True'
    CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'False') == 'True'
    SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False') == 'True'
    if SECURE_SSL_REDIRECT:
        SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '31536000'))
        SECURE_HSTS_INCLUDE_SUBDOMAINS = (
            os.getenv('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'True') == 'True'
        )
        SECURE_HSTS_PRELOAD = os.getenv('SECURE_HSTS_PRELOAD', 'False') == 'True'
        if SESSION_COOKIE_SECURE:
            SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Strict')
else:
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_SSL_REDIRECT = False

# ── SMS CONFIGURATION ───────────────────────────
# Beem SMS API Configuration (Tanzania SMS provider)
SMS_API_KEY = os.getenv('SMS_API_KEY', '')
SMS_API_SECRET = os.getenv('SMS_API_SECRET', '')
SMS_API_URL = 'https://apisms.beem.africa/public/v1/send-sms'
SMS_SENDER_ID = os.getenv('SMS_SENDER_ID', 'PHM-ARCC')

# Development mode - set to False in production
SMS_DEVELOPMENT_MODE = os.getenv('SMS_DEVELOPMENT_MODE', 'True') == 'True'

# ── TWILIO SMS CONFIGURATION ────────────────────
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_MESSAGING_SERVICE_SID = os.getenv('TWILIO_SERVICE_ID')  # Using TWILIO_SERVICE_ID as messaging service SID
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

# ── DJANGO REST FRAMEWORK ───────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': os.getenv('API_THROTTLE_ANON', '30/hour'),
        'user': os.getenv('API_THROTTLE_USER', '300/hour'),
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# ── LOGGING (errors kwenye production) ──────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
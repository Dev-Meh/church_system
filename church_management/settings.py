"""
Django settings for church_management project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-y5==$h6-5!)y&dreww3-hfq9bjg_wb%fb9hh2io0mqarxo2=-f')

DEBUG = os.getenv('DEBUG', 'True') == 'True'

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
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
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

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'members.ChurchUser'

# ── LOGIN / LOGOUT ──────────────────────────────
LOGIN_URL = '/members/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/members/login/'

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

# ── SESSION SECURITY ────────────────────────────
SESSION_COOKIE_AGE = 1800              # session expires after 30 minutes
SESSION_EXPIRE_AT_BROWSER_CLOSE = True # session dies when browser closes
SESSION_COOKIE_HTTPONLY = True         # JS cannot access session cookie
SESSION_COOKIE_SAMESITE = 'Lax'       # protects against CSRF attacks

# ── CSRF PROTECTION ─────────────────────────────
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'

# ── CLICKJACKING PROTECTION ─────────────────────
X_FRAME_OPTIONS = 'DENY'

# ── CONTENT SECURITY ────────────────────────────
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False') == 'True'
    CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'False') == 'True'
    SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False') == 'True'

# ── SMS CONFIGURATION ───────────────────────────
# Beem SMS API Configuration (Tanzania SMS provider)
SMS_API_KEY = os.getenv('SMS_API_KEY', '6e951d16009ae944')
SMS_API_SECRET = os.getenv('SMS_API_SECRET', 'YjZlMDk0NTA3Njk1Njc1MjJjNjNjMDYzNTMwMzgxNTUzZmY3OTE5MzNmNGNjMWM4M2M0YTU4MWRlMDViNTJjOA==')
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
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
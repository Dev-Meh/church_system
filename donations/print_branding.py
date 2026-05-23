from pathlib import Path

from django.conf import settings

CHURCH_LOGO_CANDIDATES = (
    'church-logo.svg',
    'church-logo.jpeg',
    'church-logo.jpg',
    'church-logo.png',
)


def get_church_logo_url():
    media_root = Path(settings.MEDIA_ROOT)
    for filename in CHURCH_LOGO_CANDIDATES:
        if (media_root / filename).is_file():
            return f'{settings.MEDIA_URL}{filename}'
    return f'{settings.MEDIA_URL}church-logo.svg'


def church_print_context(**extra):
    church_name = getattr(
        settings,
        'CHURCH_PRINT_NAME',
        'PENTECOSTAL HOLINESS MISSION',
    )
    return {
        'church_name': church_name,
        'church_logo_url': get_church_logo_url(),
        **extra,
    }

"""
Shared helpers for local bootstrap scripts (create_superadmin, create_pastor_user, etc.).

Passwords must NEVER be hardcoded. Set them in .env (gitignored) or enter at the prompt.
"""
from __future__ import annotations

import getpass
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def load_env() -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv(BASE_DIR / '.env')
    except ImportError:
        pass


def setup_django() -> None:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'church_management.settings')
    import django
    django.setup()


def require_password(env_key: str, prompt_label: str) -> str:
    """Read password from environment or secure prompt (never from source code)."""
    password = (os.environ.get(env_key) or '').strip()
    if password:
        return password

    if not sys.stdin.isatty():
        print(
            f'Error: set {env_key} in your .env file (see .env.example). '
            'Non-interactive runs cannot prompt for a password.',
            file=sys.stderr,
        )
        sys.exit(1)

    password = getpass.getpass(f'{prompt_label} (input hidden): ')
    if not password:
        print(f'Error: password required. Set {env_key} in .env or enter when prompted.', file=sys.stderr)
        sys.exit(1)
    confirm = getpass.getpass('Confirm password: ')
    if password != confirm:
        print('Error: passwords do not match.', file=sys.stderr)
        sys.exit(1)
    return password


def env_flag(name: str) -> bool:
    return os.environ.get(name, '').strip().lower() in ('1', 'true', 'yes', 'on')

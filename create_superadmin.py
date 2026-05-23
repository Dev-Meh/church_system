#!/usr/bin/env python
"""
Create the initial church admin user (local / first deploy only).

Set CHURCH_ADMIN_PASSWORD in .env — never commit real passwords to git.
Optional: CHURCH_ADMIN_USERNAME, CHURCH_ADMIN_EMAIL, CHURCH_ADMIN_RESET=1 to update password.
"""
import os

from user_bootstrap import env_flag, load_env, require_password, setup_django

load_env()
setup_django()

from django.contrib.auth import get_user_model

User = get_user_model()

username = (os.environ.get('CHURCH_ADMIN_USERNAME') or 'admin').strip()
email = (os.environ.get('CHURCH_ADMIN_EMAIL') or 'admin@church.com').strip()

existing = User.objects.filter(username=username).first()
if existing and not env_flag('CHURCH_ADMIN_RESET'):
    print(f"User '{username}' already exists. Set CHURCH_ADMIN_RESET=1 in .env to change password.")
    raise SystemExit(0)

password = require_password('CHURCH_ADMIN_PASSWORD', f'Password for admin "{username}"')

if existing:
    existing.set_password(password)
    existing.role = 'admin'
    existing.is_staff = True
    existing.is_superuser = True
    existing.save()
    print(f"Admin '{username}' password updated.")
else:
    User.objects.create_superuser(
        username=username,
        email=email,
        password=password,
        first_name=os.environ.get('CHURCH_ADMIN_FIRST_NAME', 'Admin'),
        last_name=os.environ.get('CHURCH_ADMIN_LAST_NAME', 'User'),
        role='admin',
        is_staff=True,
    )
    print(f"Admin '{username}' created ({email}).")
print('Credentials were not printed — use the password you set in .env or entered at the prompt.')

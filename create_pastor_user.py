#!/usr/bin/env python
"""
Create a verified pastor bootstrap user (local / staging only).

Set CHURCH_PASTOR_PASSWORD in .env — never commit real passwords to git.
Optional: CHURCH_PASTOR_USERNAME, CHURCH_PASTOR_EMAIL, CHURCH_PASTOR_RESET=1
"""
import os

from user_bootstrap import env_flag, load_env, require_password, setup_django

load_env()
setup_django()

from django.contrib.auth import get_user_model

User = get_user_model()

username = (os.environ.get('CHURCH_PASTOR_USERNAME') or 'pastor').strip()
email = (os.environ.get('CHURCH_PASTOR_EMAIL') or 'pastor@church.com').strip()

existing = User.objects.filter(username=username).first()
if existing and not env_flag('CHURCH_PASTOR_RESET'):
    print(f"Pastor '{username}' already exists. Set CHURCH_PASTOR_RESET=1 in .env to change password.")
    raise SystemExit(0)

password = require_password('CHURCH_PASTOR_PASSWORD', f'Password for pastor "{username}"')

if existing:
    existing.set_password(password)
    existing.role = 'pastor'
    existing.is_staff = True
    existing.is_verified_pastor = True
    existing.save()
    print(f"Pastor '{username}' password updated.")
else:
    User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=os.environ.get('CHURCH_PASTOR_FIRST_NAME', 'John'),
        last_name=os.environ.get('CHURCH_PASTOR_LAST_NAME', 'Pastor'),
        role='pastor',
        is_staff=True,
        is_verified_pastor=True,
    )
    print(f"Pastor '{username}' created ({email}), verified.")
print('Credentials were not printed — use the password you set in .env or entered at the prompt.')

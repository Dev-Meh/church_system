#!/usr/bin/env python
"""
Create a member bootstrap user (local / staging only).

Set CHURCH_MEMBER_PASSWORD in .env — never commit real passwords to git.
Optional: CHURCH_MEMBER_USERNAME, CHURCH_MEMBER_EMAIL, CHURCH_MEMBER_RESET=1
"""
import os

from user_bootstrap import env_flag, load_env, require_password, setup_django

load_env()
setup_django()

from django.contrib.auth import get_user_model

User = get_user_model()

username = (os.environ.get('CHURCH_MEMBER_USERNAME') or 'member').strip()
email = (os.environ.get('CHURCH_MEMBER_EMAIL') or 'member@church.com').strip()

existing = User.objects.filter(username=username).first()
if existing and not env_flag('CHURCH_MEMBER_RESET'):
    print(f"Member '{username}' already exists. Set CHURCH_MEMBER_RESET=1 in .env to change password.")
    raise SystemExit(0)

password = require_password('CHURCH_MEMBER_PASSWORD', f'Password for member "{username}"')

if existing:
    existing.set_password(password)
    existing.role = 'member'
    existing.save()
    print(f"Member '{username}' password updated.")
else:
    User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=os.environ.get('CHURCH_MEMBER_FIRST_NAME', 'Jane'),
        last_name=os.environ.get('CHURCH_MEMBER_LAST_NAME', 'Member'),
        role='member',
    )
    print(f"Member '{username}' created ({email}).")
print('Credentials were not printed — use the password you set in .env or entered at the prompt.')

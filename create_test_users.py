#!/usr/bin/env python
"""
DEV ONLY: create sample pastor/member accounts for local testing.

Requires passwords in .env (never commit real values):
  CHURCH_DEV_PASTOR_PASSWORD
  CHURCH_DEV_MEMBER_PASSWORD

Do not run this in production.
"""
import os
import sys

from user_bootstrap import load_env, require_password, setup_django

if os.environ.get('DJANGO_DEBUG', '').lower() == 'false' or os.environ.get('ENVIRONMENT') == 'production':
    print('Refusing to create test users: not a local/dev environment.', file=sys.stderr)
    sys.exit(1)

load_env()
setup_django()

from members.models import ChurchUser


def create_user(username, password, first_name, last_name, role):
    extra = {'is_verified_pastor': True} if role == 'pastor' else {}
    if not ChurchUser.objects.filter(username=username).exists():
        ChurchUser.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_staff=role in ('pastor', 'admin'),
            **extra,
        )
        print(f'User {username} created as {role}.')
    else:
        print(f'User {username} already exists.')


pastor_password = require_password('CHURCH_DEV_PASTOR_PASSWORD', 'Dev pastor password')
member_password = require_password('CHURCH_DEV_MEMBER_PASSWORD', 'Dev member password')

create_user('pastor1', pastor_password, 'John', 'Pastor', 'pastor')
create_user('member1', member_password, 'Jane', 'Member', 'member')

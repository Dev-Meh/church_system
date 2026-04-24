#!/usr/bin/env python
import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'church_management.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Check if member user already exists
if User.objects.filter(username='member').exists():
    print("Member user 'member' already exists.")
else:
    # Create member user
    User.objects.create_user(
        username='member',
        email='member@church.com',
        password='member123',
        first_name='Jane',
        last_name='Member',
        role='member'
    )
    print("Member user 'member' created successfully!")
    print("Username: member")
    print("Password: member123")
    print("Email: member@church.com")

#!/usr/bin/env python
import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'church_management.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Check if pastor user already exists
if User.objects.filter(username='pastor').exists():
    print("Pastor user 'pastor' already exists.")
else:
    # Create pastor user
    User.objects.create_user(
        username='pastor',
        email='pastor@church.com',
        password='pastor123',
        first_name='John',
        last_name='Pastor',
        role='pastor'
    )
    print("Pastor user 'pastor' created successfully!")
    print("Username: pastor")
    print("Password: pastor123")
    print("Email: pastor@church.com")

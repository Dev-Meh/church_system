#!/usr/bin/env python
import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'church_management.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Check if superuser already exists
if User.objects.filter(username='admin').exists():
    print("Superuser 'admin' already exists.")
else:
    # Create superuser
    User.objects.create_superuser(
        username='admin',
        email='admin@church.com',
        password='admin123',
        first_name='Admin',
        last_name='User',
        role='admin'
    )
    print("Superuser 'admin' created successfully!")
    print("Username: admin")
    print("Password: admin123")
    print("Email: admin@church.com")

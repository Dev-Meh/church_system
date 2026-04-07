import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'church_management.settings')
django.setup()

from members.models import ChurchUser

def create_user(username, password, first_name, last_name, role):
    if not ChurchUser.objects.filter(username=username).exists():
        user = ChurchUser.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_staff=True if role in ['pastor', 'admin'] else False
        )
        print(f"User {username} created as {role}.")
        return user
    else:
        user = ChurchUser.objects.get(username=username)
        print(f"User {username} already exists.")
        return user

# Create Pastor
create_user('pastor1', 'pastor123', 'John', 'Pastor', 'pastor')

# Create Member
create_user('member1', 'member123', 'Jane', 'Member', 'member')

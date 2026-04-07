import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'church_management.settings')
django.setup()

from members.sms_service import sms_service

def test_sms():
    print("Testing SMS Service (Development Mode)...")
    phone = "0748398259"  # Testing with the phone from .env
    message = "Test message from Church Management System."
    
    result = sms_service.send_sms(phone, message)
    print(f"Result: {result}")

if __name__ == "__main__":
    test_sms()

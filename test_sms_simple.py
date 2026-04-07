import logging
from unittest.mock import MagicMock

# Mock Django settings
class MockSettings:
    TWILIO_ACCOUNT_SID = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    TWILIO_AUTH_TOKEN = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    TWILIO_MESSAGING_SERVICE_SID = "MGxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    TWILIO_PHONE_NUMBER = "+255123456789"
    SMS_DEVELOPMENT_MODE = True

import sys
from types import ModuleType

# Create a mock django.conf module
django_conf = ModuleType('django.conf')
django_conf.settings = MockSettings()
sys.modules['django.conf'] = django_conf

# Create a mock django.contrib.messages module (just in case)
django_messages = ModuleType('django.contrib.messages')
sys.modules['django.contrib.messages'] = django_messages

# Now import the service
from members.sms_service import SMSService

def test_sms_logic():
    print("Testing SMS Logic (Mocked Settings)...")
    service = SMSService()
    phone = "0748398259"
    message = "Test message from Church Management System."
    
    # Test formatting
    formatted = service.format_phone_number(phone)
    print(f"Formatted Phone: {formatted}")
    
    # Test send (dev mode)
    result = service.send_sms(phone, message)
    print(f"Result: {result}")
    
    if result['success'] and "SMS logged" in result['message']:
        print("SUCCESS: SMS logic verified in development mode.")
    else:
        print("FAILURE: SMS logic failed.")

if __name__ == "__main__":
    test_sms_logic()

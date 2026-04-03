import urllib.request
import urllib.parse
import json
import base64
import logging
from django.conf import settings
from django.contrib import messages

logger = logging.getLogger(__name__)

class SMSService:
    """SMS service for sending messages to church members using Beem API"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'SMS_API_KEY', None)
        self.api_secret = getattr(settings, 'SMS_API_SECRET', None)
        self.api_url = getattr(settings, 'SMS_API_URL', None)
        self.sender_id = getattr(settings, 'SMS_SENDER_ID', 'PHM-ARCC')
        self.development_mode = getattr(settings, 'SMS_DEVELOPMENT_MODE', True)
    
    def send_sms(self, phone_number, message_text):
        """Send SMS to a single phone number using Beem API"""
        try:
            # For development/testing, just log the SMS
            if self.development_mode or not self.api_key or not self.api_secret or not self.api_url:
                logger.info(f"SMS would be sent to {phone_number}: {message_text}")
                return {'success': True, 'message': 'SMS logged (development mode)'}
            
            # Format phone number for Beem API
            formatted_phone = self.format_phone_number(phone_number)
            
            # Try different payload formats for Beem
            # Format 1: Original format
            payload1 = {
                'source_addr': self.sender_id,
                'encoding': '0',
                'schedule_time': '',
                'message': message_text,
                'recipients': [
                    {
                        'recipient_id': '1',
                        'dest_addr': formatted_phone
                    }
                ]
            }
            
            # Format 2: Simpler format
            payload2 = {
                'api_key': self.api_key,
                'secret_key': self.api_secret,
                'sender': self.sender_id,
                'message': message_text,
                'recipients': formatted_phone
            }
            
            # Format 3: Beem standard format
            payload3 = {
                'source_addr': self.sender_id,
                'message': message_text,
                'recipients': formatted_phone
            }
            
            # Create authentication header
            auth_string = f"{self.api_key}:{self.api_secret}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            # Try payload 1 first (original format)
            data = json.dumps(payload1).encode('utf-8')
            req = urllib.request.Request(
                self.api_url,
                data=data,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Basic {auth_b64}'
                }
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = response.read().decode('utf-8')
                result = json.loads(response_data)
                
                # Log the full response for debugging
                logger.info(f"Beem API response: {result}")
                logger.info(f"Beem API status code: {response.status}")
                
                # Check Beem API response format
                if result.get('code') == 100:
                    logger.info(f"SMS sent successfully to {formatted_phone}")
                    return {'success': True, 'message': 'SMS sent successfully'}
                elif result.get('success') == True:
                    logger.info(f"SMS sent successfully to {formatted_phone}")
                    return {'success': True, 'message': 'SMS sent successfully'}
                elif result.get('status') == 'success':
                    logger.info(f"SMS sent successfully to {formatted_phone}")
                    return {'success': True, 'message': 'SMS sent successfully'}
                else:
                    error_msg = result.get('message', result.get('description', f'Unknown error: {result}'))
                    logger.error(f"Beem API error: {error_msg}")
                    return {'success': False, 'message': error_msg}
                
        except urllib.error.URLError as e:
            logger.error(f"SMS network error: {str(e)}")
            return {'success': False, 'message': 'SMS network error'}
        except json.JSONDecodeError as e:
            logger.error(f"SMS response JSON error: {str(e)}")
            return {'success': False, 'message': 'SMS response error'}
        except Exception as e:
            logger.error(f"Unexpected SMS error: {str(e)}")
            return {'success': False, 'message': 'SMS sending failed'}
    
    def format_phone_number(self, phone_number):
        """Format phone number for Beem API (Tanzania format)"""
        # Remove all non-digit characters
        digits_only = ''.join(filter(str.isdigit, str(phone_number)))
        
        # Format for Beem API (should start with 255 for Tanzania)
        if digits_only.startswith('255'):
            # Already starts with 255, return as-is
            return digits_only
        elif phone_number.startswith('+255'):
            # Already has +255, remove + and return
            return digits_only
        elif digits_only.startswith('0') and len(digits_only) == 10:
            # Remove leading 0 and add 255 (e.g., 0712345678 → 255712345678)
            return '255' + digits_only[1:]
        elif len(digits_only) == 9 and digits_only.startswith(('6', '7')):
            # Add 255 prefix for Tanzania mobile numbers (e.g., 712345678 → 255712345678)
            return '255' + digits_only
        else:
            # Unknown format, return as-is
            return digits_only
    
    def send_bulk_sms(self, phone_numbers, message_text):
        """Send SMS to multiple phone numbers using Beem API"""
        results = []
        for phone in phone_numbers:
            if phone:  # Only send if phone number exists
                result = self.send_sms(phone, message_text)
                results.append({
                    'phone': phone,
                    'success': result['success'],
                    'message': result['message']
                })
        return results

# Create global SMS service instance
sms_service = SMSService()

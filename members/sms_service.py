import logging
from twilio.rest import Client
from django.conf import settings

logger = logging.getLogger(__name__)

class SMSService:
    """SMS service for sending messages to church members using Twilio API"""
    
    def __init__(self):
        self.account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        self.auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        self.messaging_service_sid = getattr(settings, 'TWILIO_MESSAGING_SERVICE_SID', None)
        self.twilio_phone_number = getattr(settings, 'TWILIO_PHONE_NUMBER', None)
        self.development_mode = getattr(settings, 'SMS_DEVELOPMENT_MODE', True)
        
        self.client = None
        if self.account_sid and self.auth_token:
            try:
                self.client = Client(self.account_sid, self.auth_token)
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {str(e)}")
    
    def send_sms(self, phone_number, message_text):
        """Send SMS to a single phone number using Twilio"""
        try:
            if self.development_mode:
                logger.info(f"SMS DEVELOPMENT MODE: Would be sent to {phone_number}: {message_text}")
                return {'success': True, 'message': 'SMS logged (development mode)'}
            
            if not self.client:
                logger.error("Twilio client not initialized. Check credentials.")
                return {'success': False, 'message': 'SMS service not configured'}

            # Prepare message parameters
            msg_params = {
                'to': self.format_phone_number(phone_number),
                'body': message_text
            }
            
            # Use Messaging Service SID if available, otherwise use phone number
            if self.messaging_service_sid:
                msg_params['messaging_service_sid'] = self.messaging_service_sid
            elif self.twilio_phone_number:
                msg_params['from_'] = self.twilio_phone_number
            else:
                logger.error("Neither Twilio Phone Number nor Messaging Service SID is configured.")
                return {'success': False, 'message': 'SMS sender not configured'}

            # Send via Twilio
            message = self.client.messages.create(**msg_params)
            
            logger.info(f"SMS sent successfully to {phone_number}. SID: {message.sid}")
            return {'success': True, 'sid': message.sid}
            
        except Exception as e:
            logger.error(f"Twilio SMS error: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    def format_phone_number(self, phone_number):
        """Format phone number for Twilio (E.164 format)"""
        if not phone_number:
            return None
            
        # Remove all non-digit characters
        digits_only = ''.join(filter(str.isdigit, str(phone_number)))
        
        # If it already looks like E.164 (starts with +), just return it
        if str(phone_number).startswith('+'):
            return str(phone_number)
            
        # Handle TZ numbers (assuming Tanzania if no prefix)
        if digits_only.startswith('255'):
            return '+' + digits_only
        elif digits_only.startswith('0') and len(digits_only) == 10:
            return '+255' + digits_only[1:]
        elif len(digits_only) == 9:
            return '+255' + digits_only
            
        # Default fallback: add + if missing
        return '+' + digits_only if not digits_only.startswith('+') else digits_only
    
    def send_bulk_sms(self, phone_numbers, message_text):
        """Send SMS to multiple phone numbers using Twilio"""
        results = []
        for phone in phone_numbers:
            if phone:
                result = self.send_sms(phone, message_text)
                results.append({
                    'phone': phone,
                    'success': result['success'],
                    'message': result.get('message', 'Sent')
                })
        return results

# Create global SMS service instance
sms_service = SMSService()

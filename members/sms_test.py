import urllib.request
import urllib.parse
import json
import base64
import logging

logger = logging.getLogger(__name__)

def test_beem_sms():
    """Test Beem SMS API with your credentials"""
    
    # Your Beem credentials
    api_key = '6e951d16009ae944'
    api_secret = 'YjZlMDk0NTA3Njk1Njc1MjJjNjNjMDYzNTMwMzgxNTUzZmY3OTE5MzNmNGNjMWM4M2M0YTU4MWRlMDViNTJjOA=='
    api_url = 'https://apisms.beem.africa/public/v1/send-sms'
    sender_id = 'PHM-ARCC'
    
    # Test phone number (replace with your actual test number)
    test_phone = '255712345678'  # Replace with your phone number
    
    # Format phone number
    digits_only = ''.join(filter(str.isdigit, str(test_phone)))
    if not digits_only.startswith('255') and len(digits_only) == 9 and digits_only.startswith(('6', '7')):
        formatted_phone = '255' + digits_only
    else:
        formatted_phone = digits_only
    
    # Prepare payload
    payload = {
        'source_addr': sender_id,
        'encoding': '0',
        'schedule_time': '',
        'message': 'Test message from PHM-ARCC Church Management System',
        'recipients': [
            {
                'recipient_id': '1',
                'dest_addr': formatted_phone
            }
        ]
    }
    
    try:
        # Create authentication header
        auth_string = f"{api_key}:{api_secret}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        # Send request
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            api_url,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Basic {auth_b64}'
            }
        )
        
        print("Sending SMS with the following data:")
        print(f"URL: {api_url}")
        print(f"Phone: {formatted_phone}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        print(f"Auth: Basic {auth_b64[:20]}...")
        
        with urllib.request.urlopen(req, timeout=30) as response:
            response_data = response.read().decode('utf-8')
            result = json.loads(response_data)
            
            print(f"\nResponse Status: {response.status}")
            print(f"Response Data: {json.dumps(result, indent=2)}")
            
            # Check response
            if result.get('code') == 100:
                print("✅ SMS sent successfully!")
            elif result.get('success') == True:
                print("✅ SMS sent successfully!")
            else:
                error_msg = result.get('message', result.get('description', 'Unknown error'))
                print(f"❌ SMS failed: {error_msg}")
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_beem_sms()

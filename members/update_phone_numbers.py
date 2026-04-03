import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'church_management.settings')
django.setup()

from members.models import ChurchUser

def update_phone_numbers():
    """Update all member phone numbers to start with +255 and remove leading 0"""
    
    print("Starting phone number update process...")
    
    # Get all members with phone numbers
    members = ChurchUser.objects.filter(phone_number__isnull=False).exclude(phone_number='')
    
    print(f"Found {members.count()} members with phone numbers")
    
    updated_count = 0
    errors = []
    
    for member in members:
        try:
            original_phone = member.phone_number
            if not original_phone:
                continue
                
            print(f"\nProcessing: {member.first_name} {member.last_name}")
            print(f"Original phone: {original_phone}")
            
            # Remove all non-digit characters
            digits_only = ''.join(filter(str.isdigit, str(original_phone)))
            print(f"Digits only: {digits_only}")
            
            # Format phone number
            if digits_only.startswith('255'):
                # Already starts with 255, just add +
                new_phone = '+' + digits_only
            elif digits_only.startswith('0') and len(digits_only) == 10:
                # Remove leading 0 and add 255
                new_phone = '+255' + digits_only[1:]
            elif len(digits_only) == 9 and digits_only.startswith(('6', '7')):
                # Add 255 prefix (Tanzania mobile)
                new_phone = '+255' + digits_only
            else:
                # Unknown format, just add +
                new_phone = '+' + digits_only if not digits_only.startswith('+') else digits_only
            
            print(f"New phone: {new_phone}")
            
            # Update the member's phone number
            member.phone_number = new_phone
            member.save()
            
            updated_count += 1
            print(f"✅ Updated successfully")
            
        except Exception as e:
            error_msg = f"Error updating {member.first_name} {member.last_name}: {str(e)}"
            errors.append(error_msg)
            print(f"❌ {error_msg}")
    
    print(f"\n" + "="*50)
    print(f"UPDATE SUMMARY:")
    print(f"Total members processed: {members.count()}")
    print(f"Successfully updated: {updated_count}")
    print(f"Errors: {len(errors)}")
    
    if errors:
        print(f"\nERRORS:")
        for error in errors:
            print(f"  - {error}")
    
    print(f"\nPhone number update process completed!")

if __name__ == "__main__":
    update_phone_numbers()

from django import forms
from .models import ChurchUser
from .models_message import Message, Announcement

class MessageForm(forms.ModelForm):
    """Form for pastors to create messages"""
    
    class Meta:
        model = Message
        fields = ['title', 'content', 'priority', 'send_to_all', 'target_roles']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Message title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Write your message here...'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control'
            }),
            'send_to_all': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'target_roles': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., member,pastor,elder (leave blank for all)'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['target_roles'].help_text = "Comma-separated roles. Leave blank if sending to all members."
        
    def clean(self):
        cleaned_data = super().clean()
        
        # If not sending to all, target_roles is required
        if not cleaned_data.get('send_to_all') and not cleaned_data.get('target_roles'):
            raise forms.ValidationError(
                "Either 'Send to all' must be checked or target roles must be specified."
            )
        
        # Validate target roles
        target_roles = cleaned_data.get('target_roles', '')
        if target_roles:
            valid_roles = [choice[0] for choice in ChurchUser.ROLE_CHOICES]
            role_list = [role.strip() for role in target_roles.split(',')]
            
            for role in role_list:
                if role not in valid_roles:
                    raise forms.ValidationError(
                        f"Invalid role: '{role}'. Valid roles: {', '.join(valid_roles)}"
                    )
        
        return cleaned_data

class AnnouncementForm(forms.ModelForm):
    """Form for creating public announcements"""
    
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'priority', 'expires_at']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Announcement title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Write your announcement here...'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control'
            }),
            'expires_at': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            })
        }

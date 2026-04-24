from django import forms
from django.utils import timezone
from .models import Event, EventRegistration, EventResource
from members.models import ChurchUser

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'event_type', 'start_date', 'end_date',
            'location', 'frequency', 'is_recurring', 'max_participants',
            'registration_required', 'registration_deadline', 'image',
            'speakers', 'is_published'
        ]
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'date'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'date'}),
            'registration_deadline': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-textarea'}),
            'speakers': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['speakers'].queryset = ChurchUser.objects.filter(
            role__in=['pastor', 'elder', 'deacon']
        )
        self.fields['image'].required = False
        
        # Add better error messages for date fields
        self.fields['start_date'].error_messages = {
            'required': 'Start date and time are required.',
            'invalid': 'Please enter a valid start date and time.',
        }
        self.fields['end_date'].error_messages = {
            'required': 'End date and time are required.',
            'invalid': 'Please enter a valid end date and time.',
        }
        self.fields['registration_deadline'].error_messages = {
            'invalid': 'Please enter a valid registration deadline.',
        }

    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        if not start_date:
            raise forms.ValidationError("Start date and time are required.")
        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data.get('end_date')
        if not end_date:
            raise forms.ValidationError("End date and time are required.")
        return end_date

    def clean_registration_deadline(self):
        registration_deadline = self.cleaned_data.get('registration_deadline')
        if registration_deadline:
            from django.utils import timezone
            if registration_deadline < timezone.now():
                raise forms.ValidationError("Registration deadline cannot be in the past.")
        return registration_deadline

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        registration_deadline = cleaned_data.get('registration_deadline')

        # Check if start_date is provided and valid
        if not start_date:
            raise forms.ValidationError("Start date and time are required.")
        
        # Check if end_date is provided and valid
        if not end_date:
            raise forms.ValidationError("End date and time are required.")
        
        # Validate date logic
        if start_date and end_date:
            if start_date >= end_date:
                raise forms.ValidationError("End date must be after start date.")
        
        # Validate registration deadline
        if registration_deadline and start_date:
            if registration_deadline >= start_date:
                raise forms.ValidationError("Registration deadline must be before event start date.")

        return cleaned_data

class EventRegistrationForm(forms.ModelForm):
    class Meta:
        model = EventRegistration
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Any special requirements or notes...'})
        }

class EventResourceForm(forms.ModelForm):
    class Meta:
        model = EventResource
        fields = ['title', 'description', 'resource_type', 'file', 'url']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        resource_type = cleaned_data.get('resource_type')
        file = cleaned_data.get('file')
        url = cleaned_data.get('url')

        if resource_type in ['document', 'image', 'video', 'audio'] and not file:
            raise forms.ValidationError(f"File is required for {resource_type} resources.")
        
        if resource_type == 'link' and not url:
            raise forms.ValidationError("URL is required for link resources.")

        return cleaned_data

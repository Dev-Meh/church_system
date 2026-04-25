from datetime import datetime, time

from django import forms
from django.utils import timezone
from .models import Event, EventRegistration, EventResource
from members.models import ChurchUser

class EventForm(forms.ModelForm):
    # Use date pickers only, then convert to datetime in save().
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-input', 'type': 'date'})
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-input', 'type': 'date'})
    )
    registration_deadline = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-input', 'type': 'date'})
    )

    class Meta:
        model = Event
        fields = [
            'title', 'description', 'event_type', 'start_date', 'end_date',
            'location', 'frequency', 'is_recurring', 'max_participants',
            'registration_required', 'registration_deadline', 'image',
            'speakers', 'is_published'
        ]
        widgets = {
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
            'required': 'Start date is required.',
            'invalid': 'Please choose a valid start date.',
        }
        self.fields['end_date'].error_messages = {
            'required': 'End date is required.',
            'invalid': 'Please choose a valid end date.',
        }
        self.fields['registration_deadline'].error_messages = {
            'invalid': 'Please choose a valid registration deadline.',
        }

    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        if not start_date:
            raise forms.ValidationError("Start date is required.")
        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data.get('end_date')
        if not end_date:
            raise forms.ValidationError("End date is required.")
        return end_date

    def clean_registration_deadline(self):
        registration_deadline = self.cleaned_data.get('registration_deadline')
        if registration_deadline:
            if registration_deadline < timezone.localdate():
                raise forms.ValidationError("Registration deadline cannot be in the past.")
        return registration_deadline

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        registration_deadline = cleaned_data.get('registration_deadline')

        # Check if start_date is provided and valid
        if not start_date:
            raise forms.ValidationError("Start date is required.")
        
        # Check if end_date is provided and valid
        if not end_date:
            raise forms.ValidationError("End date is required.")
        
        # Validate date logic
        if start_date and end_date:
            if start_date >= end_date:
                raise forms.ValidationError("End date must be after start date.")
        
        # Validate registration deadline
        if registration_deadline and start_date:
            if registration_deadline >= start_date:
                raise forms.ValidationError("Registration deadline must be before event start date.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        start_date = self.cleaned_data.get('start_date')
        end_date = self.cleaned_data.get('end_date')
        registration_deadline = self.cleaned_data.get('registration_deadline')

        if start_date:
            instance.start_date = timezone.make_aware(
                datetime.combine(start_date, time(hour=8, minute=0))
            )
        if end_date:
            instance.end_date = timezone.make_aware(
                datetime.combine(end_date, time(hour=18, minute=0))
            )
        if registration_deadline:
            instance.registration_deadline = timezone.make_aware(
                datetime.combine(registration_deadline, time(hour=23, minute=59))
            )
        else:
            instance.registration_deadline = None

        if commit:
            instance.save()
            self.save_m2m()
        return instance

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

from django import forms
from .models import Donation, DonationCampaign

class DonationForm(forms.ModelForm):
    class Meta:
        model = Donation
        fields = ['amount', 'payment_method', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter amount',
                'min': '1',
                'step': '0.01'
            }),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional notes about your donation'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['amount'].label = 'Donation Amount ($)'
        self.fields['payment_method'].label = 'Payment Method'
        self.fields['notes'].label = 'Notes (Optional)'
        self.fields['notes'].required = False

class CampaignForm(forms.ModelForm):
    class Meta:
        model = DonationCampaign
        fields = ['title', 'description', 'target_amount', 'start_date', 'end_date', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'target_amount': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'})
        }

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import ChurchUser

class PastorRegistrationForm(UserCreationForm):
    """Registration form for pastors with additional verification"""
    
    # Pastor-specific fields
    pastoral_license = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Pastoral License Number'
        })
    )
    
    ordination_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    ordination_church = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Church where you were ordained'
        })
    )
    
    years_in_ministry = forms.IntegerField(
        required=True,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Years in ministry'
        })
    )
    
    theology_education = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Theological Education (e.g., B.Th, M.Div)'
        })
    )
    
    ministry_specialization = forms.ChoiceField(
        choices=[
            ('senior_pastor', 'Senior Pastor'),
            ('associate_pastor', 'Associate Pastor'),
            ('youth_pastor', 'Youth Pastor'),
            ('children_pastor', 'Children Pastor'),
            ('worship_pastor', 'Worship Pastor'),
            ('outreach_pastor', 'Outreach Pastor'),
            ('other', 'Other'),
        ],
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    reference_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Reference Name (Senior Pastor or Bishop)'
        })
    )
    
    reference_email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Reference Email'
        })
    )
    
    reference_phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Reference Phone'
        })
    )
    
    # Basic info fields
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email address'
        })
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First name'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last name'
        })
    )
    
    phone_number = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone number'
        })
    )
    
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Current address'
        }),
        required=True
    )
    
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
    )
    
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    )
    
    class Meta:
        model = ChurchUser
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 
                 'address', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if ChurchUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'pastor'
        user.is_staff = True  # Pastors can access admin
        
        # Save pastor-specific info in user fields (we'll add these fields to model later)
        user.pastoral_license = self.cleaned_data['pastoral_license']
        user.ordination_date = self.cleaned_data['ordination_date']
        user.ordination_church = self.cleaned_data['ordination_church']
        user.years_in_ministry = self.cleaned_data['years_in_ministry']
        user.theology_education = self.cleaned_data['theology_education']
        user.ministry_specialization = self.cleaned_data['ministry_specialization']
        user.reference_name = self.cleaned_data['reference_name']
        user.reference_email = self.cleaned_data['reference_email']
        user.reference_phone = self.cleaned_data['reference_phone']
        
        if commit:
            user.save()
        return user

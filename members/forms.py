from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, SetPasswordForm, PasswordResetForm
from django.core.exceptions import ValidationError
from .models import ChurchUser, ChurchGroup, GroupActivity

class ChurchUserRegistrationForm(UserCreationForm):
    """Public registration: church members only."""

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
            'placeholder': 'Enter your email'
        })
    )
    phone_number = forms.CharField(
        max_length=20, 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Phone number'
        })
    )
    date_of_birth = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    gender = forms.ChoiceField(
        choices=ChurchUser.GENDER_CHOICES, 
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'rows': 3,
            'placeholder': 'Your address'
        }), 
        required=False
    )
    city = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'City'
        })
    )
    country = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Country'
        })
    )
    postal_code = forms.CharField(
        max_length=20, 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Postal code'
        })
    )
    marital_status = forms.ChoiceField(
        choices=ChurchUser.MARITAL_STATUS_CHOICES, 
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    occupation = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Occupation'
        })
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
    
    class Meta:
        model = ChurchUser
        fields = (
            'username', 'first_name', 'last_name', 'email', 'phone_number',
            'date_of_birth', 'gender', 'address', 'city', 'country',
            'postal_code', 'marital_status', 'occupation', 'password1', 'password2',
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.phone_number = self.cleaned_data.get('phone_number', '')
        user.date_of_birth = self.cleaned_data.get('date_of_birth')
        user.gender = self.cleaned_data.get('gender', '')
        user.address = self.cleaned_data.get('address', '')
        user.city = self.cleaned_data.get('city', '')
        user.country = self.cleaned_data.get('country', '')
        user.postal_code = self.cleaned_data.get('postal_code', '')
        user.marital_status = self.cleaned_data.get('marital_status', '')
        user.occupation = self.cleaned_data.get('occupation', '')
        user.role = 'member'
        user.is_staff = False
        user.is_verified_pastor = False
        if commit:
            user.save()
        return user

class ChurchUserLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'})
    )

    error_messages = {
        'invalid_login': "Invalid username or password. Please check your credentials and try again.",
        'inactive': "This account is inactive. Please contact church administration.",
    }

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not getattr(user, 'is_active_member', True):
            raise ValidationError(
                'Akaunti hii imesimamishwa. Wasiliana na mchungaji wa kanisa.',
                code='inactive',
            )


class PastorSetPasswordForm(SetPasswordForm):
    """Pastor sets a new password for a member directly."""

    new_password1 = forms.CharField(
        label='Nenosiri jipya',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )
    new_password2 = forms.CharField(
        label='Thibitisha nenosiri',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )


class ChurchPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label='Barua pepe',
        max_length=254,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email uliyosajiliwa'}),
    )

    def get_users(self, email):
        active = ChurchUser.objects.filter(
            email__iexact=email,
            is_active=True,
            is_active_member=True,
        )
        return active


class ChurchUserUpdateForm(forms.ModelForm):
    class Meta:
        model = ChurchUser
        fields = ('first_name', 'last_name', 'email', 'phone_number', 
                 'date_of_birth', 'gender', 'address', 'city', 'country', 
                 'postal_code', 'marital_status', 'occupation', 'profile_picture')
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class ChurchGroupForm(forms.ModelForm):
    class Meta:
        model = ChurchGroup
        fields = ["name", "group_type", "description", "leader", "is_active"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "group_type": forms.Select(attrs={"class": "form-control"}),
            "leader": forms.Select(attrs={"class": "form-control"}),
        }


class GroupActivityForm(forms.ModelForm):
    class Meta:
        model = GroupActivity
        fields = ["title", "description", "activity_date"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "activity_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }

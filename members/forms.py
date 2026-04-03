from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import ChurchUser
from .models_message import Message, Announcement

class ChurchUserRegistrationForm(UserCreationForm):
    """Unified registration form for both members and pastors"""
    role = forms.ChoiceField(
        choices=ChurchUser.ROLE_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'onchange': 'togglePastorFields()'
        })
    )
    
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
    
    # Pastor-specific fields (conditionally required)
    pastoral_license = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control pastor-field',
            'placeholder': 'Pastoral License Number',
            'style': 'display:none;'
        })
    )
    
    ordination_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control pastor-field',
            'style': 'display:none;'
        })
    )
    
    ordination_church = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control pastor-field',
            'placeholder': 'Church where you were ordained',
            'style': 'display:none;'
        })
    )
    
    years_in_ministry = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control pastor-field',
            'placeholder': 'Years in ministry',
            'style': 'display:none;'
        })
    )
    
    theology_education = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control pastor-field',
            'placeholder': 'Theological Education (e.g., B.Th, M.Div)',
            'style': 'display:none;'
        })
    )
    
    ministry_specialization = forms.ChoiceField(
        choices=ChurchUser.MINISTRY_SPECIALIZATION_CHOICES, 
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control pastor-field',
            'style': 'display:none;'
        })
    )
    
    reference_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control pastor-field',
            'placeholder': 'Reference Name (Senior Pastor or Bishop)',
            'style': 'display:none;'
        })
    )
    
    reference_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control pastor-field',
            'placeholder': 'Reference Email',
            'style': 'display:none;'
        })
    )
    
    reference_phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control pastor-field',
            'placeholder': 'Reference Phone',
            'style': 'display:none;'
        })
    )
    
    class Meta:
        model = ChurchUser
        fields = ('role', 'username', 'first_name', 'last_name', 'email', 'phone_number', 
                 'date_of_birth', 'gender', 'address', 'city', 'country', 
                 'postal_code', 'marital_status', 'occupation', 'password1', 'password2',
                 'pastoral_license', 'ordination_date', 'ordination_church', 'years_in_ministry',
                 'theology_education', 'ministry_specialization', 'reference_name', 
                 'reference_email', 'reference_phone')
    
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        
        # If role is pastor, validate pastor-specific fields
        if role == 'pastor':
            required_pastor_fields = [
                'pastoral_license', 'ordination_date', 'ordination_church',
                'years_in_ministry', 'theology_education', 'ministry_specialization',
                'reference_name', 'reference_email', 'reference_phone'
            ]
            
            for field in required_pastor_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, f'This field is required for pastor registration')
        
        return cleaned_data
    
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
        
        # Set role and pastor-specific fields
        user.role = self.cleaned_data['role']
        
        if user.role == 'pastor':
            user.is_staff = True  # Pastors get staff access
            user.pastoral_license = self.cleaned_data.get('pastoral_license', '')
            user.ordination_date = self.cleaned_data.get('ordination_date')
            user.ordination_church = self.cleaned_data.get('ordination_church', '')
            user.years_in_ministry = self.cleaned_data.get('years_in_ministry')
            user.theology_education = self.cleaned_data.get('theology_education', '')
            user.ministry_specialization = self.cleaned_data.get('ministry_specialization', '')
            user.reference_name = self.cleaned_data.get('reference_name', '')
            user.reference_email = self.cleaned_data.get('reference_email', '')
            user.reference_phone = self.cleaned_data.get('reference_phone', '')
        
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

class MessageForm(forms.ModelForm):
    """Form for pastors to create messages to members"""
    
    class Meta:
        model = Message
        fields = ['title', 'content', 'priority', 'send_to_all', 'target_roles']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter message title...',
                'required': True
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Write your message to church members...',
                'required': True
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control'
            }),
            'send_to_all': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'target_roles': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., member,elder,deacon (leave empty if sending to all)'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].label = 'Message Title'
        self.fields['content'].label = 'Message Content'
        self.fields['priority'].label = 'Priority Level'
        self.fields['send_to_all'].label = 'Send to All Members'
        self.fields['target_roles'].label = 'Target Specific Roles (Optional)'
        self.fields['target_roles'].help_text = 'Comma-separated roles. Only used if "Send to All" is unchecked.'
        
    def clean_target_roles(self):
        target_roles = self.cleaned_data.get('target_roles', '')
        if target_roles:
            # Validate role names
            valid_roles = ['member', 'pastor', 'elder', 'deacon', 'admin']
            roles = [role.strip() for role in target_roles.split(',')]
            for role in roles:
                if role not in valid_roles:
                    raise forms.ValidationError(f'Invalid role: {role}. Valid roles are: {", ".join(valid_roles)}')
        return target_roles

class AnnouncementForm(forms.ModelForm):
    """Form for creating public announcements"""
    
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'priority', 'expires_at']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter announcement title...',
                'required': True
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Write your announcement...',
                'required': True
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control'
            }),
            'expires_at': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].label = 'Announcement Title'
        self.fields['content'].label = 'Announcement Content'
        self.fields['priority'].label = 'Priority Level'
        self.fields['expires_at'].label = 'Expiration Date (Optional)'
        self.fields['expires_at'].help_text = 'Leave empty for no expiration'

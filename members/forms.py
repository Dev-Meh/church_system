from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, SetPasswordForm, PasswordResetForm
from django.core.exceptions import ValidationError
from .birth_date_field import MobileBirthDateField, MobileBirthDateWidget
from .language_utils import get_translation
from .models import ChurchUser, ChurchGroup, GroupActivity, UniversityStudentRecord

_GENDER_I18N = {"M": "gender_male", "F": "gender_female", "O": "gender_other"}
_MARITAL_I18N = {
    "single": "marital_single",
    "married": "marital_married",
    "divorced": "marital_divorced",
    "widowed": "marital_widowed",
}
_UNI_LEVEL_I18N = {
    "certificate": "uni_level_certificate",
    "diploma": "uni_level_diploma",
    "degree": "uni_level_degree",
    "masters": "uni_level_masters",
    "phd": "uni_level_phd",
    "other": "uni_level_other",
}

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
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email (optional)',
        }),
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone number (optional)',
        }),
    )
    date_of_birth = MobileBirthDateField(required=True)
    gender = forms.ChoiceField(
        choices=ChurchUser.GENDER_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
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

    is_university_student = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'id_is_university_student',
        }),
    )
    uni_institution = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'data-uni-field': '1',
        }),
    )
    uni_course = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'data-uni-field': '1',
        }),
    )
    uni_faculty = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'data-uni-field': '1',
        }),
    )
    uni_level = forms.ChoiceField(
        choices=UniversityStudentRecord.LEVEL_CHOICES,
        required=False,
        initial='degree',
        widget=forms.Select(attrs={'class': 'form-control', 'data-uni-field': '1'}),
    )
    uni_year_started = forms.IntegerField(
        required=False,
        min_value=1990,
        max_value=2100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1990',
            'max': '2100',
            'data-uni-field': '1',
        }),
    )
    uni_expected_completion_year = forms.IntegerField(
        required=False,
        min_value=1990,
        max_value=2100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1990',
            'max': '2100',
            'data-uni-field': '1',
        }),
    )
    uni_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'data-uni-field': '1',
        }),
    )

    class Meta:
        model = ChurchUser
        fields = (
            'username', 'first_name', 'last_name', 'email', 'phone_number',
            'date_of_birth', 'gender', 'address', 'city', 'country',
            'postal_code', 'marital_status', 'occupation', 'password1', 'password2',
        )

    def __init__(self, *args, language=None, **kwargs):
        self._language = language or 'en'
        super().__init__(*args, **kwargs)
        self._apply_registration_i18n()
        if self.data.get('is_university_student') in ('on', 'true', '1', True):
            self._require_university_fields()

    def _apply_registration_i18n(self):
        lang = self._language
        t = lambda key: get_translation(key, lang)

        placeholder_keys = {
            'username': 'ph_username',
            'email': 'ph_email',
            'phone_number': 'ph_phone',
            'password1': 'ph_password',
            'password2': 'ph_password_confirm',
            'first_name': 'ph_first_name',
            'last_name': 'ph_last_name',
            'address': 'ph_address',
            'city': 'ph_city',
            'country': 'ph_country',
            'postal_code': 'ph_postal_code',
            'occupation': 'ph_occupation',
            'uni_institution': 'ph_uni_institution',
            'uni_course': 'ph_uni_course',
            'uni_faculty': 'ph_uni_faculty',
            'uni_year_started': 'ph_uni_year',
            'uni_expected_completion_year': 'ph_uni_grad_year',
            'uni_notes': 'ph_uni_notes',
        }
        for field_name, key in placeholder_keys.items():
            if field_name in self.fields:
                self.fields[field_name].widget.attrs['placeholder'] = t(key)

        self.fields['gender'].choices = [
            (code, t(_GENDER_I18N[code])) for code, _ in ChurchUser.GENDER_CHOICES
        ]
        self.fields['gender'].empty_label = t('select_gender')
        self.fields['gender'].error_messages['required'] = t('err_gender_required')

        self.fields['marital_status'].choices = [
            (code, t(_MARITAL_I18N[code])) for code, _ in ChurchUser.MARITAL_STATUS_CHOICES
        ]
        self.fields['marital_status'].empty_label = t('select_marital')

        dob_field = self.fields['date_of_birth']
        dob_field._language = lang
        dob_field.widget = MobileBirthDateWidget(language=lang)
        dob_field.error_messages = {
            'required': t('dob_required'),
            'invalid': t('dob_invalid'),
        }

        self.fields['uni_level'].choices = [
            (code, t(_UNI_LEVEL_I18N[code])) for code, _ in UniversityStudentRecord.LEVEL_CHOICES
        ]

    def _require_university_fields(self):
        for name in ('uni_institution', 'uni_course', 'uni_level'):
            self.fields[name].required = True

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip()
        if not email:
            return ''
        if ChurchUser.objects.filter(email__iexact=email).exists():
            raise ValidationError(get_translation('err_email_exists', self._language))
        return email

    def clean_phone_number(self):
        return (self.cleaned_data.get('phone_number') or '').strip()

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('is_university_student'):
            self._require_university_fields()
            missing = []
            if not (cleaned_data.get('uni_institution') or '').strip():
                missing.append('uni_institution')
            if not (cleaned_data.get('uni_course') or '').strip():
                missing.append('uni_course')
            if not cleaned_data.get('uni_level'):
                missing.append('uni_level')
            err_msg = get_translation('err_uni_required', self._language)
            for field_name in missing:
                self.add_error(field_name, err_msg)
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email') or ''
        user.phone_number = self.cleaned_data.get('phone_number') or ''
        user.date_of_birth = self.cleaned_data['date_of_birth']
        user.gender = self.cleaned_data['gender']
        user.address = self.cleaned_data.get('address', '')
        user.city = self.cleaned_data.get('city', '')
        user.country = self.cleaned_data.get('country', '')
        user.postal_code = self.cleaned_data.get('postal_code', '')
        user.marital_status = self.cleaned_data.get('marital_status', '')
        user.occupation = self.cleaned_data.get('occupation', '')
        user.role = 'member'
        user.is_staff = False
        user.is_verified_pastor = False
        user.is_active = True
        user.is_active_member = False
        if commit:
            user.save()
            if self.cleaned_data.get('is_university_student'):
                UniversityStudentRecord.objects.create(
                    member=user,
                    institution=self.cleaned_data['uni_institution'].strip(),
                    course=self.cleaned_data['uni_course'].strip(),
                    faculty=(self.cleaned_data.get('uni_faculty') or '').strip(),
                    level=self.cleaned_data['uni_level'],
                    year_started=self.cleaned_data.get('uni_year_started'),
                    expected_completion_year=self.cleaned_data.get(
                        'uni_expected_completion_year'
                    ),
                    status='studying',
                    notes=(self.cleaned_data.get('uni_notes') or '').strip(),
                    recorded_by=None,
                )
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
            if getattr(user, 'is_active', True):
                raise ValidationError(
                    'Akaunti yako inasubiri uidhinisho wa mchungaji au msimamizi. '
                    'Utaweza kuingia baada ya kuidhinishwa.',
                    code='pending_approval',
                )
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
    MAX_PROFILE_IMAGE_BYTES = 5 * 1024 * 1024

    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'profile-file-input-hidden',
            'accept': 'image/*',
            'capture': 'user',
        }),
    )
    date_of_birth = MobileBirthDateField(required=False)

    class Meta:
        model = ChurchUser
        fields = ('first_name', 'last_name', 'email', 'phone_number',
                 'date_of_birth', 'gender', 'address', 'city', 'country',
                 'postal_code', 'marital_status', 'occupation', 'profile_picture')
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'marital_status': forms.Select(attrs={'class': 'form-control'}),
            'occupation': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_profile_picture(self):
        picture = self.cleaned_data.get('profile_picture')
        if not picture:
            return picture
        # Already stored on disk — user did not pick a new file
        if not hasattr(picture, 'read'):
            return picture
        if picture.size > self.MAX_PROFILE_IMAGE_BYTES:
            raise ValidationError('Picha ni kubwa sana. Lazima iwe chini ya 5MB.')
        try:
            from PIL import Image

            picture.seek(0)
            with Image.open(picture) as img:
                img.load()
            picture.seek(0)
        except Exception:
            raise ValidationError('Faili hii si picha. Chagua picha halisi kutoka simu.')
        return picture

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.date_of_birth:
            self.fields['date_of_birth'].initial = self.instance.date_of_birth

    def save(self, commit=True):
        """Keep existing photo when the user saves other fields without re-uploading."""
        existing_picture = self.instance.profile_picture
        had_picture = bool(existing_picture and getattr(existing_picture, 'name', None))
        instance = super().save(commit=False)
        if not self.files.get('profile_picture') and had_picture:
            instance.profile_picture = existing_picture
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class ChurchGroupForm(forms.ModelForm):
    class Meta:
        model = ChurchGroup
        fields = ["name", "group_type", "description", "leader", "is_active"]
        widgets = {
            "description": forms.Textarea(attrs={
                "rows": 3,
                "class": "form-control",
                "placeholder": "Maelezo mafupi: shughuli, siku za mkutano, n.k.",
            }),
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Mfano: Kwaya ya PHM-ARCC",
            }),
            "group_type": forms.Select(attrs={"class": "form-control"}),
            "leader": forms.Select(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "name": "Jina la kundi",
            "group_type": "Aina ya kundi",
            "description": "Maelezo",
            "leader": "Mwenyekiti wa kundi",
            "is_active": "Kundi linaendelea (hai)",
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


class UniversityStudentRecordForm(forms.ModelForm):
    class Meta:
        model = UniversityStudentRecord
        fields = [
            "member",
            "institution",
            "course",
            "faculty",
            "level",
            "year_started",
            "expected_completion_year",
            "year_completed",
            "status",
            "notes",
        ]
        widgets = {
            "member": forms.Select(attrs={"class": "form-control"}),
            "institution": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Mfano: UDOM, DUCE, ARU"}
            ),
            "course": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Mfano: Ualimu, Nursing, Law"}
            ),
            "faculty": forms.TextInput(attrs={"class": "form-control"}),
            "level": forms.Select(attrs={"class": "form-control"}),
            "year_started": forms.NumberInput(
                attrs={"class": "form-control", "min": "1990", "max": "2100"}
            ),
            "expected_completion_year": forms.NumberInput(
                attrs={"class": "form-control", "min": "1990", "max": "2100"}
            ),
            "year_completed": forms.NumberInput(
                attrs={"class": "form-control", "min": "1990", "max": "2100"}
            ),
            "status": forms.Select(attrs={"class": "form-control"}),
            "notes": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "placeholder": "Hiari"}
            ),
        }
        labels = {
            "member": "Mwanachama",
            "institution": "Chuo",
            "course": "Kozi",
            "faculty": "Ndaki",
            "level": "Kiwango cha elimu",
            "year_started": "Mwaka alianza (Novemba)",
            "expected_completion_year": "Mwaka wa kutarajiwa kuhitimu (Novemba)",
            "year_completed": "Mwaka alihitimu (Novemba)",
            "status": "Hali",
            "notes": "Maelezo",
        }

    def __init__(self, *args, language='en', **kwargs):
        super().__init__(*args, **kwargs)
        lang = language or 'en'
        self._lang = lang
        from .language_utils import get_translation as t

        self.fields["member"].queryset = ChurchUser.objects.filter(
            is_active=True,
            role="member",
        ).order_by("first_name", "last_name")
        self.fields["member"].label = t("uni_field_member", lang)
        self.fields["institution"].label = t("uni_field_institution", lang)
        self.fields["course"].label = t("uni_field_course", lang)
        self.fields["faculty"].label = t("uni_field_faculty", lang)
        self.fields["level"].label = t("uni_field_level", lang)
        self.fields["year_started"].label = t("uni_field_year_started", lang)
        self.fields["expected_completion_year"].label = t("uni_field_expected_completion", lang)
        self.fields["year_completed"].label = t("uni_field_year_completed", lang)
        self.fields["status"].label = t("uni_field_status", lang)
        self.fields["notes"].label = t("uni_field_notes", lang)
        self.fields["level"].choices = [
            (code, t(f"uni_level_{code}", lang))
            for code, _ in UniversityStudentRecord.LEVEL_CHOICES
        ]
        self.fields["status"].choices = [
            (code, t(f"uni_status_{code}", lang))
            for code, _ in UniversityStudentRecord.STATUS_CHOICES
        ]

    def clean(self):
        cleaned = super().clean()
        lang = getattr(self, "_lang", "en")
        from .language_utils import get_translation as t

        status = cleaned.get("status")
        year_completed = cleaned.get("year_completed")
        if status == "completed" and not year_completed:
            raise ValidationError(t("uni_err_grad_year_required", lang))
        return cleaned

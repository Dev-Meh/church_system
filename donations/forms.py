from decimal import Decimal
from datetime import timedelta
from django import forms
from django.utils import timezone
from .models import (
    Donation,
    DonationCampaign,
    DonationNotice,
    CashBookEntry,
    GROUP_PAYMENT_CHOICES,
)
from members.models import ChurchUser
from members.language_utils import get_translation


def _form_t(key, language='en'):
    return get_translation(key, language or 'en')


def _payment_method_choices(language='en'):
    codes = ('cash', 'bank_transfer', 'mobile_money', 'check', 'online', 'card')
    lang = language or 'en'
    return [(code, _form_t(f'pmethod_{code}', lang)) for code in codes]


def _amount_input_attrs():
    return {
        'class': 'form-control sheet-amount-input',
        'step': '1',
        'min': '0',
        'inputmode': 'numeric',
        'pattern': '[0-9]*',
        'placeholder': '0',
    }


def _contribution_date_input_attrs(**extra):
    """Tarehe ya mchango — kuruhusu nyuma, si ya baadaye."""
    attrs = {
        'class': 'form-control',
        'type': 'date',
        'max': timezone.localdate().isoformat(),
    }
    attrs.update(extra)
    return attrs


def _validate_contribution_date(date_value, lang='en'):
    if date_value and date_value > timezone.localdate():
        raise forms.ValidationError(_form_t('contrib_err_future_date', lang))
    return date_value


def _is_whole_amount(value):
    if value in (None, ''):
        return True
    return Decimal(value) == Decimal(value).quantize(Decimal('1'))

class DonationForm(forms.ModelForm):
    class Meta:
        model = Donation
        fields = ['amount', 'payment_method', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter amount',
                'min': '1',
                'step': '1'
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
        self.fields['amount'].label = 'Donation Amount (TZS)'
        self.fields['payment_method'].label = 'Payment Method'
        self.fields['notes'].label = 'Notes (Optional)'
        self.fields['notes'].required = False

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and not _is_whole_amount(amount):
            raise forms.ValidationError('Weka kiasi bila desimali (mfano 1000).')
        return amount

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


class AccountantDonationEntryForm(forms.ModelForm):
    class Meta:
        model = Donation
        fields = [
            'donor',
            'donation_type',
            'category',
            'campaign',
            'amount',
            'payment_method',
            'contribution_date',
            'notes',
        ]
        widgets = {
            'donor': forms.Select(attrs={'class': 'form-select'}),
            'donation_type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'campaign': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'step': '1'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'contribution_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, allowed_donor_ids=None, language='en', **kwargs):
        lang = language or 'en'
        self._lang = lang
        super().__init__(*args, **kwargs)
        self.fields['donor'].required = False
        self.fields['donor'].label = _form_t('don_zaka_member_label', lang)
        self.fields['donor'].empty_label = _form_t('don_select_member', lang)
        self.fields['donation_type'].label = _form_t('don_col_type', lang)
        self.fields['donation_type'].choices = [
            ('tithe', _form_t('dtype_tithe', lang)),
            ('offering', _form_t('dtype_offering', lang)),
            ('special', _form_t('dtype_special', lang)),
            ('other', _form_t('dtype_other', lang)),
        ]
        self.fields['amount'].label = _form_t('donation_amount', lang)
        self.fields['payment_method'].label = _form_t('payment_method', lang)
        self.fields['payment_method'].choices = _payment_method_choices(lang)
        self.fields['contribution_date'].label = _form_t('don_col_date', lang)
        self.fields['contribution_date'].widget.attrs.update(_contribution_date_input_attrs())
        self.fields['campaign'].required = False
        self.fields['category'].required = False
        self.fields['notes'].required = False
        self.fields['notes'].label = _form_t('don_notes_optional', lang)
        self.fields['notes'].widget.attrs['placeholder'] = _form_t('don_notes_ph', lang)
        qs = ChurchUser.objects.filter(
            is_active=True,
            role__in=['member', 'pastor', 'elder', 'deacon', 'accountant', 'admin', 'secretary']
        ).order_by('first_name', 'last_name')
        if allowed_donor_ids is not None:
            qs = qs.filter(id__in=allowed_donor_ids)
        self.fields['donor'].queryset = qs

    def clean(self):
        cleaned_data = super().clean()
        donor = cleaned_data.get('donor')
        amount = cleaned_data.get('amount')
        donation_type = cleaned_data.get('donation_type') or 'other'
        lang = getattr(self, '_lang', 'en')
        if donation_type == 'tithe':
            if not donor:
                raise forms.ValidationError(_form_t('tithe_err_member', lang))
        else:
            cleaned_data['donor'] = None
        if amount is not None and not _is_whole_amount(amount):
            raise forms.ValidationError('Kiasi cha fedha kiwekwe bila desimali.')
        _validate_contribution_date(cleaned_data.get('contribution_date'), lang)
        return cleaned_data


class GroupMchangoEntryForm(forms.ModelForm):
    """Mchango wa idara — mhasibu huandika, mwanachama huona baadaye."""

    class Meta:
        model = Donation
        fields = [
            "donor",
            "amount",
            "payment_method",
            "tithe_gift_type",
            "contribution_date",
            "notes",
        ]
        widgets = {
            "donor": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(
                attrs={"class": "form-control", "min": "1", "step": "1"}
            ),
            "payment_method": forms.Select(attrs={"class": "form-select"}),
            "tithe_gift_type": forms.Select(attrs={"class": "form-select"}),
            "contribution_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def __init__(self, *args, allowed_donor_ids=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["donor"].label = "Jina la mwanachama"
        self.fields["donor"].required = True
        self.fields["amount"].label = "Kiasi cha mchango (TZS)"
        self.fields["payment_method"].label = "Aina ya fedha"
        self.fields["payment_method"].choices = GROUP_PAYMENT_CHOICES
        self.fields["tithe_gift_type"].label = "Mchango ni"
        self.fields["contribution_date"].label = "Tarehe ya mchango"
        self.fields["notes"].label = "Maelezo (hiari)"
        self.fields["notes"].required = False
        self.fields["notes"].widget.attrs["placeholder"] = "Mfano: mchango wa mwezi Mei"
        qs = ChurchUser.objects.filter(is_active=True).order_by(
            "first_name", "last_name"
        )
        if allowed_donor_ids is not None:
            qs = qs.filter(id__in=allowed_donor_ids)
        self.fields["donor"].queryset = qs

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("donor"):
            raise forms.ValidationError("Chagua mwanachama.")
        amount = cleaned_data.get("amount")
        if amount is not None and not _is_whole_amount(amount):
            raise forms.ValidationError("Kiasi kiwe namba kamili (mfano 5000).")
        return cleaned_data


class DonationNoticeForm(forms.ModelForm):
    class Meta:
        model = DonationNotice
        fields = ['title', 'message', 'target_member', 'start_date', 'end_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kichwa cha taarifa'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Andika taarifa ya mchango...'}),
            'target_member': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, language='en', **kwargs):
        super().__init__(*args, **kwargs)
        lang = language or 'en'
        self.fields['target_member'].required = False
        self.fields['target_member'].empty_label = _form_t('recipient_all', lang)
        self.fields['target_member'].queryset = ChurchUser.objects.filter(
            is_active=True
        ).order_by('first_name', 'last_name')
        self.fields['title'].label = _form_t('don_notice_title', lang)
        self.fields['message'].label = _form_t('don_notice_message', lang)
        self.fields['target_member'].label = _form_t('don_notice_recipient', lang)
        self.fields['start_date'].label = _form_t('don_notice_start', lang)
        self.fields['end_date'].label = _form_t('don_notice_end', lang)
        self.fields['title'].widget.attrs['placeholder'] = _form_t('don_notice_title_ph', lang)
        self.fields['message'].widget.attrs['placeholder'] = _form_t('don_notice_message_ph', lang)

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError("Tarehe ya mwisho lazima iwe baada ya au sawa na tarehe ya kuanza.")
        return cleaned_data


class AccountantSheetEntryForm(forms.Form):
    ZAKA_TYPE_CHOICES = [
        ('money', 'Fedha'),
        ('asset', 'Mali (mfano mbuzi)'),
    ]

    donor = forms.ModelChoiceField(
        queryset=ChurchUser.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Mwanachama',
        required=False,
    )
    construction_donor = forms.ModelChoiceField(
        queryset=ChurchUser.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Mwanachama wa Ujenzi (ahidi / malipo)',
        required=False
    )
    contribution_date = forms.DateField(
        widget=forms.DateInput(attrs=_contribution_date_input_attrs()),
        label='Tarehe',
        initial=timezone.localdate,
    )
    payment_method = forms.ChoiceField(
        choices=Donation.PAYMENT_METHOD_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select payment-method-select'}),
        label='Njia ya Malipo'
    )
    sadaka = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        max_digits=12,
        widget=forms.NumberInput(attrs=_amount_input_attrs())
    )
    zaka = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        max_digits=12,
        widget=forms.NumberInput(attrs=_amount_input_attrs())
    )
    zaka_type = forms.ChoiceField(
        choices=ZAKA_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='money',
        label='Aina ya Zaka'
    )
    aina_nyingine_ya_zaka = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mfano: Mbuzi 1, Mahindi gunia 2'}),
        label='Aina Nyingine ya Zaka'
    )
    malimbuko = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        max_digits=12,
        widget=forms.NumberInput(attrs=_amount_input_attrs())
    )
    shukrani = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        max_digits=12,
        widget=forms.NumberInput(attrs=_amount_input_attrs())
    )
    construction_pledge_amount = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        max_digits=12,
        widget=forms.NumberInput(attrs=_amount_input_attrs()),
        label='Ahadi Mpya ya Ujenzi'
    )
    construction_payment_amount = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        max_digits=12,
        widget=forms.NumberInput(attrs=_amount_input_attrs()),
        label='Malipo ya Deni la Ujenzi'
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Maelezo (hiari)'})
    )

    def __init__(self, *args, allowed_donor_ids=None, language='en', **kwargs):
        super().__init__(*args, **kwargs)
        lang = language or 'en'
        self._lang = lang
        member_qs = ChurchUser.objects.filter(
            is_active=True,
            role__in=['member', 'pastor', 'elder', 'deacon', 'accountant', 'admin', 'secretary']
        ).order_by('first_name', 'last_name')
        if allowed_donor_ids is not None:
            member_qs = member_qs.filter(id__in=allowed_donor_ids)
        select_member = _form_t('don_select_member', lang)
        self.fields['donor'].queryset = member_qs
        self.fields['construction_donor'].queryset = member_qs
        self.fields['donor'].empty_label = select_member
        self.fields['construction_donor'].empty_label = select_member
        self.fields['donor'].label = _form_t('don_zaka_member_label', lang)
        self.fields['donor'].required = False
        self.fields['donor'].widget.attrs['required'] = False
        self.fields['construction_donor'].label = _form_t('don_construction_member', lang)
        self.fields['contribution_date'].label = _form_t('don_col_date', lang)
        self.fields['contribution_date'].widget.attrs.update(_contribution_date_input_attrs())
        self.fields['payment_method'].label = _form_t('payment_method', lang)
        self.fields['payment_method'].choices = _payment_method_choices(lang)
        self.fields['payment_method'].widget.attrs['class'] = 'form-select payment-method-select'
        for field_name in (
            'sadaka', 'zaka', 'malimbuko', 'shukrani',
            'construction_pledge_amount', 'construction_payment_amount',
        ):
            self.fields[field_name].widget.attrs.update(_amount_input_attrs())
        self.fields['sadaka'].label = _form_t('don_col_offering', lang)
        self.fields['zaka'].label = _form_t('don_col_tithe', lang)
        self.fields['zaka_type'].label = _form_t('don_zaka_type', lang)
        self.fields['zaka_type'].choices = [
            ('money', _form_t('gift_money', lang)),
            ('asset', _form_t('gift_asset', lang)),
        ]
        self.fields['aina_nyingine_ya_zaka'].label = _form_t('don_other_gift_type', lang)
        self.fields['malimbuko'].label = _form_t('don_col_special_offering', lang)
        self.fields['shukrani'].label = _form_t('don_col_thanksgiving', lang)
        self.fields['construction_pledge_amount'].label = _form_t('don_new_pledge', lang)
        self.fields['construction_payment_amount'].label = _form_t('don_col_debt_payment', lang)
        self.fields['notes'].label = _form_t('don_notes_optional', lang)
        self.fields['notes'].widget.attrs['placeholder'] = _form_t('don_notes_ph', lang)

    def clean(self):
        cleaned_data = super().clean()
        zaka_type = cleaned_data.get('zaka_type') or 'money'
        zaka_amount = cleaned_data.get('zaka') or 0
        aina_nyingine_ya_zaka = (cleaned_data.get('aina_nyingine_ya_zaka') or '').strip()
        donor = cleaned_data.get('donor')
        construction_donor = cleaned_data.get('construction_donor')
        construction_pledge_amount = cleaned_data.get('construction_pledge_amount') or 0
        construction_payment_amount = cleaned_data.get('construction_payment_amount') or 0

        personal_amounts = [
            cleaned_data.get('sadaka') or 0,
            cleaned_data.get('malimbuko') or 0,
            cleaned_data.get('shukrani') or 0,
        ]
        zaka_money = zaka_amount if zaka_type == 'money' else 0
        submitting_asset_zaka = zaka_type == 'asset' and bool(aina_nyingine_ya_zaka)
        lang = getattr(self, '_lang', 'en')

        if zaka_money > 0 and not donor:
            raise forms.ValidationError(_form_t('tithe_err_member', lang))
        if submitting_asset_zaka and not donor:
            raise forms.ValidationError(_form_t('tithe_err_member', lang))

        has_named_zaka = zaka_money > 0 or submitting_asset_zaka
        if not has_named_zaka:
            cleaned_data['donor'] = None

        if (construction_pledge_amount > 0 or construction_payment_amount > 0) and not construction_donor:
            raise forms.ValidationError('Chagua mwanachama wa ahidi au malipo ya ujenzi.')

        amount_fields = (
            'sadaka',
            'zaka',
            'malimbuko',
            'shukrani',
            'construction_pledge_amount',
            'construction_payment_amount',
        )
        for field_name in amount_fields:
            value = cleaned_data.get(field_name)
            if value is not None and value != '' and not _is_whole_amount(value):
                raise forms.ValidationError(f'Kiasi cha "{self.fields[field_name].label or field_name}" kiwe bila desimali.')

        total = sum([
            cleaned_data.get('sadaka') or 0,
            zaka_amount if zaka_type == 'money' else 0,
            cleaned_data.get('malimbuko') or 0,
            cleaned_data.get('shukrani') or 0,
            construction_payment_amount,
        ])
        if total <= 0 and not submitting_asset_zaka and construction_pledge_amount <= 0:
            raise forms.ValidationError('Weka angalau kiasi kimoja: Sadaka, Zaka, Malimbuko, Shukrani, Malipo ya Ujenzi au Ahadi ya Ujenzi.')
        _validate_contribution_date(cleaned_data.get('contribution_date'), lang)
        cleaned_data['jumla'] = total
        return cleaned_data


class ConstructionHomeEntryForm(forms.Form):
    """Ahadi na malipo ya ujenzi tu — ukurasa wa michango (home)."""

    construction_donor = forms.ModelChoiceField(
        queryset=ChurchUser.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
    )
    contribution_date = forms.DateField(
        widget=forms.DateInput(attrs=_contribution_date_input_attrs()),
        initial=timezone.localdate,
    )
    payment_method = forms.ChoiceField(
        choices=Donation.PAYMENT_METHOD_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select payment-method-select'}),
    )
    construction_pledge_amount = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        max_digits=12,
        widget=forms.NumberInput(attrs=_amount_input_attrs()),
    )
    construction_payment_amount = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        max_digits=12,
        widget=forms.NumberInput(attrs=_amount_input_attrs()),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': ''}),
    )

    def __init__(self, *args, allowed_donor_ids=None, language='en', **kwargs):
        super().__init__(*args, **kwargs)
        lang = language or 'en'
        self._lang = lang
        member_qs = ChurchUser.objects.filter(
            is_active=True,
            role__in=['member', 'pastor', 'elder', 'deacon', 'accountant', 'admin', 'secretary'],
        ).order_by('first_name', 'last_name')
        if allowed_donor_ids is not None:
            member_qs = member_qs.filter(id__in=allowed_donor_ids)
        select_member = _form_t('don_select_member', lang)
        self.fields['construction_donor'].queryset = member_qs
        self.fields['construction_donor'].empty_label = select_member
        self.fields['construction_donor'].label = _form_t('don_construction_member', lang)
        self.fields['contribution_date'].label = _form_t('don_col_date', lang)
        self.fields['contribution_date'].widget.attrs.update(_contribution_date_input_attrs())
        self.fields['payment_method'].label = _form_t('payment_method', lang)
        self.fields['payment_method'].choices = _payment_method_choices(lang)
        self.fields['payment_method'].widget.attrs['class'] = 'form-select payment-method-select'
        for field_name in ('construction_pledge_amount', 'construction_payment_amount'):
            self.fields[field_name].widget.attrs.update(_amount_input_attrs())
        self.fields['construction_pledge_amount'].label = _form_t('don_new_pledge', lang)
        self.fields['construction_payment_amount'].label = _form_t('don_col_debt_payment', lang)
        self.fields['notes'].label = _form_t('don_notes_optional', lang)
        self.fields['notes'].widget.attrs['placeholder'] = _form_t('don_notes_ph', lang)

    def clean(self):
        cleaned_data = super().clean()
        lang = getattr(self, '_lang', 'en')
        construction_donor = cleaned_data.get('construction_donor')
        construction_pledge_amount = cleaned_data.get('construction_pledge_amount') or 0
        construction_payment_amount = cleaned_data.get('construction_payment_amount') or 0

        if not construction_donor:
            raise forms.ValidationError(_form_t('pledge_err_member', lang))

        for field_name in ('construction_pledge_amount', 'construction_payment_amount'):
            value = cleaned_data.get(field_name)
            if value is not None and value != '' and not _is_whole_amount(value):
                label = self.fields[field_name].label or field_name
                raise forms.ValidationError(
                    f'Kiasi cha "{label}" kiwe bila desimali.'
                )

        if construction_pledge_amount <= 0 and construction_payment_amount <= 0:
            raise forms.ValidationError(
                'Weka ahadi mpya ya ujenzi au malipo ya deni (au vyote).'
            )

        _validate_contribution_date(cleaned_data.get('contribution_date'), lang)
        return cleaned_data


class TitheEntryForm(forms.Form):
    donor = forms.ModelChoiceField(
        queryset=ChurchUser.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
    )
    contribution_date = forms.DateField(
        widget=forms.DateInput(attrs=_contribution_date_input_attrs()),
        initial=timezone.localdate,
    )
    payment_method = forms.ChoiceField(
        choices=Donation.PAYMENT_METHOD_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select payment-method-select'}),
    )
    zaka_type = forms.ChoiceField(
        choices=AccountantSheetEntryForm.ZAKA_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='money',
    )
    amount = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        max_digits=12,
        widget=forms.NumberInput(attrs=_amount_input_attrs()),
    )
    asset_description = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': ''}),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': ''}),
    )

    def __init__(self, *args, allowed_donor_ids=None, language='en', **kwargs):
        super().__init__(*args, **kwargs)
        self._lang = language or 'en'
        lang = self._lang
        member_qs = ChurchUser.objects.filter(
            is_active=True,
            role__in=['member', 'pastor', 'elder', 'deacon', 'accountant', 'admin', 'secretary'],
        ).order_by('first_name', 'last_name')
        if allowed_donor_ids is not None:
            member_qs = member_qs.filter(id__in=allowed_donor_ids)
        self.fields['donor'].queryset = member_qs
        self.fields['donor'].empty_label = _form_t('don_select_member', lang)
        self.fields['donor'].label = _form_t('don_member_label', lang)
        self.fields['contribution_date'].label = _form_t('don_col_date', lang)
        self.fields['contribution_date'].widget.attrs.update(_contribution_date_input_attrs())
        self.fields['payment_method'].label = _form_t('payment_method', lang)
        self.fields['payment_method'].choices = _payment_method_choices(lang)
        self.fields['zaka_type'].label = _form_t('don_zaka_type', lang)
        self.fields['zaka_type'].choices = [
            ('money', _form_t('gift_money', lang)),
            ('asset', _form_t('gift_asset', lang)),
        ]
        self.fields['amount'].label = _form_t('tithe_col_zaka', lang)
        self.fields['asset_description'].label = _form_t('don_other_gift_type', lang)
        self.fields['asset_description'].widget.attrs['placeholder'] = _form_t('don_notes_ph', lang)
        self.fields['notes'].label = _form_t('don_notes_optional', lang)
        self.fields['notes'].widget.attrs['placeholder'] = _form_t('don_notes_ph', lang)

    def clean(self):
        cleaned_data = super().clean()
        zaka_type = cleaned_data.get('zaka_type') or 'money'
        amount = cleaned_data.get('amount') or 0
        asset_description = (cleaned_data.get('asset_description') or '').strip()
        lang = getattr(self, '_lang', 'en')
        if not cleaned_data.get('donor'):
            raise forms.ValidationError(_form_t('tithe_err_member', lang))
        if zaka_type == 'money':
            if amount <= 0:
                raise forms.ValidationError(_form_t('tithe_err_amount', lang))
            if not _is_whole_amount(amount):
                raise forms.ValidationError(_form_t('tithe_err_whole', lang))
        else:
            if not asset_description:
                raise forms.ValidationError(_form_t('tithe_err_asset', lang))
        _validate_contribution_date(cleaned_data.get('contribution_date'), lang)
        return cleaned_data


class MalimbukoEntryForm(forms.Form):
    """Malimbuko — michango kutoka mavuno/miladi ya kanisa (bila jina la mtoaji)."""

    contribution_date = forms.DateField(
        widget=forms.DateInput(attrs=_contribution_date_input_attrs()),
        initial=timezone.localdate,
    )
    payment_method = forms.ChoiceField(
        choices=Donation.PAYMENT_METHOD_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select payment-method-select'}),
    )
    gift_type = forms.ChoiceField(
        choices=AccountantSheetEntryForm.ZAKA_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='money',
    )
    amount = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        max_digits=12,
        widget=forms.NumberInput(attrs=_amount_input_attrs()),
    )
    asset_description = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': ''}),
    )
    miladi_source = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': ''}),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': ''}),
    )

    def __init__(self, *args, allowed_donor_ids=None, language='en', **kwargs):
        super().__init__(*args, **kwargs)
        self._lang = language or 'en'
        lang = self._lang
        self.fields['contribution_date'].label = _form_t('don_col_date', lang)
        self.fields['contribution_date'].widget.attrs.update(_contribution_date_input_attrs())
        self.fields['payment_method'].label = _form_t('payment_method', lang)
        self.fields['payment_method'].choices = _payment_method_choices(lang)
        self.fields['gift_type'].label = _form_t('malimbuko_gift_type', lang)
        self.fields['gift_type'].choices = [
            ('money', _form_t('malimbuko_gift_money', lang)),
            ('asset', _form_t('malimbuko_gift_asset', lang)),
        ]
        self.fields['amount'].label = _form_t('malimbuko_col_amount', lang)
        self.fields['asset_description'].label = _form_t('malimbuko_col_harvest', lang)
        self.fields['asset_description'].widget.attrs['placeholder'] = _form_t(
            'malimbuko_harvest_ph', lang
        )
        self.fields['miladi_source'].label = _form_t('malimbuko_col_miladi', lang)
        self.fields['miladi_source'].widget.attrs['placeholder'] = _form_t(
            'malimbuko_miladi_ph', lang
        )
        self.fields['notes'].label = _form_t('don_notes_optional', lang)
        self.fields['notes'].widget.attrs['placeholder'] = _form_t('don_notes_ph', lang)

    def clean(self):
        cleaned_data = super().clean()
        gift_type = cleaned_data.get('gift_type') or 'money'
        amount = cleaned_data.get('amount') or 0
        asset_description = (cleaned_data.get('asset_description') or '').strip()
        lang = getattr(self, '_lang', 'en')
        if gift_type == 'money':
            if amount <= 0:
                raise forms.ValidationError(_form_t('malimbuko_err_amount', lang))
            if not _is_whole_amount(amount):
                raise forms.ValidationError(_form_t('tithe_err_whole', lang))
        elif not asset_description:
            raise forms.ValidationError(_form_t('malimbuko_err_harvest', lang))
        _validate_contribution_date(cleaned_data.get('contribution_date'), lang)
        return cleaned_data


SUNDAY_OFFERING_NOTE_PREFIX = 'Sadaka ya Jumapili'


class SundayOfferingEntryForm(forms.Form):
    """Sadaka ya Jumapili — ibada ya kanisa, bila jina la mtoaji."""

    SERVICE_SESSION_CHOICES = [
        ('', '—'),
        ('morning', 'morning'),
        ('afternoon', 'afternoon'),
        ('evening', 'evening'),
    ]

    contribution_date = forms.DateField(
        widget=forms.DateInput(attrs=_contribution_date_input_attrs(
            **{'class': 'form-control worship-date-input'},
        )),
    )
    service_session = forms.ChoiceField(
        choices=SERVICE_SESSION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    payment_method = forms.ChoiceField(
        choices=Donation.PAYMENT_METHOD_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select payment-method-select'}),
    )
    amount = forms.DecimalField(
        required=True,
        min_value=1,
        decimal_places=2,
        max_digits=12,
        widget=forms.NumberInput(attrs={
            **_amount_input_attrs(),
            'class': 'form-control sheet-amount-input sunday-amount-input',
            'autocomplete': 'off',
        }),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': ''}),
    )

    def __init__(self, *args, language='en', **kwargs):
        super().__init__(*args, **kwargs)
        self._lang = language or 'en'
        lang = self._lang
        if not self.initial.get('contribution_date') and not self.data:
            self.initial['contribution_date'] = _default_worship_date()
        self.fields['contribution_date'].label = _form_t('sunday_worship_date', lang)
        self.fields['contribution_date'].help_text = _form_t('contrib_date_past_ok', lang)
        self.fields['service_session'].label = _form_t('sunday_service_session', lang)
        self.fields['service_session'].choices = [
            ('', _form_t('sunday_session_any', lang)),
            ('morning', _form_t('sunday_session_morning', lang)),
            ('afternoon', _form_t('sunday_session_afternoon', lang)),
            ('evening', _form_t('sunday_session_evening', lang)),
        ]
        self.fields['payment_method'].label = _form_t('payment_method', lang)
        self.fields['payment_method'].choices = _payment_method_choices(lang)
        self.fields['amount'].label = _form_t('sunday_amount_label', lang)
        self.fields['notes'].label = _form_t('don_notes_optional', lang)
        self.fields['notes'].widget.attrs['placeholder'] = _form_t('sunday_notes_ph', lang)

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('amount') or 0
        lang = getattr(self, '_lang', 'en')
        if amount <= 0:
            raise forms.ValidationError(_form_t('offering_err_amount', lang))
        if not _is_whole_amount(amount):
            raise forms.ValidationError(_form_t('tithe_err_whole', lang))
        _validate_contribution_date(cleaned_data.get('contribution_date'), lang)
        return cleaned_data


def _default_worship_date():
    """Tarehe ya Jumapili iliyopita au leo ikiwa ni Jumapili."""
    today = timezone.localdate()
    days_since_sunday = (today.weekday() + 1) % 7
    return today - timedelta(days=days_since_sunday)


class AnonymousContributionEntryForm(forms.Form):
    """Sadaka, Shukrani — bila jina la mtoaji."""

    contribution_date = forms.DateField(
        widget=forms.DateInput(attrs=_contribution_date_input_attrs()),
        initial=timezone.localdate,
    )
    payment_method = forms.ChoiceField(
        choices=Donation.PAYMENT_METHOD_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select payment-method-select'}),
    )
    amount = forms.DecimalField(
        required=True,
        min_value=1,
        decimal_places=2,
        max_digits=12,
        widget=forms.NumberInput(attrs=_amount_input_attrs()),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': ''}),
    )

    def __init__(self, *args, language='en', err_amount_key='contrib_err_amount', **kwargs):
        super().__init__(*args, **kwargs)
        self._lang = language or 'en'
        self._err_amount_key = err_amount_key
        lang = self._lang
        self.fields['contribution_date'].label = _form_t('don_col_date', lang)
        self.fields['contribution_date'].help_text = _form_t('contrib_date_past_ok', lang)
        self.fields['contribution_date'].widget.attrs.update(_contribution_date_input_attrs())
        self.fields['payment_method'].label = _form_t('payment_method', lang)
        self.fields['payment_method'].choices = _payment_method_choices(lang)
        self.fields['amount'].label = _form_t('don_col_amount', lang)
        self.fields['notes'].label = _form_t('don_notes_optional', lang)
        self.fields['notes'].widget.attrs['placeholder'] = _form_t('don_notes_ph', lang)

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('amount') or 0
        lang = getattr(self, '_lang', 'en')
        if amount <= 0:
            raise forms.ValidationError(_form_t(self._err_amount_key, lang))
        if not _is_whole_amount(amount):
            raise forms.ValidationError(_form_t('tithe_err_whole', lang))
        _validate_contribution_date(cleaned_data.get('contribution_date'), lang)
        return cleaned_data


class PledgeEntryForm(forms.Form):
    """Ahadi mpya ya ujenzi — na jina la mwanachama."""

    donor = forms.ModelChoiceField(
        queryset=ChurchUser.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
    )
    total_amount = forms.DecimalField(
        required=True,
        min_value=1,
        decimal_places=2,
        max_digits=12,
        widget=forms.NumberInput(attrs=_amount_input_attrs()),
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs=_contribution_date_input_attrs()),
        initial=timezone.localdate,
    )
    notes = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': ''}),
    )

    def __init__(self, *args, allowed_donor_ids=None, language='en', **kwargs):
        super().__init__(*args, **kwargs)
        self._lang = language or 'en'
        lang = self._lang
        member_qs = ChurchUser.objects.filter(
            is_active=True,
            role__in=['member', 'pastor', 'elder', 'deacon', 'accountant', 'admin', 'secretary'],
        ).order_by('first_name', 'last_name')
        if allowed_donor_ids is not None:
            member_qs = member_qs.filter(id__in=allowed_donor_ids)
        self.fields['donor'].queryset = member_qs
        self.fields['donor'].empty_label = _form_t('don_select_member', lang)
        self.fields['donor'].label = _form_t('don_member_label', lang)
        self.fields['total_amount'].label = _form_t('don_new_pledge', lang)
        self.fields['start_date'].label = _form_t('don_col_date', lang)
        self.fields['start_date'].help_text = _form_t('contrib_date_past_ok', lang)
        self.fields['notes'].label = _form_t('don_notes_optional', lang)
        self.fields['notes'].widget.attrs['placeholder'] = _form_t('don_notes_ph', lang)

    def clean(self):
        cleaned_data = super().clean()
        lang = getattr(self, '_lang', 'en')
        if not cleaned_data.get('donor'):
            raise forms.ValidationError(_form_t('pledge_err_member', lang))
        amount = cleaned_data.get('total_amount') or 0
        if amount <= 0:
            raise forms.ValidationError(_form_t('pledge_err_amount', lang))
        if not _is_whole_amount(amount):
            raise forms.ValidationError(_form_t('tithe_err_whole', lang))
        _validate_contribution_date(cleaned_data.get('start_date'), lang)
        return cleaned_data


class PledgePaymentForm(forms.Form):
    amount = forms.DecimalField(
        required=True,
        min_value=1,
        decimal_places=2,
        max_digits=12,
        widget=forms.NumberInput(attrs={
            **{k: v for k, v in _amount_input_attrs().items() if k != 'min'},
            'class': 'form-control sheet-amount-input pledge-input',
            'min': '1',
        }),
    )
    payment_method = forms.ChoiceField(
        choices=Donation.PAYMENT_METHOD_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select payment-method-select pledge-input'}),
    )
    contribution_date = forms.DateField(
        widget=forms.DateInput(attrs=_contribution_date_input_attrs(
            **{'class': 'form-control pledge-input'},
        )),
        initial=timezone.localdate,
    )
    notes = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control pledge-input', 'placeholder': ''}),
    )

    def __init__(self, *args, pledge=None, language='en', **kwargs):
        super().__init__(*args, **kwargs)
        lang = language or 'en'
        self.pledge = pledge
        self.fields['amount'].label = _form_t('don_col_amount', lang)
        self.fields['payment_method'].label = _form_t('payment_method', lang)
        self.fields['payment_method'].choices = _payment_method_choices(lang)
        self.fields['contribution_date'].label = _form_t('don_col_date', lang)
        self.fields['notes'].label = _form_t('don_notes_optional', lang)
        self.fields['notes'].widget.attrs['placeholder'] = _form_t('don_notes_ph', lang)
        if pledge and pledge.debt_balance_display > 0:
            self.fields['amount'].widget.attrs['max'] = str(pledge.debt_balance_display)

    def clean(self):
        cleaned_data = super().clean()
        lang = getattr(self, '_lang', 'en')
        _validate_contribution_date(cleaned_data.get('contribution_date'), lang)
        return cleaned_data

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and not _is_whole_amount(amount):
            raise forms.ValidationError('Weka kiasi bila desimali.')
        if self.pledge and amount and amount > self.pledge.debt_balance_display:
            raise forms.ValidationError(
                f'Kiasi hakiwezi kuzidi deni lililobaki (TZS {self.pledge.debt_balance_display:,}).'
            )
        return amount


class PledgeReduceForm(forms.Form):
    reduce_amount = forms.DecimalField(
        required=True,
        min_value=1,
        decimal_places=2,
        max_digits=12,
        widget=forms.NumberInput(attrs={
            **{k: v for k, v in _amount_input_attrs().items() if k != 'min'},
            'class': 'form-control sheet-amount-input pledge-input',
            'min': '1',
        }),
    )
    reason = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control pledge-input', 'placeholder': ''}),
    )

    def __init__(self, *args, pledge=None, language='en', **kwargs):
        super().__init__(*args, **kwargs)
        lang = language or 'en'
        self.pledge = pledge
        self.fields['reduce_amount'].label = _form_t('don_pledge_reduce_amount', lang)
        self.fields['reason'].label = _form_t('don_pledge_reduce_reason', lang)
        self.fields['reason'].widget.attrs['placeholder'] = _form_t('don_pledge_reduce_reason_ph', lang)
        if pledge and pledge.debt_balance_display > 0:
            self.fields['reduce_amount'].widget.attrs['max'] = str(pledge.debt_balance_display)

    def clean_reduce_amount(self):
        amount = self.cleaned_data.get('reduce_amount')
        if amount is not None and not _is_whole_amount(amount):
            raise forms.ValidationError('Weka kiasi bila desimali.')
        if self.pledge and amount and amount > self.pledge.debt_balance_display:
            raise forms.ValidationError(
                f'Huwezi kupunguza zaidi ya deni lililobaki (TZS {self.pledge.debt_balance_display:,}).'
            )
        return amount


class CashBookEntryForm(forms.ModelForm):
    class Meta:
        model = CashBookEntry
        fields = ['entry_date', 'entry_type', 'description', 'cash_amount', 'bank_amount']
        widgets = {
            'entry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'entry_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Maelezo ya muamala'}),
            'cash_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'min': '0'}),
            'bank_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'min': '0'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        cash_amount = cleaned_data.get('cash_amount') or 0
        bank_amount = cleaned_data.get('bank_amount') or 0
        if cash_amount <= 0 and bank_amount <= 0:
            raise forms.ValidationError('Weka kiasi kwenye Cash au Bank (au vyote viwili).')
        if not _is_whole_amount(cash_amount) or not _is_whole_amount(bank_amount):
            raise forms.ValidationError('Cash na Bank amount ziwekwe bila desimali.')
        return cleaned_data


class IncomeAllocationReportForm(forms.Form):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Tarehe ya Kuanza'
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Tarehe ya Mwisho'
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError('Tarehe ya mwisho lazima iwe sawa au baada ya tarehe ya kuanza.')
        return cleaned_data

from decimal import Decimal
from django import forms
from .models import Donation, DonationCampaign, DonationNotice, CashBookEntry
from members.models import ChurchUser


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['donor'].required = False
        self.fields['campaign'].required = False
        self.fields['category'].required = False
        self.fields['notes'].required = False
        self.fields['notes'].widget.attrs['placeholder'] = 'Maelezo mafupi (hiari): mfano zaka ya mwezi huu'
        self.fields['donor'].queryset = ChurchUser.objects.filter(
            is_active=True,
            role__in=['member', 'pastor', 'elder', 'deacon', 'accountant', 'admin']
        ).order_by('first_name', 'last_name')

    def clean(self):
        cleaned_data = super().clean()
        donation_type = cleaned_data.get('donation_type')
        donor = cleaned_data.get('donor')
        amount = cleaned_data.get('amount')
        if donation_type == 'tithe' and not donor:
            raise forms.ValidationError('Kwa zaka, lazima uchague mwanachama.')
        if amount is not None and not _is_whole_amount(amount):
            raise forms.ValidationError('Kiasi cha fedha kiwekwe bila desimali.')
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['target_member'].required = False
        self.fields['target_member'].empty_label = "Wote"
        self.fields['target_member'].queryset = ChurchUser.objects.filter(
            is_active=True
        ).order_by('first_name', 'last_name')

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
        label='Mwanachama wa Zaka',
        required=False
    )
    construction_donor = forms.ModelChoiceField(
        queryset=ChurchUser.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Mwanachama wa Ujenzi (ahidi / malipo)',
        required=False
    )
    contribution_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Tarehe'
    )
    payment_method = forms.ChoiceField(
        choices=Donation.PAYMENT_METHOD_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Njia ya Malipo'
    )
    sadaka = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        max_digits=12,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'min': '0'})
    )
    zaka = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        max_digits=12,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'min': '0'})
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
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'min': '0'})
    )
    shukrani = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        max_digits=12,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'min': '0'})
    )
    construction_pledge_amount = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        max_digits=12,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'min': '0'}),
        label='Ahadi Mpya ya Ujenzi'
    )
    construction_payment_amount = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        max_digits=12,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'min': '0'}),
        label='Malipo ya Deni la Ujenzi'
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Maelezo (hiari)'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        member_qs = ChurchUser.objects.filter(
            is_active=True,
            role__in=['member', 'pastor', 'elder', 'deacon', 'accountant', 'admin']
        ).order_by('first_name', 'last_name')
        self.fields['donor'].queryset = member_qs
        self.fields['construction_donor'].queryset = member_qs

    def clean(self):
        cleaned_data = super().clean()
        zaka_type = cleaned_data.get('zaka_type') or 'money'
        zaka_amount = cleaned_data.get('zaka') or 0
        aina_nyingine_ya_zaka = (cleaned_data.get('aina_nyingine_ya_zaka') or '').strip()
        donor = cleaned_data.get('donor')
        construction_donor = cleaned_data.get('construction_donor')
        construction_pledge_amount = cleaned_data.get('construction_pledge_amount') or 0
        construction_payment_amount = cleaned_data.get('construction_payment_amount') or 0

        if zaka_amount > 0 and zaka_type == 'money' and not donor:
            raise forms.ValidationError('Chagua mwanachama aliyechanga zaka ya fedha.')
        if zaka_type == 'asset':
            if not aina_nyingine_ya_zaka:
                raise forms.ValidationError('Ukichagua zaka ya mali, andika aina ya mali (mfano mbuzi).')
            if not donor:
                raise forms.ValidationError('Chagua mwanachama wa zaka ya mali.')

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
        if total <= 0 and zaka_type != 'asset' and construction_pledge_amount <= 0:
            raise forms.ValidationError('Weka angalau kiasi kimoja: Sadaka, Zaka, Malimbuko, Shukrani, Malipo ya Ujenzi au Ahadi ya Ujenzi.')
        cleaned_data['jumla'] = total
        return cleaned_data


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

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.db.models.functions import TruncMonth
from datetime import timedelta
import csv
import json
from members.models import ChurchUser
from members.language_utils import LanguageManager
from .models import (
    Donation,
    DonationCampaign,
    DonationCategory,
    DonationNotice,
    CashBookEntry,
    Pledge,
    _as_whole_amount,
)
from .print_branding import church_print_context
from .forms import (
    DonationForm,
    DonationNoticeForm,
    ConstructionHomeEntryForm,
    PledgePaymentForm,
    PledgeReduceForm,
    TitheEntryForm,
    MalimbukoEntryForm,
    SundayOfferingEntryForm,
    AnonymousContributionEntryForm,
    PledgeEntryForm,
    CashBookEntryForm,
    IncomeAllocationReportForm,
)


def _is_church_wide_accountant(user):
    from members.group_permissions import is_church_wide_accountant
    return is_church_wide_accountant(user)


def _is_accountant(user):
    from members.group_permissions import (
        groups_accounted_by,
        is_church_wide_accountant,
    )
    if is_church_wide_accountant(user):
        return True
    return groups_accounted_by(user).exists()


def _is_group_only_accountant(user):
    from members.group_permissions import is_group_only_accountant
    return is_group_only_accountant(user)


def _allowed_donor_ids(user):
    from members.group_permissions import get_scoped_donor_ids_for_user
    return get_scoped_donor_ids_for_user(user)


def _can_view_all_donations(user):
    from members.permissions import has_church_leadership
    if _is_group_only_accountant(user):
        return True
    return _is_church_wide_accountant(user) or has_church_leadership(user)


def _can_publish_donation_notice(user):
    from members.permissions import can_publish_donation_notice
    return can_publish_donation_notice(user)


def _can_view_tithe_list(user):
    from members.permissions import has_church_leadership
    if _is_group_only_accountant(user):
        return False
    return has_church_leadership(user) or _is_church_wide_accountant(user)


def _can_manage_cash_book(user):
    return _is_church_wide_accountant(user)


def _can_view_cash_book(user):
    from members.permissions import has_church_leadership
    return has_church_leadership(user) or _is_accountant(user)


def _can_view_income_allocation(user):
    from members.permissions import has_church_leadership
    return has_church_leadership(user) or _is_accountant(user)


def _can_view_sadaka(user):
    from members.permissions import can_view_church_sadaka
    return can_view_church_sadaka(user)


def _can_manage_construction_pledges(user):
    from members.permissions import has_church_leadership
    if has_church_leadership(user):
        return True
    return _is_church_wide_accountant(user) and bool(
        getattr(user, 'can_post_member_donations', False)
    )


def _can_enter_tithe(user):
    return _can_manage_construction_pledges(user)


def _can_view_malimbuko_list(user):
    return _can_view_tithe_list(user)


def _can_enter_malimbuko(user):
    return _can_enter_tithe(user)


def _named_donation_fields(donor):
    """Michango yenye jina la mtoaji (zaka, ahadi)."""
    if not donor:
        return {'donor': None, 'donor_name': '', 'is_anonymous': True}
    return {
        'donor': donor,
        'donor_name': donor.full_name,
        'is_anonymous': False,
    }


def _anonymous_donation_fields():
    """Michango isiyo na jina (sadaka, malimbuko, shukrani, n.k.)."""
    return {'donor': None, 'donor_name': '', 'is_anonymous': True}


def _save_tithe_entry(cleaned_data, processed_by):
    """Rekodi zaka kutoka fomu ya list au sheet."""
    donor = cleaned_data['donor']
    contribution_date = cleaned_data['contribution_date']
    payment_method = cleaned_data['payment_method']
    zaka_type = cleaned_data.get('zaka_type') or 'money'
    notes = (cleaned_data.get('notes') or '').strip()

    if zaka_type == 'asset':
        asset_desc = (cleaned_data.get('asset_description') or '').strip()
        asset_note = f"Zaka ya mali: {asset_desc}"
        combined_notes = f"{asset_note}. {notes}".strip() if notes else asset_note
        return Donation.objects.create(
            donor=donor,
            donation_type='tithe',
            amount=0,
            payment_method=payment_method,
            notes=combined_notes,
            donor_name=donor.full_name,
            contribution_date=contribution_date,
            status='completed',
            processed_by=processed_by,
            processed_date=timezone.now(),
            tithe_gift_type='asset',
            tithe_asset_description=asset_desc,
        )

    return Donation.objects.create(
        donor=donor,
        donation_type='tithe',
        amount=cleaned_data['amount'],
        payment_method=payment_method,
        notes=notes,
        donor_name=donor.full_name,
        contribution_date=contribution_date,
        status='completed',
        processed_by=processed_by,
        processed_date=timezone.now(),
        tithe_gift_type='money',
    )


def _malimbuko_donations_queryset():
    """Malimbuko — special contributions, si malipo ya ujenzi."""
    construction_ids = list(
        DonationCategory.objects.filter(name__iexact='Ujenzi').values_list('id', flat=True)
    )
    return (
        Donation.objects.filter(donation_type='special')
        .exclude(category_id__in=construction_ids)
        .exclude(notes__icontains='Malipo ya deni la ujenzi')
        .select_related('donor')
        .order_by('-contribution_date', '-donation_date')
    )


def _save_malimbuko_entry(cleaned_data, processed_by):
    contribution_date = cleaned_data['contribution_date']
    payment_method = cleaned_data['payment_method']
    gift_type = cleaned_data.get('gift_type') or 'money'
    miladi = (cleaned_data.get('miladi_source') or '').strip()
    notes = (cleaned_data.get('notes') or '').strip()
    identity = _anonymous_donation_fields()

    if gift_type == 'asset':
        asset_desc = (cleaned_data.get('asset_description') or '').strip()
        parts = ['Malimbuko (miladi ya kanisa)']
        if miladi:
            parts.append(f'Miladi: {miladi}')
        parts.append(f'Mavuno: {asset_desc}')
        if notes:
            parts.append(notes)
        combined_notes = '. '.join(parts)
        return Donation.objects.create(
            donation_type='special',
            amount=0,
            payment_method=payment_method,
            notes=combined_notes,
            contribution_date=contribution_date,
            status='completed',
            processed_by=processed_by,
            processed_date=timezone.now(),
            tithe_gift_type='asset',
            tithe_asset_description=asset_desc,
            **identity,
        )

    parts = ['Malimbuko (miladi ya kanisa)']
    if miladi:
        parts.append(f'Miladi: {miladi}')
    if notes:
        parts.append(notes)
    combined_notes = '. '.join(parts)
    return Donation.objects.create(
        donation_type='special',
        amount=cleaned_data['amount'],
        payment_method=payment_method,
        notes=combined_notes,
        contribution_date=contribution_date,
        status='completed',
        processed_by=processed_by,
        processed_date=timezone.now(),
        tithe_gift_type='money',
        **identity,
    )


def _donations_by_type_queryset(donation_type):
    return (
        Donation.objects.filter(donation_type=donation_type)
        .select_related('donor')
        .order_by('-contribution_date', '-donation_date')
    )


def _save_anonymous_contribution(cleaned_data, processed_by, donation_type, notes_override=None):
    notes = notes_override if notes_override is not None else (cleaned_data.get('notes') or '').strip()
    return Donation.objects.create(
        donation_type=donation_type,
        amount=cleaned_data['amount'],
        payment_method=cleaned_data['payment_method'],
        notes=notes,
        contribution_date=cleaned_data['contribution_date'],
        status='completed',
        processed_by=processed_by,
        processed_date=timezone.now(),
        tithe_gift_type='money',
        **_anonymous_donation_fields(),
    )


SUNDAY_OFFERING_NOTE_PREFIX = 'Sadaka ya Jumapili'


def _sunday_offering_queryset():
    return _donations_by_type_queryset('offering')


def _build_sunday_offering_notes(cleaned_data, language='en'):
    from members.language_utils import get_translation

    session = cleaned_data.get('service_session') or ''
    user_notes = (cleaned_data.get('notes') or '').strip()
    parts = [SUNDAY_OFFERING_NOTE_PREFIX]
    if session:
        session_labels = {
            'morning': get_translation('sunday_session_morning', language),
            'afternoon': get_translation('sunday_session_afternoon', language),
            'evening': get_translation('sunday_session_evening', language),
        }
        label = session_labels.get(session, session)
        parts.append(f'{get_translation("sunday_service_label", language)}: {label}')
    if user_notes:
        parts.append(user_notes)
    return '. '.join(parts)


def _save_sunday_offering(cleaned_data, processed_by, language='en'):
    notes = _build_sunday_offering_notes(cleaned_data, language)
    return _save_anonymous_contribution(
        cleaned_data, processed_by, 'offering', notes_override=notes
    )


def _sunday_offering_stats():
    today = timezone.localdate()
    days_since_sunday = (today.weekday() + 1) % 7
    this_sunday = today - timedelta(days=days_since_sunday)
    month_start = today.replace(day=1)
    qs = _sunday_offering_queryset()
    this_sunday_total = qs.filter(contribution_date=this_sunday).aggregate(
        total=models.Sum('amount')
    )['total'] or 0
    month_total = qs.filter(contribution_date__gte=month_start).aggregate(
        total=models.Sum('amount')
    )['total'] or 0
    all_total = qs.aggregate(total=models.Sum('amount'))['total'] or 0
    return {
        'this_sunday_date': this_sunday,
        'this_sunday_total': this_sunday_total,
        'month_total': month_total,
        'all_total': all_total,
        'record_count': qs.count(),
    }


def _save_pledge_entry(cleaned_data, processed_by):
    construction_category = _construction_category()
    donor = cleaned_data['donor']
    amount = cleaned_data['total_amount']
    start_date = cleaned_data['start_date']
    notes = (cleaned_data.get('notes') or '').strip()
    pledge = (
        Pledge.objects.filter(
            donor=donor,
            category=construction_category,
            status__in=['active', 'overdue'],
        )
        .order_by('-created_at')
        .first()
    )
    if pledge:
        pledge.total_amount = _as_whole_amount(pledge.total_amount) + _as_whole_amount(amount)
        if pledge.status != 'active':
            pledge.status = 'active'
        if notes:
            pledge.notes = f'{pledge.notes}\n{notes}'.strip() if pledge.notes else notes
        pledge.save(update_fields=['total_amount', 'status', 'notes', 'updated_at'])
        return pledge
    return Pledge.objects.create(
        donor=donor,
        category=construction_category,
        total_amount=amount,
        amount_paid=0,
        frequency='monthly',
        installment_amount=amount,
        start_date=start_date,
        end_date=start_date + timedelta(days=365),
        status='active',
        notes=notes or 'Ahadi ya ujenzi imeanzishwa kwenye ukurasa wa ahadi.',
    )


def _process_construction_home_entry(cleaned_data, processed_by):
    """Rekodi ahadi mpya na/au malipo ya deni la ujenzi."""
    construction_donor = cleaned_data['construction_donor']
    contribution_date = cleaned_data['contribution_date']
    payment_method = cleaned_data['payment_method']
    notes = (cleaned_data.get('notes') or '').strip()
    construction_pledge_amount = cleaned_data.get('construction_pledge_amount') or 0
    construction_payment_amount = cleaned_data.get('construction_payment_amount') or 0
    construction_category = _construction_category()

    pledge = (
        Pledge.objects.filter(
            donor=construction_donor,
            category=construction_category,
            status__in=['active', 'overdue'],
        )
        .order_by('-created_at')
        .first()
    )

    if construction_pledge_amount > 0:
        if pledge:
            pledge.total_amount = (
                _as_whole_amount(pledge.total_amount)
                + _as_whole_amount(construction_pledge_amount)
            )
            if pledge.status != 'active':
                pledge.status = 'active'
            pledge.save(update_fields=['total_amount', 'status', 'updated_at'])
        else:
            pledge = Pledge.objects.create(
                donor=construction_donor,
                category=construction_category,
                total_amount=construction_pledge_amount,
                amount_paid=0,
                frequency='monthly',
                installment_amount=construction_pledge_amount,
                start_date=contribution_date,
                end_date=contribution_date + timedelta(days=365),
                status='active',
                notes='Ahadi ya ujenzi imeanzishwa kwenye ukurasa wa michango.',
            )

    if construction_payment_amount > 0:
        if not pledge:
            raise ValueError('no_pledge')
        _record_pledge_payment(
            pledge,
            construction_payment_amount,
            payment_method,
            contribution_date,
            notes,
            processed_by,
        )
        pledge.refresh_from_db()
        return pledge, 'payment'

    return pledge, 'pledge'


def _construction_pledges_queryset():
    construction_category = _construction_category()
    return (
        Pledge.objects.filter(category=construction_category)
        .select_related('donor')
        .order_by('-created_at')
    )


def _construction_category():
    return (
        DonationCategory.objects.filter(name__iexact='Ujenzi').first()
        or DonationCategory.objects.create(
            name='Ujenzi',
            description='Michango na ahadi za ujenzi',
            is_active=True,
        )
    )


def _record_pledge_payment(pledge, amount, payment_method, contribution_date, notes, processed_by):
    """Rekodi malipo ya deni la ahadi na usasishe salio."""
    construction_category = pledge.category or _construction_category()
    note_text = f"Malipo ya deni la ujenzi. {notes}".strip() if notes else "Malipo ya deni la ujenzi."
    Donation.objects.create(
        donor=pledge.donor,
        donation_type='special',
        category=construction_category,
        amount=amount,
        payment_method=payment_method,
        notes=note_text,
        donor_name=pledge.donor.full_name,
        contribution_date=contribution_date,
        status='completed',
        processed_by=processed_by,
        processed_date=timezone.now(),
    )
    return pledge.apply_payment(amount)


def _contributions_list_for_user(user, limit=30):
    """Michango iliyounganishwa na mwanachama — orodha ya mtu husika tu."""
    from members.group_permissions import donations_queryset_for_user

    base_qs = (
        Donation.objects.select_related('donor')
        .filter(donor__isnull=False)
        .order_by('-contribution_date', '-donation_date')
    )
    if _can_view_all_donations(user):
        qs = donations_queryset_for_user(user, base_qs)
    else:
        qs = base_qs.filter(donor=user)
    return qs[:limit]


def _csv_response(filename):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def _cash_book_row_from_entry(entry):
    cash = int(entry.cash_amount or 0)
    bank = int(entry.bank_amount or 0)
    return {
        'tarehe': entry.entry_date,
        'maelezo': entry.description,
        'cash': cash if cash else '',
        'bank': bank if bank else '',
    }


def _build_cash_book_sheet_rows():
    """Two-column cash book: DR (left) and CR (right), one row per side-aligned entry only."""
    empty = {'tarehe': '', 'maelezo': '', 'cash': '', 'bank': ''}
    dr_list = [
        _cash_book_row_from_entry(e)
        for e in CashBookEntry.objects.filter(entry_type='dr').order_by('entry_date', 'created_at')
    ]
    cr_list = [
        _cash_book_row_from_entry(e)
        for e in CashBookEntry.objects.filter(entry_type='cr').order_by('entry_date', 'created_at')
    ]
    total_rows = max(len(dr_list), len(cr_list))
    sheet_rows = []
    for i in range(total_rows):
        sheet_rows.append({
            'dr': dr_list[i] if i < len(dr_list) else empty.copy(),
            'cr': cr_list[i] if i < len(cr_list) else empty.copy(),
        })
    return sheet_rows


def _get_accountant_sheet_rows():
    return (
        Donation.objects.values('contribution_date')
        .annotate(
            sadaka=models.Sum(
                models.Case(
                    models.When(donation_type='offering', then='amount'),
                    default=0,
                    output_field=models.DecimalField(max_digits=12, decimal_places=2),
                )
            ),
            zaka=models.Sum(
                models.Case(
                    models.When(donation_type='tithe', then='amount'),
                    default=0,
                    output_field=models.DecimalField(max_digits=12, decimal_places=2),
                )
            ),
            malimbuko=models.Sum(
                models.Case(
                    models.When(donation_type='special', then='amount'),
                    default=0,
                    output_field=models.DecimalField(max_digits=12, decimal_places=2),
                )
            ),
            shukrani=models.Sum(
                models.Case(
                    models.When(donation_type='other', then='amount'),
                    default=0,
                    output_field=models.DecimalField(max_digits=12, decimal_places=2),
                )
            ),
            jumla=models.Sum('amount'),
        )
        .order_by('-contribution_date')
    )

@login_required
def donation_home(request):
    """Donation page: manual entry for accountant, summary for member."""
    if _is_group_only_accountant(request.user):
        from members.group_permissions import groups_accounted_by
        group = groups_accounted_by(request.user).first()
        if group:
            messages.info(
                request,
                'Unaingiza michango ya wanachama wa kundi lako tu.',
            )
            from django.urls import reverse
            return redirect('members:group_donations', pk=group.pk)
        messages.error(request, 'Hujapangiwa kundi la mhasibu.')
        return redirect('members:group_list')

    lang = LanguageManager.get_current_language(request)
    campaigns = DonationCampaign.objects.filter(status='active').order_by('-created_at')
    categories = DonationCategory.objects.all()
    is_accountant = _is_accountant(request.user)
    is_accountant_role = request.user.role == 'accountant'
    has_accountant_access = bool(getattr(request.user, 'can_post_member_donations', False))
    can_publish_notice = _can_publish_donation_notice(request.user)
    today = timezone.localdate()
    donor_scope = _allowed_donor_ids(request.user)
    construction_entry_form = None
    notice_form = None

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create_notice':
            if not can_publish_notice:
                messages.error(request, 'Huna ruhusa ya kutuma taarifa ya michango.')
                return redirect('donations:home')
            notice_form = DonationNoticeForm(request.POST, language=lang)
            if notice_form.is_valid():
                notice = notice_form.save(commit=False)
                notice.created_by = request.user
                notice.save()
                messages.success(request, 'Taarifa ya mchango imetumwa kikamilifu.')
                return redirect('donations:home')
            construction_entry_form = (
                ConstructionHomeEntryForm(allowed_donor_ids=donor_scope, language=lang)
                if is_accountant and _can_manage_construction_pledges(request.user)
                else None
            )
        elif action in ('pay_pledge', 'reduce_pledge'):
            if not _can_manage_construction_pledges(request.user):
                messages.error(request, 'Huna ruhusa ya kudhibiti ahadi za ujenzi.')
                return redirect('donations:home')
            pledge = get_object_or_404(
                Pledge.objects.select_related('donor', 'category'),
                pk=request.POST.get('pledge_id'),
            )
            construction_category = _construction_category()
            if pledge.category_id and pledge.category_id != construction_category.id:
                messages.error(request, 'Ahadi hii si ya ujenzi.')
                return redirect('donations:home')
            if not pledge.has_outstanding_debt:
                messages.info(request, 'Deni la ahadi hili tayari limekwisha.')
                return redirect('donations:home')

            if action == 'pay_pledge':
                pay_form = PledgePaymentForm(
                    request.POST, pledge=pledge, language=lang
                )
                if pay_form.is_valid():
                    new_balance = _record_pledge_payment(
                        pledge,
                        pay_form.cleaned_data['amount'],
                        pay_form.cleaned_data['payment_method'],
                        pay_form.cleaned_data['contribution_date'],
                        pay_form.cleaned_data.get('notes', ''),
                        request.user,
                    )
                    if pledge.debt_balance_display == 0:
                        messages.success(
                            request,
                            f'Malipo yamehifadhiwa. Deni la {pledge.donor.full_name} limefutika kabisa.',
                        )
                    else:
                        messages.success(
                            request,
                            f'Malipo yamehifadhiwa. Salio la deni: TZS {pledge.debt_balance_display:,}',
                        )
                    return redirect('donations:home')
                for error in pay_form.non_field_errors():
                    messages.error(request, error)
                for field_name, errors in pay_form.errors.items():
                    label = pay_form.fields[field_name].label or field_name
                    for error in errors:
                        messages.error(request, f'{label}: {error}')
            else:
                reduce_form = PledgeReduceForm(
                    request.POST, pledge=pledge, language=lang
                )
                if reduce_form.is_valid():
                    reason = (reduce_form.cleaned_data.get('reason') or '').strip()
                    reduce_amount = reduce_form.cleaned_data['reduce_amount']
                    new_balance = pledge.reduce_commitment(reduce_amount)
                    if reason:
                        pledge.notes = f"{pledge.notes}\nPunguzo: TZS {int(reduce_amount):,} — {reason}".strip()
                        pledge.save(update_fields=['notes', 'updated_at'])
                    if pledge.debt_balance_display == 0:
                        messages.success(
                            request,
                            f'Ahadi imepunguzwa. Deni la {pledge.donor.full_name} limefutika kabisa.',
                        )
                    else:
                        messages.success(
                            request,
                            f'Ahadi imepunguzwa. Salio la deni: TZS {pledge.debt_balance_display:,}',
                        )
                    return redirect('donations:home')
                for error in reduce_form.non_field_errors():
                    messages.error(request, error)
                for field_name, errors in reduce_form.errors.items():
                    label = reduce_form.fields[field_name].label or field_name
                for error in errors:
                    messages.error(request, f'{label}: {error}')
            if notice_form is None and can_publish_notice:
                notice_form = DonationNoticeForm(language=lang)
            if construction_entry_form is None and is_accountant and _can_manage_construction_pledges(request.user):
                construction_entry_form = ConstructionHomeEntryForm(
                    allowed_donor_ids=donor_scope, language=lang
                )
        elif action == 'construction_entry':
            if not is_accountant or not _can_manage_construction_pledges(request.user):
                messages.error(request, 'Huna ruhusa ya kuingiza ahadi za ujenzi.')
                return redirect('donations:home')
            if _is_group_only_accountant(request.user):
                messages.error(
                    request,
                    'Mhasibu wa kundi hutumia ukurasa wa Michango wa Kundi.',
                )
                return redirect('donations:home')
            donor_scope = _allowed_donor_ids(request.user)
            construction_entry_form = ConstructionHomeEntryForm(
                request.POST, allowed_donor_ids=donor_scope, language=lang
            )
            if construction_entry_form.is_valid():
                try:
                    pledge, result = _process_construction_home_entry(
                        construction_entry_form.cleaned_data,
                        request.user,
                    )
                except ValueError:
                    messages.error(
                        request,
                        'Mwanachama huyu hana ahadi ya ujenzi. Weka ahadi kwanza au ingiza ahadi mpya.',
                    )
                    return redirect('donations:home')

                donor_name = construction_entry_form.cleaned_data['construction_donor'].full_name
                if result == 'payment':
                    if pledge.debt_balance_display == 0:
                        messages.success(
                            request,
                            f'Malipo ya ujenzi yamehifadhiwa. Deni la {donor_name} limefutika kabisa.',
                        )
                    else:
                        messages.success(
                            request,
                            f'Malipo ya ujenzi yamehifadhiwa. Salio la deni: TZS {pledge.debt_balance_display:,}',
                        )
                else:
                    messages.success(
                        request,
                        f'Ahadi imeandikwa kwa {donor_name}. '
                        f'Salio la deni: TZS {pledge.debt_balance_display:,}',
                    )
                return redirect('donations:home')

            for error in construction_entry_form.non_field_errors():
                messages.error(request, error)
            for field_name, errors in construction_entry_form.errors.items():
                if field_name == '__all__':
                    continue
                label = construction_entry_form.fields[field_name].label or field_name
                for error in errors:
                    messages.error(request, f'{label}: {error}')
            if notice_form is None and can_publish_notice:
                notice_form = DonationNoticeForm(language=lang)
        else:
            messages.error(request, 'Kitendo hakitambuliki.')
            return redirect('donations:home')
    else:
        construction_entry_form = (
            ConstructionHomeEntryForm(allowed_donor_ids=donor_scope, language=lang)
            if is_accountant and _can_manage_construction_pledges(request.user)
            else None
        )
        notice_form = DonationNoticeForm(language=lang) if can_publish_notice else None

    if notice_form is None and can_publish_notice:
        notice_form = DonationNoticeForm(language=lang)

    # Show active donation notices (all members, or targeted member only).
    active_notices = DonationNotice.objects.filter(
        is_active=True,
        start_date__lte=today,
        end_date__gte=today,
    ).filter(
        Q(target_member__isnull=True) | Q(target_member=request.user)
    ).select_related('created_by', 'target_member').order_by('-created_at')

    can_view_sadaka = _can_view_sadaka(request.user)
    my_donations = Donation.objects.filter(donor=request.user)
    totals = my_donations.values('donation_type').annotate(total=models.Sum('amount'))
    totals_map = {item['donation_type']: item['total'] or 0 for item in totals}
    if can_view_sadaka:
        church_offering_total = (
            Donation.objects.filter(donation_type='offering').aggregate(
                total=models.Sum('amount')
            )['total']
            or 0
        )
    else:
        church_offering_total = None
    contributions_list = _contributions_list_for_user(request.user, limit=30)
    construction_pledges = []
    if can_view_sadaka:
        construction_pledges = list(_construction_pledges_queryset()[:30])

    six_months_ago = timezone.now().date() - timedelta(days=180)
    donation_qs = Donation.objects.filter(contribution_date__gte=six_months_ago)
    if request.user.role == 'member':
        donation_qs = donation_qs.filter(donor=request.user)

    donation_monthly = (
        donation_qs.annotate(month=TruncMonth('contribution_date'))
        .values('month')
        .annotate(total=models.Sum('amount'))
        .order_by('month')
    )
    donation_chart_labels = [item['month'].strftime('%b %Y') for item in donation_monthly if item['month']]
    donation_chart_data = [float(item['total'] or 0) for item in donation_monthly]

    registration_monthly = (
        ChurchUser.objects.filter(role='member', date_joined__date__gte=six_months_ago)
        .annotate(month=TruncMonth('date_joined'))
        .values('month')
        .annotate(total=models.Count('id'))
        .order_by('month')
    )
    registration_chart_labels = [item['month'].strftime('%b %Y') for item in registration_monthly if item['month']]
    registration_chart_data = [int(item['total'] or 0) for item in registration_monthly]

    context = {
        'campaigns': campaigns,
        'categories': categories,
        'construction_entry_form': construction_entry_form,
        'is_accountant': is_accountant,
        'is_accountant_role': is_accountant_role,
        'has_accountant_access': has_accountant_access,
        'can_publish_notice': can_publish_notice,
        'notice_form': notice_form,
        'active_notices': active_notices,
        'total_all': my_donations.aggregate(total=models.Sum('amount'))['total'] or 0,
        'total_tithe': totals_map.get('tithe', 0),
        'total_my_offering': totals_map.get('offering', 0),
        'total_offering': church_offering_total,
        'can_view_sadaka': can_view_sadaka,
        'can_view_all_donations': _can_view_all_donations(request.user),
        'total_special': totals_map.get('special', 0),
        'total_other': totals_map.get('other', 0),
        'recent_my_donations': my_donations.order_by(
            '-contribution_date', '-donation_date'
        )[:10],
        'contributions_list': contributions_list,
        'show_management_graphs': request.user.role in {'pastor', 'accountant'},
        'donation_chart_labels': json.dumps(donation_chart_labels),
        'donation_chart_data': json.dumps(donation_chart_data),
        'registration_chart_labels': json.dumps(registration_chart_labels),
        'registration_chart_data': json.dumps(registration_chart_data),
        'construction_pledges': construction_pledges,
        'can_manage_construction_pledges': _can_manage_construction_pledges(request.user),
        'pledge_payment_form': PledgePaymentForm(language=lang),
        'pledge_reduce_form': PledgeReduceForm(language=lang),
        'current_language': lang,
    }
    return render(request, 'donations/donation_home.html', context)

@login_required
def make_donation(request, campaign_id=None):
    """Public donate endpoint disabled: donations are entered by accountant."""
    messages.info(request, 'Michango inaingizwa na mhasibu baada ya kupokea malipo.')
    return redirect('donations:home')

class DonationHistoryView(LoginRequiredMixin, ListView):
    """View donation history by role permissions."""
    model = Donation
    template_name = 'donations/donation_history.html'
    context_object_name = 'donations'
    paginate_by = 10
    
    def get_queryset(self):
        from members.group_permissions import donations_queryset_for_user

        base_qs = Donation.objects.select_related('donor', 'recorded_for_group').order_by(
            '-donation_date'
        )
        if _can_view_all_donations(self.request.user):
            qs = donations_queryset_for_user(self.request.user, base_qs)
        else:
            qs = base_qs.filter(donor=self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        can_view_sadaka = _can_view_sadaka(self.request.user)
        by_type = qs.values('donation_type').annotate(total=models.Sum('amount'))
        totals_map = {item['donation_type']: item['total'] or 0 for item in by_type}
        context['total_tithe'] = totals_map.get('tithe', 0)
        context['total_offering'] = totals_map.get('offering', 0)
        context['total_special'] = totals_map.get('special', 0)
        context['total_other'] = totals_map.get('other', 0)
        context['total_all'] = qs.aggregate(total=models.Sum('amount'))['total'] or 0
        context['can_view_all_donations'] = _can_view_all_donations(self.request.user)
        context['can_view_sadaka'] = can_view_sadaka
        return context


def _tithe_donations_queryset():
    return (
        Donation.objects.filter(donation_type='tithe')
        .select_related('donor')
        .order_by('-contribution_date', '-donation_date')
    )


class TitheContributionListView(LoginRequiredMixin, ListView):
    model = Donation
    template_name = 'donations/tithe_contribution_list.html'
    context_object_name = 'tithe_donations'
    paginate_by = 30

    def dispatch(self, request, *args, **kwargs):
        if not _can_view_tithe_list(request.user):
            messages.error(request, 'Ni mhasibu au mchungaji tu anaweza kuona list ya zaka.')
            return redirect('donations:home')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return _tithe_donations_queryset()

    def post(self, request, *args, **kwargs):
        from members.language_utils import get_translation

        if request.POST.get('action') != 'tithe_entry':
            return redirect('donations:tithe_list')
        if not _can_enter_tithe(request.user):
            messages.error(request, get_translation('tithe_no_entry_access', LanguageManager.get_current_language(request)))
            return redirect('donations:tithe_list')

        lang = LanguageManager.get_current_language(request)
        donor_scope = _allowed_donor_ids(request.user)
        form = TitheEntryForm(request.POST, allowed_donor_ids=donor_scope, language=lang)
        if form.is_valid():
            _save_tithe_entry(form.cleaned_data, request.user)
            messages.success(request, get_translation('tithe_saved_success', lang))
            return redirect('donations:tithe_list')

        for error in form.non_field_errors():
            messages.error(request, error)
        for field_name, errors in form.errors.items():
            label = form.fields.get(field_name).label if field_name in form.fields else field_name
            for error in errors:
                messages.error(request, f'{label}: {error}')

        self.object_list = self.get_queryset()
        context = self.get_context_data(tithe_entry_form=form)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lang = LanguageManager.get_current_language(self.request)
        donor_scope = _allowed_donor_ids(self.request.user)
        context['can_enter_tithe'] = _can_enter_tithe(self.request.user)
        if context['can_enter_tithe']:
            context.setdefault(
                'tithe_entry_form',
                TitheEntryForm(allowed_donor_ids=donor_scope, language=lang),
            )
        else:
            context['tithe_entry_form'] = None
        return context


def _malimbuko_list_context_extra(donations):
    total_money = sum(
        int(d.amount or 0)
        for d in donations
        if d.tithe_gift_type == 'money'
    )
    return {
        'total_count': len(donations),
        'total_money': total_money,
    }


class MalimbukoContributionListView(LoginRequiredMixin, ListView):
    model = Donation
    template_name = 'donations/malimbuko_contribution_list.html'
    context_object_name = 'malimbuko_donations'
    paginate_by = 30

    def dispatch(self, request, *args, **kwargs):
        if not _can_view_malimbuko_list(request.user):
            messages.error(request, 'Ni mhasibu au mchungaji tu anaweza kuona list ya malimbuko.')
            return redirect('donations:home')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return _malimbuko_donations_queryset()

    def post(self, request, *args, **kwargs):
        from members.language_utils import get_translation

        if request.POST.get('action') != 'malimbuko_entry':
            return redirect('donations:malimbuko_list')
        if not _can_enter_malimbuko(request.user):
            messages.error(
                request,
                get_translation('malimbuko_no_entry_access', LanguageManager.get_current_language(request)),
            )
            return redirect('donations:malimbuko_list')

        lang = LanguageManager.get_current_language(request)
        donor_scope = _allowed_donor_ids(request.user)
        form = MalimbukoEntryForm(request.POST, allowed_donor_ids=donor_scope, language=lang)
        if form.is_valid():
            _save_malimbuko_entry(form.cleaned_data, request.user)
            messages.success(request, get_translation('malimbuko_saved_success', lang))
            return redirect('donations:malimbuko_list')

        for error in form.non_field_errors():
            messages.error(request, error)
        for field_name, errors in form.errors.items():
            label = form.fields.get(field_name).label if field_name in form.fields else field_name
            for error in errors:
                messages.error(request, f'{label}: {error}')

        self.object_list = self.get_queryset()
        context = self.get_context_data(malimbuko_entry_form=form)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lang = LanguageManager.get_current_language(self.request)
        donor_scope = _allowed_donor_ids(self.request.user)
        context['can_enter_malimbuko'] = _can_enter_malimbuko(self.request.user)
        if context['can_enter_malimbuko']:
            context.setdefault(
                'malimbuko_entry_form',
                MalimbukoEntryForm(allowed_donor_ids=donor_scope, language=lang),
            )
        else:
            context['malimbuko_entry_form'] = None
        return context


@login_required
def malimbuko_list_print(request):
    if not _can_view_malimbuko_list(request.user):
        messages.error(request, 'Ni mhasibu au mchungaji tu anaweza kuona list ya malimbuko.')
        return redirect('donations:home')

    malimbuko_donations = list(_malimbuko_donations_queryset())
    extra = _malimbuko_list_context_extra(malimbuko_donations)
    return render(request, 'donations/malimbuko_list_print.html', church_print_context(
        malimbuko_donations=malimbuko_donations,
        report_date=timezone.localdate(),
        **extra,
    ))


@login_required
def export_malimbuko_list_csv(request):
    from members.language_utils import get_translation

    if not _can_view_malimbuko_list(request.user):
        messages.error(request, 'Ni mhasibu au mchungaji tu anaweza kupakua report ya malimbuko.')
        return redirect('donations:home')

    lang = LanguageManager.get_current_language(request)
    qs = _malimbuko_donations_queryset()
    response = _csv_response('malimbuko_contributions_report.csv')
    writer = csv.writer(response)
    writer.writerow([
        get_translation('table_date', lang),
        get_translation('malimbuko_col_amount', lang),
        get_translation('malimbuko_col_miladi', lang),
        get_translation('malimbuko_col_harvest', lang),
        get_translation('payment_method', lang),
    ])
    for donation in qs:
        writer.writerow([
            donation.contribution_date,
            int(donation.amount or 0) if donation.tithe_gift_type == 'money' else '',
            donation.malimbuko_miladi_source,
            donation.tithe_asset_description or '',
            donation.payment_method_sw or donation.get_payment_method_display(),
        ])
    return response


class _ContributionPageMixin:
    """Msingi wa kurasa za michango (sadaka, shukrani)."""
    donation_type = None
    entry_action = None
    i18n_prefix = None
    err_amount_key = None
    csv_filename = None
    list_redirect_name = None
    paginate_by = 30
    template_name = 'donations/simple_contribution_list.html'
    context_object_name = 'contributions'

    def dispatch(self, request, *args, **kwargs):
        if not _can_view_tithe_list(request.user):
            messages.error(request, 'Ni mhasibu au mchungaji tu anaweza kuona orodha hii.')
            return redirect('donations:home')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return _donations_by_type_queryset(self.donation_type)

    def _page_keys(self):
        p = self.i18n_prefix
        return {
            'title': f'{p}_list_title',
            'subtitle': f'{p}_list_subtitle',
            'enter_section': f'{p}_enter_section',
            'enter_help': f'{p}_enter_help',
            'save_btn': f'{p}_save_btn',
            'no_records': f'{p}_no_records',
            'print_title': f'{p}_print_title',
            'preview_print': f'{p}_preview_print',
            'download_csv': f'{p}_download_csv',
            'download_pdf': f'{p}_download_pdf',
            'back_list': f'{p}_back_list',
            'total_records': f'{p}_total_records',
            'total_cash': f'{p}_total_cash',
            'saved_success': f'{p}_saved_success',
            'no_entry_access': f'{p}_no_entry_access',
        }

    def post(self, request, *args, **kwargs):
        from members.language_utils import get_translation

        keys = self._page_keys()
        if request.POST.get('action') != self.entry_action:
            return redirect(self.list_redirect_name)
        if not _can_enter_tithe(request.user):
            messages.error(
                request,
                get_translation(keys['no_entry_access'], LanguageManager.get_current_language(request)),
            )
            return redirect(self.list_redirect_name)

        lang = LanguageManager.get_current_language(request)
        form = AnonymousContributionEntryForm(
            request.POST,
            language=lang,
            err_amount_key=self.err_amount_key,
        )
        if form.is_valid():
            _save_anonymous_contribution(form.cleaned_data, request.user, self.donation_type)
            messages.success(request, get_translation(keys['saved_success'], lang))
            return redirect(self.list_redirect_name)

        for error in form.non_field_errors():
            messages.error(request, error)
        for field_name, errors in form.errors.items():
            label = form.fields.get(field_name).label if field_name in form.fields else field_name
            for error in errors:
                messages.error(request, f'{label}: {error}')

        self.object_list = self.get_queryset()
        context = self.get_context_data(entry_form=form)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lang = LanguageManager.get_current_language(self.request)
        keys = self._page_keys()
        context['page_keys'] = keys
        context['entry_action'] = self.entry_action
        context['can_enter'] = _can_enter_tithe(self.request.user)
        context['print_url'] = self.print_url_name
        context['export_url'] = self.export_url_name
        context['list_url'] = self.list_redirect_name
        if context['can_enter']:
            context.setdefault(
                'entry_form',
                AnonymousContributionEntryForm(
                    language=lang,
                    err_amount_key=self.err_amount_key,
                ),
            )
        else:
            context['entry_form'] = None
        qs = self.get_queryset()
        context['total_count'] = qs.count()
        context['total_money'] = qs.aggregate(total=models.Sum('amount'))['total'] or 0
        return context


class SundayOfferingListView(LoginRequiredMixin, ListView):
    """Sadaka ya Jumapili — ukurasa maalum wa kuhifadhi na kuona rekodi."""
    model = Donation
    template_name = 'donations/sunday_offering_list.html'
    context_object_name = 'contributions'
    paginate_by = 30

    def dispatch(self, request, *args, **kwargs):
        if not _can_view_tithe_list(request.user):
            messages.error(request, 'Ni mhasibu au mchungaji tu anaweza kuona sadaka ya Jumapili.')
            return redirect('donations:home')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return _sunday_offering_queryset()

    def post(self, request, *args, **kwargs):
        from members.language_utils import get_translation

        if request.POST.get('action') != 'sunday_offering_entry':
            return redirect('donations:offering_list')
        if not _can_enter_tithe(request.user):
            messages.error(
                request,
                get_translation('offering_no_entry_access', LanguageManager.get_current_language(request)),
            )
            return redirect('donations:offering_list')

        lang = LanguageManager.get_current_language(request)
        form = SundayOfferingEntryForm(request.POST, language=lang)
        if form.is_valid():
            _save_sunday_offering(form.cleaned_data, request.user, language=lang)
            messages.success(request, get_translation('sunday_saved_success', lang))
            return redirect('donations:offering_list')

        for error in form.non_field_errors():
            messages.error(request, error)
        for field_name, errors in form.errors.items():
            label = form.fields.get(field_name).label if field_name in form.fields else field_name
            for error in errors:
                messages.error(request, f'{label}: {error}')

        self.object_list = self.get_queryset()
        context = self.get_context_data(entry_form=form)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lang = LanguageManager.get_current_language(self.request)
        context['can_enter'] = _can_enter_tithe(self.request.user)
        if context['can_enter']:
            context.setdefault(
                'entry_form',
                SundayOfferingEntryForm(language=lang),
            )
        else:
            context['entry_form'] = None
        stats = _sunday_offering_stats()
        context.update(stats)
        return context


# Alias — URL ya zamani (sadaka-list) inaelekeza hapa
OfferingContributionListView = SundayOfferingListView


class ShukraniContributionListView(LoginRequiredMixin, _ContributionPageMixin, ListView):
    donation_type = 'other'
    entry_action = 'shukrani_entry'
    i18n_prefix = 'shukrani'
    err_amount_key = 'shukrani_err_amount'
    csv_filename = 'shukrani_contributions_report.csv'
    list_redirect_name = 'donations:shukrani_list'
    print_url_name = 'donations:shukrani_list_print'
    export_url_name = 'donations:export_shukrani_csv'


def _simple_contribution_print(request, page_config):
    from members.language_utils import get_translation

    if not _can_view_tithe_list(request.user):
        messages.error(request, 'Ni mhasibu au mchungaji tu anaweza kuona orodha hii.')
        return redirect('donations:home')

    lang = LanguageManager.get_current_language(request)
    prefix = page_config['i18n_prefix']
    donations = list(_donations_by_type_queryset(page_config['donation_type']))
    total_money = sum(int(d.amount or 0) for d in donations)
    return render(request, 'donations/simple_contribution_print.html', church_print_context(
        contributions=donations,
        report_date=timezone.localdate(),
        page_keys={
            'title': f'{prefix}_list_title',
            'print_title': f'{prefix}_print_title',
            'print_date': f'{prefix}_print_date',
            'total_records': f'{prefix}_total_records',
            'total_cash': f'{prefix}_total_cash',
            'no_records': f'{prefix}_no_records',
            'back_list': f'{prefix}_back_list',
            'download_pdf': f'{prefix}_download_pdf',
        },
        list_url_name=page_config['list_url_name'],
        total_count=len(donations),
        total_money=total_money,
        lang=lang,
    ))


def _export_simple_contribution_csv(request, page_config):
    from members.language_utils import get_translation

    if not _can_view_tithe_list(request.user):
        messages.error(request, 'Ni mhasibu au mchungaji tu anaweza kupakua report.')
        return redirect('donations:home')

    lang = LanguageManager.get_current_language(request)
    qs = _donations_by_type_queryset(page_config['donation_type'])
    response = _csv_response(page_config['csv_filename'])
    writer = csv.writer(response)
    writer.writerow([
        get_translation('table_date', lang),
        get_translation('don_col_amount', lang),
        get_translation('payment_method', lang),
        get_translation('don_col_details', lang),
    ])
    for donation in qs:
        writer.writerow([
            donation.contribution_date,
            int(donation.amount or 0),
            donation.payment_method_sw or donation.get_payment_method_display(),
            donation.notes or '',
        ])
    return response


@login_required
def offering_list_print(request):
    from members.language_utils import get_translation

    if not _can_view_tithe_list(request.user):
        messages.error(request, 'Ni mhasibu au mchungaji tu anaweza kuona orodha hii.')
        return redirect('donations:home')

    lang = LanguageManager.get_current_language(request)
    donations = list(_sunday_offering_queryset())
    total_money = sum(int(d.amount or 0) for d in donations)
    stats = _sunday_offering_stats()
    return render(request, 'donations/sunday_offering_print.html', church_print_context(
        contributions=donations,
        report_date=timezone.localdate(),
        total_count=len(donations),
        total_money=total_money,
        this_sunday_total=stats['this_sunday_total'],
        this_sunday_date=stats['this_sunday_date'],
        month_total=stats['month_total'],
        lang=lang,
    ))


@login_required
def export_offering_csv(request):
    return _export_simple_contribution_csv(request, {
        'donation_type': 'offering',
        'csv_filename': 'sadaka_jumapili_report.csv',
    })


@login_required
def shukrani_list_print(request):
    return _simple_contribution_print(request, {
        'donation_type': 'other',
        'i18n_prefix': 'shukrani',
        'list_url_name': 'donations:shukrani_list',
    })


@login_required
def export_shukrani_csv(request):
    return _export_simple_contribution_csv(request, {
        'donation_type': 'other',
        'csv_filename': 'shukrani_contributions_report.csv',
    })


class ConstructionPledgeListView(LoginRequiredMixin, ListView):
    model = Pledge
    template_name = 'donations/construction_pledge_list.html'
    context_object_name = 'construction_pledges'
    paginate_by = 30

    def dispatch(self, request, *args, **kwargs):
        if not _can_view_sadaka(request.user):
            messages.error(request, 'Huna ruhusa ya kuona ahadi za ujenzi.')
            return redirect('donations:home')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return _construction_pledges_queryset()

    def post(self, request, *args, **kwargs):
        from members.language_utils import get_translation

        lang = LanguageManager.get_current_language(request)
        action = request.POST.get('action')
        redirect_name = 'donations:pledge_list'

        if action == 'pledge_entry':
            if not _can_manage_construction_pledges(request.user):
                messages.error(request, get_translation('pledge_no_entry_access', lang))
                return redirect(redirect_name)
            donor_scope = _allowed_donor_ids(request.user)
            form = PledgeEntryForm(request.POST, allowed_donor_ids=donor_scope, language=lang)
            if form.is_valid():
                pledge = _save_pledge_entry(form.cleaned_data, request.user)
                messages.success(
                    request,
                    f'{get_translation("pledge_saved_success", lang)} {pledge.donor.full_name}. '
                    f'Salio la deni: TZS {pledge.debt_balance_display:,}',
                )
                return redirect(redirect_name)
            for error in form.non_field_errors():
                messages.error(request, error)
            for field_name, errors in form.errors.items():
                label = form.fields.get(field_name).label if field_name in form.fields else field_name
                for error in errors:
                    messages.error(request, f'{label}: {error}')
            self.object_list = self.get_queryset()
            context = self.get_context_data(pledge_entry_form=form)
            return self.render_to_response(context)

        if action in ('pay_pledge', 'reduce_pledge'):
            if not _can_manage_construction_pledges(request.user):
                messages.error(request, 'Huna ruhusa ya kudhibiti ahadi za ujenzi.')
                return redirect(redirect_name)
            pledge = get_object_or_404(
                Pledge.objects.select_related('donor', 'category'),
                pk=request.POST.get('pledge_id'),
            )
            construction_category = _construction_category()
            if pledge.category_id and pledge.category_id != construction_category.id:
                messages.error(request, 'Ahadi hii si ya ujenzi.')
                return redirect(redirect_name)
            if not pledge.has_outstanding_debt:
                messages.info(request, 'Deni la ahadi hili tayari limekwisha.')
                return redirect(redirect_name)

            if action == 'pay_pledge':
                pay_form = PledgePaymentForm(request.POST, pledge=pledge, language=lang)
                if pay_form.is_valid():
                    _record_pledge_payment(
                        pledge,
                        pay_form.cleaned_data['amount'],
                        pay_form.cleaned_data['payment_method'],
                        pay_form.cleaned_data['contribution_date'],
                        pay_form.cleaned_data.get('notes', ''),
                        request.user,
                    )
                    if pledge.debt_balance_display == 0:
                        messages.success(
                            request,
                            f'Malipo yamehifadhiwa. Deni la {pledge.donor.full_name} limefutika kabisa.',
                        )
                    else:
                        messages.success(
                            request,
                            f'Malipo yamehifadhiwa. Salio la deni: TZS {pledge.debt_balance_display:,}',
                        )
                    return redirect(redirect_name)
                for error in pay_form.non_field_errors():
                    messages.error(request, error)
            else:
                reduce_form = PledgeReduceForm(request.POST, pledge=pledge, language=lang)
                if reduce_form.is_valid():
                    reason = (reduce_form.cleaned_data.get('reason') or '').strip()
                    reduce_amount = reduce_form.cleaned_data['reduce_amount']
                    pledge.reduce_commitment(reduce_amount)
                    if reason:
                        pledge.notes = f"{pledge.notes}\nPunguzo: TZS {int(reduce_amount):,} — {reason}".strip()
                        pledge.save(update_fields=['notes', 'updated_at'])
                    if pledge.debt_balance_display == 0:
                        messages.success(
                            request,
                            f'Ahadi imepunguzwa. Deni la {pledge.donor.full_name} limefutika kabisa.',
                        )
                    else:
                        messages.success(
                            request,
                            f'Ahadi imepunguzwa. Salio la deni: TZS {pledge.debt_balance_display:,}',
                        )
                    return redirect(redirect_name)
                for error in reduce_form.non_field_errors():
                    messages.error(request, error)

        return redirect(redirect_name)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lang = LanguageManager.get_current_language(self.request)
        donor_scope = _allowed_donor_ids(self.request.user)
        context['can_manage_construction_pledges'] = _can_manage_construction_pledges(self.request.user)
        context['can_view_sadaka'] = _can_view_sadaka(self.request.user)
        context['pledge_payment_form'] = PledgePaymentForm(language=lang)
        if context['can_manage_construction_pledges']:
            context.setdefault(
                'pledge_entry_form',
                PledgeEntryForm(allowed_donor_ids=donor_scope, language=lang),
            )
        else:
            context['pledge_entry_form'] = None
        return context


def _pledge_list_context_extra(pledges):
    total_pledged = sum(int(p.total_amount or 0) for p in pledges)
    total_paid = sum(int(p.amount_paid or 0) for p in pledges)
    total_debt = sum(int(p.debt_balance_display or 0) for p in pledges)
    return {
        'total_count': len(pledges),
        'total_pledged': total_pledged,
        'total_paid': total_paid,
        'total_debt': total_debt,
    }


@login_required
def pledge_list_print(request):
    if not _can_view_sadaka(request.user):
        messages.error(request, 'Huna ruhusa ya kuona ahadi za ujenzi.')
        return redirect('donations:home')

    construction_pledges = list(_construction_pledges_queryset())
    extra = _pledge_list_context_extra(construction_pledges)
    return render(request, 'donations/construction_pledge_list_print.html', church_print_context(
        construction_pledges=construction_pledges,
        report_date=timezone.localdate(),
        **extra,
    ))


@login_required
def tithe_list_print(request):
    if not _can_view_tithe_list(request.user):
        messages.error(request, 'Ni mhasibu au mchungaji tu anaweza kuona list ya zaka.')
        return redirect('donations:home')

    tithe_donations = list(_tithe_donations_queryset())
    total_money = sum(
        int(donation.amount or 0)
        for donation in tithe_donations
        if donation.tithe_gift_type == 'money'
    )
    return render(request, 'donations/tithe_list_print.html', church_print_context(
        tithe_donations=tithe_donations,
        report_date=timezone.localdate(),
        total_count=len(tithe_donations),
        total_money=total_money,
    ))


@login_required
def cash_book_view(request):
    if not _can_view_cash_book(request.user):
        messages.error(request, 'Ni mhasibu au mchungaji tu anaweza kuona cash book.')
        return redirect('donations:home')

    can_manage_cash_book = _can_manage_cash_book(request.user)
    if request.method == 'POST':
        if not can_manage_cash_book:
            messages.error(request, 'Ni mhasibu mwenye access tu anaweza kurekodi cash book.')
            return redirect('donations:cash_book')
        form = CashBookEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.created_by = request.user
            entry.save()
            messages.success(request, 'Cash book entry imehifadhiwa kikamilifu.')
            return redirect('donations:cash_book')
    else:
        form = CashBookEntryForm() if can_manage_cash_book else None

    entries = CashBookEntry.objects.select_related('created_by').order_by('-entry_date', '-created_at')[:80]
    totals = CashBookEntry.objects.aggregate(
        dr_cash=models.Sum(models.Case(models.When(entry_type='dr', then='cash_amount'), default=0, output_field=models.DecimalField(max_digits=14, decimal_places=2))),
        cr_cash=models.Sum(models.Case(models.When(entry_type='cr', then='cash_amount'), default=0, output_field=models.DecimalField(max_digits=14, decimal_places=2))),
        dr_bank=models.Sum(models.Case(models.When(entry_type='dr', then='bank_amount'), default=0, output_field=models.DecimalField(max_digits=14, decimal_places=2))),
        cr_bank=models.Sum(models.Case(models.When(entry_type='cr', then='bank_amount'), default=0, output_field=models.DecimalField(max_digits=14, decimal_places=2))),
    )
    dr_cash = totals.get('dr_cash') or 0
    cr_cash = totals.get('cr_cash') or 0
    dr_bank = totals.get('dr_bank') or 0
    cr_bank = totals.get('cr_bank') or 0

    return render(request, 'donations/cash_book.html', {
        'form': form,
        'entries': entries,
        'can_manage_cash_book': can_manage_cash_book,
        'can_view_cash_book': True,
        'cash_balance': dr_cash - cr_cash,
        'bank_balance': dr_bank - cr_bank,
        'total_dr_cash': dr_cash,
        'total_cr_cash': cr_cash,
        'total_dr_bank': dr_bank,
        'total_cr_bank': cr_bank,
    })


def _build_income_allocation_report(start_date, end_date, include_sadaka=True):
    period_qs = Donation.objects.filter(
        contribution_date__range=(start_date, end_date),
        status='completed',
    )

    total_zaka = period_qs.filter(donation_type='tithe').aggregate(total=models.Sum('amount'))['total'] or 0
    total_sadaka = 0
    if include_sadaka:
        total_sadaka = period_qs.filter(donation_type='offering').aggregate(
            total=models.Sum('amount')
        )['total'] or 0
    total_mapato_mengineyo = period_qs.filter(
        donation_type__in=['other', 'special']
    ).aggregate(total=models.Sum('amount'))['total'] or 0
    total_mapato = total_zaka + total_sadaka + total_mapato_mengineyo

    allocations = [
        ('Posho ya Mchungaji', 65),
        ('Zaka ya Ofisi Kuu', 10),
        ('Elimu ya Vyuo', 5),
        ('Akiba Mafao ya Mchungaji', 5),
        ('Matumizi ya Kanisa', 15),
    ]
    allocation_rows = []
    for name, percent in allocations:
        allocation_rows.append({
            'name': name,
            'percent': percent,
            'amount': (total_mapato * percent) / 100 if total_mapato else 0,
        })

    return {
        'start_date': start_date,
        'end_date': end_date,
        'total_zaka': total_zaka,
        'total_sadaka': total_sadaka,
        'total_mapato_mengineyo': total_mapato_mengineyo,
        'total_mapato': total_mapato,
        'allocation_rows': allocation_rows,
    }


@login_required
def income_allocation_report_view(request):
    if not _can_view_income_allocation(request.user):
        messages.error(request, 'Ni mhasibu au mchungaji tu anaweza kuona report hii.')
        return redirect('donations:home')

    form = IncomeAllocationReportForm(request.GET or None)
    report = None

    can_view_sadaka = _can_view_sadaka(request.user)
    if form.is_valid():
        report = _build_income_allocation_report(
            form.cleaned_data['start_date'],
            form.cleaned_data['end_date'],
            include_sadaka=can_view_sadaka,
        )

    return render(request, 'donations/income_allocation_report.html', {
        'form': form,
        'report': report,
        'can_view_sadaka': can_view_sadaka,
    })


@login_required
def income_allocation_report_print(request):
    if not _can_view_income_allocation(request.user):
        messages.error(request, 'Ni mhasibu au mchungaji tu anaweza kuona report hii.')
        return redirect('donations:home')

    form = IncomeAllocationReportForm(request.GET or None)
    if not form.is_valid():
        messages.error(request, 'Chagua tarehe sahihi kisha generate report kabla ya print.')
        return redirect('donations:income_allocation_report')

    can_view_sadaka = _can_view_sadaka(request.user)
    report = _build_income_allocation_report(
        form.cleaned_data['start_date'],
        form.cleaned_data['end_date'],
        include_sadaka=can_view_sadaka,
    )
    return render(request, 'donations/income_allocation_print.html', church_print_context(
        report=report,
        report_date=timezone.localdate(),
        can_view_sadaka=can_view_sadaka,
    ))

@login_required
def export_donation_history_csv(request):
    base_qs = Donation.objects.select_related('donor', 'campaign').order_by('-donation_date')
    if _can_view_all_donations(request.user):
        qs = base_qs
    else:
        qs = base_qs.filter(donor=request.user)

    response = _csv_response('donation_history_report.csv')
    writer = csv.writer(response)
    writer.writerow(['Date', 'Member', 'Type', 'Amount', 'Payment Method', 'Campaign', 'Status', 'Notes'])
    for donation in qs:
        writer.writerow([
            donation.contribution_date,
            donation.donor.full_name if donation.donor else (donation.donor_name or 'Anonymous'),
            donation.get_donation_type_display(),
            int(donation.amount or 0),
            donation.get_payment_method_display(),
            donation.campaign.title if donation.campaign else 'General',
            donation.get_status_display(),
            donation.notes or '',
        ])
    return response


@login_required
def export_tithe_list_csv(request):
    from members.language_utils import get_translation

    if not _can_view_tithe_list(request.user):
        messages.error(request, 'Ni mhasibu au mchungaji tu anaweza kupakua report ya zaka.')
        return redirect('donations:home')

    lang = LanguageManager.get_current_language(request)
    qs = _tithe_donations_queryset()
    response = _csv_response('tithe_contributions_report.csv')
    writer = csv.writer(response)
    writer.writerow([
        get_translation('table_date', lang),
        get_translation('tithe_col_full_name', lang),
        get_translation('tithe_col_zaka', lang),
        get_translation('tithe_col_other_zaka', lang),
    ])
    for donation in qs:
        writer.writerow([
            donation.contribution_date,
            donation.donor.full_name if donation.donor else (donation.donor_name or ''),
            int(donation.amount or 0) if donation.tithe_gift_type == 'money' else '',
            donation.tithe_asset_description or '',
        ])
    return response


@login_required
def export_accountant_sheet_csv(request):
    if not _is_accountant(request.user):
        messages.error(request, 'Ni mhasibu mwenye access tu anaweza kupakua report hii.')
        return redirect('donations:home')

    rows = _get_accountant_sheet_rows()

    response = _csv_response('accountant_sheet_report.csv')
    writer = csv.writer(response)
    writer.writerow(['Date', 'Sadaka', 'Zaka', 'Malimbuko', 'Shukrani', 'Jumla'])
    for row in rows:
        writer.writerow([
            row['contribution_date'],
            int(row.get('sadaka') or 0),
            int(row.get('zaka') or 0),
            int(row.get('malimbuko') or 0),
            int(row.get('shukrani') or 0),
            int(row.get('jumla') or 0),
        ])
    return response


@login_required
def export_construction_pledges_csv(request):
    if not _is_accountant(request.user):
        messages.error(request, 'Ni mhasibu mwenye access tu anaweza kupakua report ya ujenzi.')
        return redirect('donations:home')

    construction_category = DonationCategory.objects.filter(name__iexact='Ujenzi').first()
    pledges = Pledge.objects.none()
    if construction_category:
        pledges = Pledge.objects.filter(category=construction_category).select_related('donor').order_by('-created_at')

    response = _csv_response('construction_pledges_report.csv')
    writer = csv.writer(response)
    writer.writerow(['Member', 'Ahadi (Hasi)', 'Amount Paid', 'Salio Deni (Hasi)', 'Status', 'Start Date', 'End Date'])
    for pledge in pledges:
        writer.writerow([
            pledge.donor.full_name,
            -int(pledge.total_amount or 0),
            int(pledge.amount_paid or 0),
            pledge.debt_balance_display,
            pledge.get_status_display(),
            pledge.start_date,
            pledge.end_date,
        ])
    return response


@login_required
def export_cash_book_csv(request):
    if not _can_view_cash_book(request.user):
        messages.error(request, 'Ni mhasibu au mchungaji tu anaweza kupakua cash book report.')
        return redirect('donations:home')

    entries = CashBookEntry.objects.select_related('created_by').order_by('-entry_date', '-created_at')
    response = _csv_response('cash_book_report.csv')
    writer = csv.writer(response)
    writer.writerow([
        'Date',
        'Entry Type',
        'Description',
        'Cash Amount',
        'Bank Amount',
        'Cash DR',
        'Bank DR',
        'Cash CR',
        'Bank CR',
        'Created By',
    ])
    for entry in entries:
        cash_amount = int(entry.cash_amount or 0)
        bank_amount = int(entry.bank_amount or 0)
        writer.writerow([
            entry.entry_date,
            entry.get_entry_type_display(),
            entry.description,
            cash_amount,
            bank_amount,
            cash_amount if entry.entry_type == 'dr' else 0,
            bank_amount if entry.entry_type == 'dr' else 0,
            cash_amount if entry.entry_type == 'cr' else 0,
            bank_amount if entry.entry_type == 'cr' else 0,
            entry.created_by.full_name if entry.created_by else '',
        ])
    return response


@login_required
def donation_report_preview(request, report_type):
    report_date = timezone.localdate()
    context = church_print_context(
        report_type=report_type,
        report_date=report_date,
        rows=[],
        columns=[],
    )

    if report_type == 'accountant_sheet':
        if not _is_accountant(request.user):
            messages.error(request, 'Ni mhasibu mwenye access tu anaweza kuona report hii.')
            return redirect('donations:home')
        rows = _get_accountant_sheet_rows()[:300]
        context.update({
            'report_title': 'Report ya Karatasi ya Mhasibu',
            'columns': ['Tarehe', 'Sadaka', 'Zaka', 'Malimbuko', 'Shukrani', 'Jumla'],
            'rows': [{
                'tarehe': r['contribution_date'],
                'sadaka': int(r.get('sadaka') or 0),
                'zaka': int(r.get('zaka') or 0),
                'malimbuko': int(r.get('malimbuko') or 0),
                'shukrani': int(r.get('shukrani') or 0),
                'jumla': int(r.get('jumla') or 0),
            } for r in rows],
        })
    elif report_type == 'construction_pledges':
        if not _is_accountant(request.user):
            messages.error(request, 'Ni mhasibu mwenye access tu anaweza kuona report ya ujenzi.')
            return redirect('donations:home')
        construction_category = DonationCategory.objects.filter(name__iexact='Ujenzi').first()
        pledges = Pledge.objects.none()
        if construction_category:
            pledges = Pledge.objects.filter(category=construction_category).select_related('donor').order_by('-created_at')[:300]
        context.update({
            'report_title': 'Report ya Ahadi za Ujenzi',
            'columns': ['Mwanachama', 'Ahadi (Hasi)', 'Kilicholipwa', 'Salio Deni (Hasi)', 'Hali'],
            'rows': [{
                'mwanachama': p.donor.full_name,
                'ahadi_jumla': -int(p.total_amount or 0),
                'kilicholipwa': int(p.amount_paid or 0),
                'deni': p.debt_balance_display,
                'hali': p.get_status_display(),
            } for p in pledges],
        })
    elif report_type == 'cash_book':
        if not _can_view_cash_book(request.user):
            messages.error(request, 'Ni mhasibu au mchungaji tu anaweza kuona cash book report.')
            return redirect('donations:home')
        return render(request, 'donations/cash_book_print.html', church_print_context(
            sheet_rows=_build_cash_book_sheet_rows(),
            report_date=report_date,
        ))
    else:
        messages.error(request, 'Aina ya report haijatambulika.')
        return redirect('donations:home')

    return render(request, 'donations/report_preview.html', context)

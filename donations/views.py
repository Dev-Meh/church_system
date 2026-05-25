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
from .models import Donation, DonationCampaign, DonationCategory, DonationNotice, CashBookEntry, Pledge
from .print_branding import church_print_context
from .forms import (
    DonationForm,
    AccountantDonationEntryForm,
    DonationNoticeForm,
    AccountantSheetEntryForm,
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

    campaigns = DonationCampaign.objects.filter(status='active').order_by('-created_at')
    categories = DonationCategory.objects.all()
    is_accountant = _is_accountant(request.user)
    is_accountant_role = request.user.role == 'accountant'
    has_accountant_access = bool(getattr(request.user, 'can_post_member_donations', False))
    can_publish_notice = _can_publish_donation_notice(request.user)
    today = timezone.localdate()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create_notice':
            if not can_publish_notice:
                messages.error(request, 'Huna ruhusa ya kutuma taarifa ya michango.')
                return redirect('donations:home')
            notice_form = DonationNoticeForm(request.POST)
            if notice_form.is_valid():
                notice = notice_form.save(commit=False)
                notice.created_by = request.user
                notice.save()
                messages.success(request, 'Taarifa ya mchango imetumwa kikamilifu.')
                return redirect('donations:home')
            donor_scope = _allowed_donor_ids(request.user)
            form = (
                AccountantDonationEntryForm(allowed_donor_ids=donor_scope)
                if is_accountant
                else None
            )
            sheet_form = (
                AccountantSheetEntryForm(allowed_donor_ids=donor_scope)
                if is_accountant
                else None
            )
        else:
            if not is_accountant:
                messages.error(request, 'Ni mhasibu mwenye access tu anaweza kuingiza michango manually.')
                return redirect('donations:home')

            if action == 'sheet_entry':
                if _is_group_only_accountant(request.user):
                    messages.error(
                        request,
                        'Mhasibu wa kundi hutumia ukurasa wa Michango wa Kundi.',
                    )
                    return redirect('donations:home')
                donor_scope = _allowed_donor_ids(request.user)
                sheet_form = AccountantSheetEntryForm(
                    request.POST, allowed_donor_ids=donor_scope
                )
                form = AccountantDonationEntryForm(allowed_donor_ids=donor_scope)
                if sheet_form.is_valid():
                    tithe_donor = sheet_form.cleaned_data.get('donor')
                    construction_donor = sheet_form.cleaned_data.get('construction_donor')
                    contribution_date = sheet_form.cleaned_data['contribution_date']
                    payment_method = sheet_form.cleaned_data['payment_method']
                    notes = sheet_form.cleaned_data.get('notes', '')
                    zaka_type = sheet_form.cleaned_data.get('zaka_type', 'money')
                    aina_nyingine_ya_zaka = (sheet_form.cleaned_data.get('aina_nyingine_ya_zaka') or '').strip()
                    construction_pledge_amount = sheet_form.cleaned_data.get('construction_pledge_amount') or 0
                    construction_payment_amount = sheet_form.cleaned_data.get('construction_payment_amount') or 0
                    type_amount_map = {
                        'offering': sheet_form.cleaned_data.get('sadaka') or 0,
                        'tithe': sheet_form.cleaned_data.get('zaka') or 0 if zaka_type == 'money' else 0,
                        'special': sheet_form.cleaned_data.get('malimbuko') or 0,
                        'other': sheet_form.cleaned_data.get('shukrani') or 0,
                    }
                    for donation_type, amount in type_amount_map.items():
                        if amount and amount > 0:
                            Donation.objects.create(
                                donor=tithe_donor if donation_type == 'tithe' else None,
                                donation_type=donation_type,
                                amount=amount,
                                payment_method=payment_method,
                                notes=notes,
                                donor_name=(
                                    tithe_donor.full_name
                                    if tithe_donor and donation_type == 'tithe'
                                    else 'Michango ya Pamoja'
                                ),
                                contribution_date=contribution_date,
                                status='completed',
                                processed_by=request.user,
                                processed_date=timezone.now(),
                                tithe_gift_type='money' if donation_type == 'tithe' else 'money',
                            )
                    if zaka_type == 'asset':
                        asset_note = f"Zaka ya mali: {aina_nyingine_ya_zaka}"
                        combined_notes = f"{asset_note}. {notes}".strip() if notes else asset_note
                        Donation.objects.create(
                            donor=tithe_donor,
                            donation_type='tithe',
                            amount=0,
                            payment_method=payment_method,
                            notes=combined_notes,
                            contribution_date=contribution_date,
                            status='completed',
                            processed_by=request.user,
                            processed_date=timezone.now(),
                            tithe_gift_type='asset',
                            tithe_asset_description=aina_nyingine_ya_zaka,
                        )

                    if construction_pledge_amount > 0 or construction_payment_amount > 0:
                        construction_category = (
                            DonationCategory.objects.filter(name__iexact='Ujenzi').first()
                            or DonationCategory.objects.create(
                                name='Ujenzi',
                                description='Michango na ahadi za ujenzi',
                                is_active=True,
                            )
                        )
                        pledge = (
                            Pledge.objects.filter(
                                donor=construction_donor,
                                category=construction_category,
                                status__in=['active', 'overdue']
                            )
                            .order_by('-created_at')
                            .first()
                        )

                        if construction_pledge_amount > 0:
                            if pledge:
                                pledge.total_amount = (pledge.total_amount or 0) + construction_pledge_amount
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
                                    notes='Ahadi ya ujenzi imeanzishwa kupitia sheet ya mhasibu.',
                                )

                        if construction_payment_amount > 0:
                            if not pledge:
                                messages.error(
                                    request,
                                    'Mwanachama huyu hana ahadi ya ujenzi. Weka ahadi kwanza au ingiza ahadi mpya kwenye fomu hii.'
                                )
                                return redirect('donations:home')

                            Donation.objects.create(
                                donor=construction_donor,
                                donation_type='special',
                                category=construction_category,
                                amount=construction_payment_amount,
                                payment_method=payment_method,
                                notes=f"Malipo ya deni la ujenzi. {notes}".strip(),
                                donor_name=construction_donor.full_name,
                                contribution_date=contribution_date,
                                status='completed',
                                processed_by=request.user,
                                processed_date=timezone.now(),
                            )

                            pledge.amount_paid = (pledge.amount_paid or 0) + construction_payment_amount
                            if pledge.amount_paid >= pledge.total_amount:
                                pledge.amount_paid = pledge.total_amount
                                pledge.status = 'completed'
                            pledge.save(update_fields=['amount_paid', 'status', 'updated_at'])
                    messages.success(
                        request,
                        f"Mchango umehifadhiwa kwa mafanikio. Jumla: TZS {sheet_form.cleaned_data['jumla']}"
                    )
                    return redirect('donations:home')
            else:
                donor_scope = _allowed_donor_ids(request.user)
                form = AccountantDonationEntryForm(
                    request.POST, allowed_donor_ids=donor_scope
                )
                sheet_form = AccountantSheetEntryForm(allowed_donor_ids=donor_scope)
                if form.is_valid():
                    donation = form.save(commit=False)
                    if donation.donation_type != 'tithe':
                        donation.donor = None
                        donation.donor_name = 'Michango ya Pamoja'
                    elif donation.donor and not donation.donor_name:
                        donation.donor_name = donation.donor.full_name
                    if donor_scope is not None and donation.donor_id:
                        from members.group_permissions import groups_accounted_by
                        donation.recorded_for_group = groups_accounted_by(
                            request.user
                        ).filter(
                            memberships__member_id=donation.donor_id,
                            memberships__is_active=True,
                        ).first() or groups_accounted_by(request.user).first()
                    donation.status = 'completed'
                    donation.processed_by = request.user
                    donation.processed_date = timezone.now()
                    donation.save()
                    messages.success(request, 'Mchango umehifadhiwa kikamilifu.')
                    return redirect('donations:home')
            notice_form = DonationNoticeForm() if can_publish_notice else None
    else:
        donor_scope = _allowed_donor_ids(request.user)
        form = (
            AccountantDonationEntryForm(allowed_donor_ids=donor_scope)
            if is_accountant
            else None
        )
        sheet_form = (
            AccountantSheetEntryForm(allowed_donor_ids=donor_scope)
            if is_accountant
            else None
        )
        notice_form = DonationNoticeForm() if can_publish_notice else None

    # Show active donation notices (all members, or targeted member only).
    active_notices = DonationNotice.objects.filter(
        is_active=True,
        start_date__lte=today,
        end_date__gte=today,
    ).filter(
        Q(target_member__isnull=True) | Q(target_member=request.user)
    ).select_related('created_by', 'target_member').order_by('-created_at')

    my_donations = Donation.objects.filter(donor=request.user)
    totals = my_donations.values('donation_type').annotate(total=models.Sum('amount'))
    totals_map = {item['donation_type']: item['total'] or 0 for item in totals}
    accountant_sheet_rows = []
    construction_pledges = []
    if is_accountant:
        accountant_sheet_rows = _get_accountant_sheet_rows()[:20]
        construction_category = DonationCategory.objects.filter(name__iexact='Ujenzi').first()
        if construction_category:
            construction_pledges = (
                Pledge.objects.filter(category=construction_category)
                .select_related('donor')
                .order_by('-created_at')[:30]
            )

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
        'form': form,
        'sheet_form': sheet_form,
        'is_accountant': is_accountant,
        'is_accountant_role': is_accountant_role,
        'has_accountant_access': has_accountant_access,
        'can_publish_notice': can_publish_notice,
        'notice_form': notice_form,
        'active_notices': active_notices,
        'total_all': my_donations.aggregate(total=models.Sum('amount'))['total'] or 0,
        'total_tithe': totals_map.get('tithe', 0),
        'total_offering': totals_map.get('offering', 0),
        'total_special': totals_map.get('special', 0),
        'total_other': totals_map.get('other', 0),
        'recent_my_donations': my_donations.order_by('-contribution_date', '-donation_date')[:10],
        'show_management_graphs': request.user.role in {'pastor', 'accountant'},
        'donation_chart_labels': json.dumps(donation_chart_labels),
        'donation_chart_data': json.dumps(donation_chart_data),
        'registration_chart_labels': json.dumps(registration_chart_labels),
        'registration_chart_data': json.dumps(registration_chart_data),
        'accountant_sheet_rows': accountant_sheet_rows,
        'construction_pledges': construction_pledges,
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
            return donations_queryset_for_user(self.request.user, base_qs)
        return base_qs.filter(donor=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        by_type = qs.values('donation_type').annotate(total=models.Sum('amount'))
        totals_map = {item['donation_type']: item['total'] or 0 for item in by_type}
        context['total_tithe'] = totals_map.get('tithe', 0)
        context['total_offering'] = totals_map.get('offering', 0)
        context['total_special'] = totals_map.get('special', 0)
        context['total_other'] = totals_map.get('other', 0)
        context['total_all'] = qs.aggregate(total=models.Sum('amount'))['total'] or 0
        context['can_view_all_donations'] = _can_view_all_donations(self.request.user)
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


def _build_income_allocation_report(start_date, end_date):
    period_qs = Donation.objects.filter(
        contribution_date__range=(start_date, end_date),
        status='completed',
    )

    total_zaka = period_qs.filter(donation_type='tithe').aggregate(total=models.Sum('amount'))['total'] or 0
    total_sadaka = period_qs.filter(donation_type='offering').aggregate(total=models.Sum('amount'))['total'] or 0
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

    if form.is_valid():
        report = _build_income_allocation_report(
            form.cleaned_data['start_date'],
            form.cleaned_data['end_date'],
        )

    return render(request, 'donations/income_allocation_report.html', {
        'form': form,
        'report': report,
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

    report = _build_income_allocation_report(
        form.cleaned_data['start_date'],
        form.cleaned_data['end_date'],
    )
    return render(request, 'donations/income_allocation_print.html', church_print_context(
        report=report,
        report_date=timezone.localdate(),
    ))

@login_required
def financial_status(request):
    """View church financial status (for all members)"""
    total_donations = Donation.objects.aggregate(
        total=models.Sum('amount')
    )['total'] or 0
    
    recent_donations = Donation.objects.order_by('-donation_date')[:10]
    campaign_stats = []
    
    campaigns = DonationCampaign.objects.filter(status='active')
    for campaign in campaigns:
        total = Donation.objects.filter(campaign=campaign).aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        progress_percentage = 0
        if campaign.target_amount and campaign.target_amount > 0:
            progress_percentage = float((total / campaign.target_amount) * 100)
        campaign_stats.append({
            'campaign': campaign,
            'total': total,
            'donors': Donation.objects.filter(campaign=campaign).count(),
            'progress_percentage': progress_percentage,
        })
    
    return render(request, 'donations/financial_status.html', {
        'total_donations': total_donations,
        'recent_donations': recent_donations,
        'campaign_stats': campaign_stats
    })


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
    if not _can_view_tithe_list(request.user):
        messages.error(request, 'Ni mhasibu au mchungaji tu anaweza kupakua report ya zaka.')
        return redirect('donations:home')

    qs = _tithe_donations_queryset()
    response = _csv_response('tithe_contributions_report.csv')
    writer = csv.writer(response)
    writer.writerow(['Date', 'Member', 'Tithe Type', 'Amount', 'Asset Description', 'Notes'])
    for donation in qs:
        writer.writerow([
            donation.contribution_date,
            donation.donor.full_name if donation.donor else (donation.donor_name or ''),
            'Mali' if donation.tithe_gift_type == 'asset' else 'Fedha',
            int(donation.amount or 0),
            donation.tithe_asset_description or '',
            donation.notes or '',
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
    writer.writerow(['Member', 'Total Pledge', 'Amount Paid', 'Remaining Debt', 'Status', 'Start Date', 'End Date'])
    for pledge in pledges:
        writer.writerow([
            pledge.donor.full_name,
            int(pledge.total_amount or 0),
            int(pledge.amount_paid or 0),
            int(pledge.remaining_amount or 0),
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
            'columns': ['Mwanachama', 'Ahadi Jumla', 'Kilicholipwa', 'Deni Lililobaki', 'Hali'],
            'rows': [{
                'mwanachama': p.donor.full_name,
                'ahadi_jumla': int(p.total_amount or 0),
                'kilicholipwa': int(p.amount_paid or 0),
                'deni': int(p.remaining_amount or 0),
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

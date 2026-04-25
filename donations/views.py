from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.utils import timezone
from .models import Donation, DonationCampaign, DonationCategory
from .forms import DonationForm, AccountantDonationEntryForm


def _is_accountant(user):
    return user.role == 'accountant' and bool(getattr(user, 'can_post_member_donations', False))

@login_required
def donation_home(request):
    """Donation page: manual entry for accountant, summary for member."""
    campaigns = DonationCampaign.objects.filter(status='active').order_by('-created_at')
    categories = DonationCategory.objects.all()
    is_accountant = _is_accountant(request.user)
    is_accountant_role = request.user.role == 'accountant'
    has_accountant_access = bool(getattr(request.user, 'can_post_member_donations', False))

    if request.method == 'POST':
        if not is_accountant:
            messages.error(request, 'Ni mhasibu tu anaweza kuingiza michango manually.')
            return redirect('donations:home')

        form = AccountantDonationEntryForm(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.status = 'completed'
            donation.processed_by = request.user
            donation.processed_date = timezone.now()
            donation.save()
            messages.success(request, 'Mchango umehifadhiwa kikamilifu.')
            return redirect('donations:home')
    else:
        form = AccountantDonationEntryForm() if is_accountant else None

    my_donations = Donation.objects.filter(donor=request.user)
    totals = my_donations.values('donation_type').annotate(total=models.Sum('amount'))
    totals_map = {item['donation_type']: item['total'] or 0 for item in totals}

    context = {
        'campaigns': campaigns,
        'categories': categories,
        'form': form,
        'is_accountant': is_accountant,
        'is_accountant_role': is_accountant_role,
        'has_accountant_access': has_accountant_access,
        'total_all': my_donations.aggregate(total=models.Sum('amount'))['total'] or 0,
        'total_tithe': totals_map.get('tithe', 0),
        'total_offering': totals_map.get('offering', 0),
        'total_special': totals_map.get('special', 0),
        'total_other': totals_map.get('other', 0),
        'recent_my_donations': my_donations.order_by('-contribution_date', '-donation_date')[:10],
    }
    return render(request, 'donations/donation_home.html', context)

@login_required
def make_donation(request, campaign_id=None):
    """Public donate endpoint disabled: donations are entered by accountant."""
    messages.info(request, 'Michango inaingizwa na mhasibu baada ya kupokea malipo.')
    return redirect('donations:home')

class DonationHistoryView(LoginRequiredMixin, ListView):
    """View donation history for the logged-in user"""
    model = Donation
    template_name = 'donations/donation_history.html'
    context_object_name = 'donations'
    paginate_by = 10
    
    def get_queryset(self):
        return Donation.objects.filter(donor=self.request.user).order_by('-donation_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = Donation.objects.filter(donor=self.request.user)
        by_type = qs.values('donation_type').annotate(total=models.Sum('amount'))
        totals_map = {item['donation_type']: item['total'] or 0 for item in by_type}
        context['total_tithe'] = totals_map.get('tithe', 0)
        context['total_offering'] = totals_map.get('offering', 0)
        context['total_special'] = totals_map.get('special', 0)
        context['total_other'] = totals_map.get('other', 0)
        context['total_all'] = qs.aggregate(total=models.Sum('amount'))['total'] or 0
        return context

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

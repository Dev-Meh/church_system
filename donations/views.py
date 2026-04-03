from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from .models import Donation, DonationCampaign, DonationCategory
from .forms import DonationForm

@login_required
def donation_home(request):
    """Main donation page with campaigns and donation form"""
    campaigns = DonationCampaign.objects.filter(status='active').order_by('-created_at')
    categories = DonationCategory.objects.all()
    
    if request.method == 'POST':
        form = DonationForm(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.donor = request.user
            donation.save()
            messages.success(request, 'Thank you for your generous donation!')
            return redirect('donations:home')
    else:
        form = DonationForm()
    
    return render(request, 'donations/donation_home.html', {
        'campaigns': campaigns,
        'categories': categories,
        'form': form
    })

@login_required
def make_donation(request, campaign_id=None):
    """Make a donation to a specific campaign or general donation"""
    campaign = None
    if campaign_id:
        campaign = get_object_or_404(DonationCampaign, id=campaign_id, status='active')
    
    if request.method == 'POST':
        form = DonationForm(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.donor = request.user
            donation.campaign = campaign
            donation.save()
            
            if campaign:
                messages.success(request, f'Thank you for donating to "{campaign.title}"!')
            else:
                messages.success(request, 'Thank you for your generous donation!')
            
            return redirect('donations:home')
    else:
        initial_data = {}
        if campaign:
            initial_data['campaign'] = campaign
        form = DonationForm(initial=initial_data)
    
    return render(request, 'donations/make_donation.html', {
        'form': form,
        'campaign': campaign
    })

class DonationHistoryView(LoginRequiredMixin, ListView):
    """View donation history for the logged-in user"""
    model = Donation
    template_name = 'donations/donation_history.html'
    context_object_name = 'donations'
    paginate_by = 10
    
    def get_queryset(self):
        return Donation.objects.filter(donor=self.request.user).order_by('-donation_date')

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
        campaign_stats.append({
            'campaign': campaign,
            'total': total,
            'donors': Donation.objects.filter(campaign=campaign).count()
        })
    
    return render(request, 'donations/financial_status.html', {
        'total_donations': total_donations,
        'recent_donations': recent_donations,
        'campaign_stats': campaign_stats
    })

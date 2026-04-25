from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.http import JsonResponse
import json
from .models import ChurchUser
from donations.models import Donation, DonationCampaign
from .models_message import MessageRecipient
from events.models import Event
from sermons.models import Sermon
from prayers.models import PrayerRequest

@login_required(login_url='members:login')
def dashboard(request):
    """Role-based dashboard that adapts to user role"""
    user = request.user
    
    if user.role == 'pastor':
        return pastor_dashboard(request)
    else:
        return member_dashboard(request)

def pastor_dashboard(request):
    """Pastor-specific dashboard with member and donation oversight"""
    user = request.user
    
    # Member statistics
    total_members = ChurchUser.objects.filter(role='member').count()
    active_members = ChurchUser.objects.filter(role='member', is_active_member=True).count()
    new_members_this_month = ChurchUser.objects.filter(
        role='member',
        date_joined__month=timezone.now().month,
        date_joined__year=timezone.now().year
    ).count()
    
    # Donation statistics
    total_donations = Donation.objects.aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    donations_this_month = Donation.objects.filter(
        donation_date__month=timezone.now().month,
        donation_date__year=timezone.now().year
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    recent_donations = Donation.objects.select_related('donor', 'campaign').order_by('-donation_date')[:10]
    
    # Campaign statistics
    active_campaigns = DonationCampaign.objects.filter(status='active').count()
    campaign_stats = []
    for campaign in DonationCampaign.objects.filter(status='active')[:5]:
        total = Donation.objects.filter(campaign=campaign).aggregate(
            total=Sum('amount')
        )['total'] or 0
        donors = Donation.objects.filter(campaign=campaign).count()
        campaign_stats.append({
            'campaign': campaign,
            'total': total,
            'donors': donors
        })
    
    # Recent members
    recent_members = ChurchUser.objects.filter(
        role='member'
    ).order_by('-date_joined')[:10]
    
    # Recent messages sent by pastor
    recent_messages = MessageRecipient.objects.filter(
        message__sender=user
    ).select_related('message').order_by('-message__created_at')[:10]

    accountant_users = ChurchUser.objects.filter(role='accountant').order_by('first_name', 'last_name')
    
    # Prepare data for JSON serialization
    dashboard_data = {
        'total_members': total_members,
        'active_members': active_members,
        'new_members_this_month': new_members_this_month,
        'total_donations': float(total_donations),
        'donations_this_month': float(donations_this_month),
        'recent_messages': [
            {
                'title': msg.message.title,
                'sender': msg.message.sender.get_full_name(),
                'date': msg.message.created_at.strftime('%Y-%m-%d %H:%M'),
                'recipients': msg.message.recipient_count
            }
            for msg in recent_messages
        ],
        'recent_members': [
            {
                'first_name': member.first_name,
                'last_name': member.last_name,
                'email': member.email,
                'joined': member.date_joined.strftime('%Y-%m-%d'),
                'status': 'active' if member.is_active_member else 'inactive'
            }
            for member in recent_members
        ],
        'recent_donations': [
            {
                'donor': donation.donor.get_full_name() if donation.donor else 'Anonymous',
                'campaign': donation.campaign.title if donation.campaign else 'General Fund',
                'amount': float(donation.amount),
                'date': donation.donation_date.strftime('%Y-%m-%d %H:%M')
            }
            for donation in recent_donations
        ],
        'campaign_stats': [
            {
                'title': stat.campaign.title,
                'description': stat.campaign.description,
                'raised': float(stat.total),
                'goal': float(stat.campaign.target_amount),
                'donors': stat.donors
            }
            for stat in campaign_stats
        ]
    }
    
    context = {
        'user': user,
        'total_members': total_members,
        'active_members': active_members,
        'new_members_this_month': new_members_this_month,
        'total_donations': total_donations,
        'donations_this_month': donations_this_month,
        'recent_donations': recent_donations,
        'active_campaigns': active_campaigns,
        'campaign_stats': campaign_stats,
        'recent_members': recent_members,
        'recent_messages': recent_messages,
        'accountant_users': accountant_users,
        'dashboard_data': json.dumps(dashboard_data),
        'is_pastor': True,
    }
    
    return render(request, 'members/pastor_dashboard.html', context)

def member_dashboard(request):
    """Member-specific dashboard"""
    user = request.user
    
    # User's donation history
    user_donations = Donation.objects.filter(donor=user).order_by('-donation_date')[:5]
    total_user_donations = Donation.objects.filter(donor=user).aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Available campaigns
    available_campaigns = DonationCampaign.objects.filter(status='active').order_by('-created_at')[:5]
    
    # Unread messages count
    unread_messages_count = MessageRecipient.objects.filter(
        recipient=user,
        is_read=False
    ).count()
    
    # Recent messages for this member
    member_messages = MessageRecipient.objects.filter(
        recipient=user
    ).select_related('message', 'message__sender').order_by('-message__created_at')[:5]

    # Left navigation counters
    nav_events_count = Event.objects.filter(is_published=True).count()
    nav_sermons_count = Sermon.objects.filter(is_published=True).count()
    nav_prayers_count = PrayerRequest.objects.filter(
        visibility__in=['public', 'leadership']
    ).exclude(status='closed').count()
    nav_messages_count = MessageRecipient.objects.filter(recipient=user).count()
    
    context = {
        'user': user,
        'user_donations': user_donations,
        'total_user_donations': total_user_donations,
        'available_campaigns': available_campaigns,
        'unread_messages_count': unread_messages_count,
        'member_messages': member_messages,
        'nav_events_count': nav_events_count,
        'nav_sermons_count': nav_sermons_count,
        'nav_prayers_count': nav_prayers_count,
        'nav_messages_count': nav_messages_count,
        'is_pastor': False,
    }
    
    return render(request, 'members/member_dashboard.html', context)

class MemberListView(LoginRequiredMixin, ListView):
    """Pastor-only view to see all members"""
    model = ChurchUser
    template_name = 'members/member_list.html'
    context_object_name = 'members'
    paginate_by = 20
    login_url = '/members/login/'
    
    def get_queryset(self):
        # Show church members and accountants so pastor can manage donation access
        return ChurchUser.objects.filter(
            role__in=['member', 'accountant']
        ).order_by('role', '-date_joined')
    
    def dispatch(self, request, *args, **kwargs):
        # Only allow pastors to access this view
        if not request.user.role == 'pastor':
            from django.contrib import messages
            messages.error(request, 'Access denied. Pastor privileges required.')
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

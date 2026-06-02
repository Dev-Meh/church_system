from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.db.models import Count, Sum, Q
from django.db.models.functions import Concat
from django.db.models import Value, CharField
from django.utils import timezone
from django.http import JsonResponse
from django.db.models.functions import TruncMonth
from datetime import timedelta
import json
from .models import ChurchUser, UniversityStudentRecord
from donations.models import Donation, DonationCampaign
from .models_message import MessageRecipient
from .message_queries import member_inbox_queryset, church_inbox_unread_count
from .permissions import (
    can_manage_church_communications,
    can_create_church_announcements,
    can_manage_members,
    can_promote_to_pastor,
    can_promote_to_admin,
    has_church_leadership,
    is_verified_pastor,
)
from events.models import Event
from sermons.models import Sermon
from prayers.models import PrayerRequest

@login_required
def dashboard(request):
    """Role-based dashboard that adapts to user role"""
    user = request.user

    if getattr(user, 'is_app_admin', False) or user.role == 'admin':
        return pastor_dashboard(request)

    if user.role == 'pastor':
        if is_verified_pastor(user):
            return pastor_dashboard(request)
        messages.warning(
            request,
            'Akaunti yako ya mchungaji inasubiri uthibitisho. Wasiliana na msimamizi wa kanisa.',
        )
        return member_dashboard(request)

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
    secretary_users = ChurchUser.objects.filter(role='secretary').order_by('first_name', 'last_name')
    university_students_studying = UniversityStudentRecord.objects.filter(
        status='studying'
    ).count()
    university_students_alumni = UniversityStudentRecord.objects.filter(
        status='completed'
    ).count()
    
    # Donation trend (last 6 months)
    six_months_ago = timezone.now().date() - timedelta(days=180)
    donation_monthly = (
        Donation.objects.filter(contribution_date__gte=six_months_ago)
        .annotate(month=TruncMonth('contribution_date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )
    donation_chart_labels = [item['month'].strftime('%b %Y') for item in donation_monthly if item['month']]
    donation_chart_data = [float(item['total'] or 0) for item in donation_monthly]

    # Member registration trend (last 6 months)
    registration_monthly = (
        ChurchUser.objects.filter(role='member', date_joined__date__gte=six_months_ago)
        .annotate(month=TruncMonth('date_joined'))
        .values('month')
        .annotate(total=Count('id'))
        .order_by('month')
    )
    registration_chart_labels = [item['month'].strftime('%b %Y') for item in registration_monthly if item['month']]
    registration_chart_data = [int(item['total'] or 0) for item in registration_monthly]

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
        ],
        'donation_chart_labels': donation_chart_labels,
        'donation_chart_data': donation_chart_data,
        'registration_chart_labels': registration_chart_labels,
        'registration_chart_data': registration_chart_data,
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
        'secretary_users': secretary_users,
        'dashboard_data': json.dumps(dashboard_data),
        'is_pastor': True,
        'donation_chart_labels': json.dumps(donation_chart_labels),
        'donation_chart_data': json.dumps(donation_chart_data),
        'registration_chart_labels': json.dumps(registration_chart_labels),
        'registration_chart_data': json.dumps(registration_chart_data),
        'university_students_studying': university_students_studying,
        'university_students_alumni': university_students_alumni,
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
    
    # Ujumbe wa kanisa zima tu (si matangazo ya idara)
    unread_messages_count = church_inbox_unread_count(user)

    member_messages = member_inbox_queryset(user, group=None)[:5]

    # Left navigation counters
    nav_events_count = Event.objects.filter(is_published=True).count()
    nav_sermons_count = Sermon.objects.filter(is_published=True).count()
    nav_prayers_count = PrayerRequest.objects.filter(
        visibility__in=['public', 'leadership']
    ).exclude(status='closed').count()
    nav_messages_count = member_inbox_queryset(user, group=None).count()

    # Member personal donation trend (last 6 months)
    six_months_ago = timezone.now().date() - timedelta(days=180)
    my_monthly_donations = (
        Donation.objects.filter(donor=user, contribution_date__gte=six_months_ago)
        .annotate(month=TruncMonth('contribution_date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )
    member_donation_chart_labels = [item['month'].strftime('%b %Y') for item in my_monthly_donations if item['month']]
    member_donation_chart_data = [float(item['total'] or 0) for item in my_monthly_donations]

    sent_messages_count = 0
    if can_manage_church_communications(user):
        from .models_message import Message
        sent_messages_count = Message.objects.filter(sender=user).count()

    pastor_pending_verification = (
        user.role == 'pastor' and not bool(getattr(user, 'is_verified_pastor', False))
    )

    context = {
        'user': user,
        'pastor_pending_verification': pastor_pending_verification,
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
        'can_manage_communications': can_manage_church_communications(user),
        'can_create_announcements': can_create_church_announcements(user),
        'sent_messages_count': sent_messages_count,
        'member_donation_chart_labels': json.dumps(member_donation_chart_labels),
        'member_donation_chart_data': json.dumps(member_donation_chart_data),
    }
    
    return render(request, 'members/member_dashboard.html', context)

class MemberListView(LoginRequiredMixin, ListView):
    """Pastor/admin: list, search, and manage members."""
    model = ChurchUser
    template_name = 'members/member_list.html'
    context_object_name = 'members'
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not can_manage_members(request.user):
            from django.contrib import messages
            messages.error(request, 'Ni mchungaji tu anaweza kusimamia wanachama.')
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = ChurchUser.objects.filter(
            role__in=['member', 'accountant', 'secretary', 'pastor']
        )

        q = (self.request.GET.get('q') or '').strip()
        role = (self.request.GET.get('role') or '').strip()
        status = (self.request.GET.get('status') or '').strip()

        if q:
            qs = qs.annotate(
                full_name_search=Concat(
                    'first_name', Value(' '), 'last_name',
                    output_field=CharField(),
                )
            ).filter(
                Q(full_name_search__icontains=q)
                | Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(username__icontains=q)
                | Q(email__icontains=q)
                | Q(phone_number__icontains=q)
            )

        if role in ('member', 'accountant', 'secretary', 'pastor'):
            qs = qs.filter(role=role)

        if status == 'active':
            qs = qs.filter(is_active=True, is_active_member=True)
        elif status == 'inactive':
            qs = qs.filter(Q(is_active=False) | Q(is_active_member=False))

        return qs.order_by('role', 'first_name', 'last_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_q'] = (self.request.GET.get('q') or '').strip()
        context['filter_role'] = (self.request.GET.get('role') or '').strip()
        context['filter_status'] = (self.request.GET.get('status') or '').strip()
        context['role_choices'] = [
            ('', 'Roles zote'),
            ('member', 'Member'),
            ('pastor', 'Mchungaji'),
            ('secretary', 'Katibu'),
            ('accountant', 'Accountant'),
        ]
        context['can_promote_pastor'] = can_promote_to_pastor(self.request.user)
        context['can_promote_admin'] = can_promote_to_admin(self.request.user)
        context['has_leadership'] = has_church_leadership(self.request.user)
        context['status_choices'] = [
            ('', 'Hali zote'),
            ('active', 'Hai (active)'),
            ('inactive', 'Imesimamishwa'),
        ]
        return context

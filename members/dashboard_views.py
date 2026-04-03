from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.contrib import messages
from .models import ChurchUser
from .models_message import Message, MessageRecipient, Announcement
from .forms import MessageForm, AnnouncementForm
from .sms_service import sms_service
from donations.models import Donation, DonationCampaign
from .language_utils import LanguageManager

@login_required(login_url='members:login')
def dashboard(request):
    """Main dashboard view - redirects to role-based dashboard"""
    user = request.user
    
    print(f"DEBUG: Dashboard view - Session language: {request.session.get('django_language', 'NOT_SET')}")
    print(f"DEBUG: Dashboard view - User role: {user.role}")
    
    if user.is_authenticated:
        if user.role == 'pastor':
            return pastor_dashboard(request)
        else:
            return member_dashboard(request)
    else:
        # Show public dashboard for non-logged-in users
        return public_dashboard(request)

def pastor_dashboard(request):
    """Pastor-specific dashboard with member and donation oversight"""
    user = request.user
    
    # Member statistics with debug output
    all_members = ChurchUser.objects.filter(role='member')
    total_members = all_members.count()
    print(f"DEBUG: Total members query: {all_members.query}")
    print(f"DEBUG: Total members count: {total_members}")
    
    active_members_query = ChurchUser.objects.filter(role='member', is_active_member=True)
    active_members = active_members_query.count()
    print(f"DEBUG: Active members query: {active_members_query.query}")
    print(f"DEBUG: Active members count: {active_members}")
    
    # Fix: Use membership_date instead of date_joined
    new_members_query = ChurchUser.objects.filter(
        role='member',
        membership_date__month=timezone.now().month,
        membership_date__year=timezone.now().year
    )
    new_members_this_month = new_members_query.count()
    print(f"DEBUG: New members this month query: {new_members_query.query}")
    print(f"DEBUG: New members this month count: {new_members_this_month}")
    
    # Show all member data for debugging
    print(f"DEBUG: All member records:")
    for member in ChurchUser.objects.filter(role='member')[:5]:  # Show first 5
        print(f"  - {member.first_name} {member.last_name} (active: {member.is_active_member}, joined: {member.membership_date})")
    
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
    
    # Active members
    active_members_list = ChurchUser.objects.filter(
        role='member',
        is_active_member=True
    ).order_by('-date_joined')[:10]
    
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
        'active_members_list': active_members_list,
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
    
    context = {
        'user': user,
        'user_donations': user_donations,
        'total_user_donations': total_user_donations,
        'available_campaigns': available_campaigns,
        'is_pastor': False,
    }
    
    return render(request, 'members/member_dashboard.html', context)

def public_dashboard(request):
    """Public dashboard for non-logged-in users"""
    # Public statistics - show general church information
    total_members = ChurchUser.objects.filter(role='member').count()
    active_campaigns = DonationCampaign.objects.filter(status='active').count()
    
    # Show some public campaigns without sensitive data
    available_campaigns = DonationCampaign.objects.filter(status='active').order_by('-created_at')[:3]
    
    context = {
        'total_members': total_members,
        'active_campaigns': active_campaigns,
        'available_campaigns': available_campaigns,
        'is_public': True,
    }
    
    return render(request, 'members/public_dashboard.html', context)

class MemberListView(LoginRequiredMixin, ListView):
    """Pastor-only view to see all members"""
    model = ChurchUser
    template_name = 'members/member_list.html'
    context_object_name = 'members'
    paginate_by = 20
    login_url = '/members/login/'
    
    def get_queryset(self):
        # Only show active members, not pastors or admins
        return ChurchUser.objects.filter(role='member', is_active_member=True).order_by('-date_joined')
    
    def dispatch(self, request, *args, **kwargs):
        # Only allow pastors to access this view
        if not request.user.role == 'pastor':
            from django.contrib import messages
            messages.error(request, 'Access denied. Pastor privileges required.')
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

@login_required
def create_message(request):
    """Create a new message for church members (pastor only)"""
    print(f"DEBUG: create_message view called")
    print(f"DEBUG: create_message - Session language: {request.session.get('django_language', 'NOT_SET')}")
    
    if request.user.role not in ['pastor', 'admin', 'elder']:
        messages.error(request, 'Access denied. Pastor privileges required.')
        return redirect('dashboard')
    
    # TEMPORARY: Use simple test template to bypass all complex logic
    current_language = request.session.get('django_language', 'en')
    print(f"DEBUG: create_message - Using SIMPLE TEST template for language: {current_language}")
    
    context = {
        'debug_language': current_language,
        'debug_template': 'members/simple_message_test.html'
    }
    
    return render(request, 'members/simple_message_test.html', context)

@login_required
def create_announcement(request):
    """Create a new announcement (pastor only)"""
    if request.user.role not in ['pastor', 'admin', 'elder']:
        messages.error(request, 'Access denied. Pastor privileges required.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.author = request.user
            announcement.save()
            
            messages.success(request, 'Announcement created successfully!')
            return redirect('dashboard')
    else:
        form = AnnouncementForm()
    
    return render(request, 'members/create_announcement.html', {'form': form})

@login_required
def member_messages(request):
    """View messages received by the current member"""
    # Get messages for the current user
    messages = MessageRecipient.objects.filter(
        recipient=request.user
    ).select_related('message', 'message__sender').order_by('-message__created_at')
    
    current_language = LanguageManager.get_current_language(request)
    template_name = 'members/member_messages_sw.html' if current_language == 'sw' else 'members/member_messages.html'
    
    context = {
        'messages': messages,
        'user': request.user,
    }
    
    return render(request, template_name, context)

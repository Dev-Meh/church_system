from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_POST
from django.http import HttpResponseRedirect
from django.conf import settings
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import check_for_language
from .dashboard_views import dashboard as role_based_dashboard
from .forms import (
    ChurchUserRegistrationForm,
    ChurchUserUpdateForm,
    ChurchUserLoginForm,
    ChurchGroupForm,
    GroupActivityForm,
)
from .models import ChurchUser, ChurchGroup, GroupMembership
from .language_utils import LanguageManager

class CustomLoginView(LoginView):
    template_name = 'auth/unified_auth.html'
    redirect_authenticated_user = True   # 👈 already logged in → go to dashboard
    authentication_form = ChurchUserLoginForm
    
    def get_success_url(self):
        return reverse_lazy('dashboard')
    
    def form_invalid(self, form):
        messages.error(self.request, 'Invalid username or password. Please try again.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['login_form'] = self.get_form()
        context['form'] = ChurchUserRegistrationForm()  # Add registration form for template
        context['auth_mode'] = 'login'
        return context

@require_POST  # 👈 logout only works with POST, not GET
def custom_logout(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('members:login')

class RegisterView(CreateView):
    model = ChurchUser
    form_class = ChurchUserRegistrationForm
    template_name = 'auth/unified_auth.html'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse_lazy('members:login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Registration successful! Please log in with your new account.')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['login_form'] = ChurchUserLoginForm()  # Add login form for template
        context['auth_mode'] = 'register'
        return context

class ProfileView(LoginRequiredMixin, DetailView):
    login_url = '/members/login/'
    model = ChurchUser
    template_name = 'members/profile.html'
    context_object_name = 'member'
    
    def get_object(self):
        return self.request.user

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    login_url = '/members/login/'
    model = ChurchUser
    form_class = ChurchUserUpdateForm
    template_name = 'members/profile_edit.html'
    success_url = reverse_lazy('profile')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)

@login_required(login_url='members:login')
def dashboard(request):
    return role_based_dashboard(request)

def set_language_view(request, language_code):
    """Set language preference (cookie + session) and redirect back."""
    from .language_utils import get_translation

    next_url = request.META.get('HTTP_REFERER') or reverse('dashboard')
    if not url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = reverse('dashboard')

    response = HttpResponseRedirect(next_url)

    if not check_for_language(language_code):
        err = get_translation('error', 'en')
        messages.error(request, f'{err}: Invalid language selection')
        return response

    if LanguageManager.set_language(request, language_code):
        language_info = LanguageManager.get_language_info(language_code)
        success_msg = get_translation('success', language_code)
        messages.success(request, f'{language_info["native_name"]} — {success_msg}')
        response.set_cookie(
            settings.LANGUAGE_COOKIE_NAME,
            language_code,
            max_age=settings.LANGUAGE_COOKIE_AGE,
            path=settings.LANGUAGE_COOKIE_PATH,
            domain=settings.LANGUAGE_COOKIE_DOMAIN,
            secure=settings.LANGUAGE_COOKIE_SECURE,
            httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
            samesite=settings.LANGUAGE_COOKIE_SAMESITE,
        )
    else:
        error_msg = get_translation('error', language_code)
        messages.error(request, f'{error_msg}: Invalid language selection')

    return response

def test_language_view(request):
    """Test view for language functionality"""
    current_language = request.session.get('django_language', 'en')
    print(f"DEBUG: test_language_view - Session language: {current_language}")
    
    # Use simple test template
    template_name = 'members/simple_test.html'
    print(f"DEBUG: test_language_view - Using template: {template_name}")
    
    return render(request, template_name)

def home(request):
    """Home page - redirect to login if not authenticated, dashboard if authenticated"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    else:
        return redirect('members:login')


@login_required(login_url='members:login')
@require_POST
def toggle_accountant_access(request, user_id):
    """Pastor/Admin can grant or revoke donation posting access."""
    if request.user.role not in ['pastor', 'admin']:
        messages.error(request, 'Huna ruhusa ya kubadilisha access ya uingizaji michango.')
        return redirect('dashboard')

    target_user = get_object_or_404(ChurchUser, id=user_id, role='accountant')
    target_user.can_post_member_donations = not target_user.can_post_member_donations
    target_user.save(update_fields=['can_post_member_donations'])

    if target_user.can_post_member_donations:
        messages.success(request, f'Access ya kuingiza michango imetolewa kwa {target_user.full_name}.')
    else:
        messages.warning(request, f'Access ya kuingiza michango imeondolewa kwa {target_user.full_name}.')

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('dashboard')))


@login_required(login_url='members:login')
@require_POST
def promote_to_accountant(request, user_id):
    """Pastor/Admin can promote member to accountant role."""
    if request.user.role not in ['pastor', 'admin']:
        messages.error(request, 'Huna ruhusa ya kubadilisha role ya mtumiaji.')
        return redirect('dashboard')

    member_user = get_object_or_404(ChurchUser, id=user_id)
    if member_user.role not in ['member', 'accountant']:
        messages.error(request, 'Ni member tu anaweza kubadilishwa kuwa accountant.')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('members:member_list')))

    member_user.role = 'accountant'
    member_user.can_post_member_donations = True
    member_user.save(update_fields=['role', 'can_post_member_donations'])
    messages.success(request, f'{member_user.full_name} sasa ni accountant mwenye access ya kuchapisha michango.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('members:member_list')))


def _can_manage_group(request, group):
    if request.user.role in ["pastor", "admin"]:
        return True
    return GroupMembership.objects.filter(
        group=group, member=request.user, role__in=["leader", "assistant"], is_active=True
    ).exists()


@login_required(login_url='members:login')
def group_list(request):
    groups = ChurchGroup.objects.filter(is_active=True).select_related("leader")
    if request.user.role not in ["pastor", "admin"]:
        groups = groups.filter(
            memberships__member=request.user, memberships__is_active=True
        ).distinct()
    return render(request, "members/group_list.html", {"groups": groups})


@login_required(login_url='members:login')
def group_detail(request, pk):
    group = get_object_or_404(ChurchGroup.objects.select_related("leader"), pk=pk, is_active=True)

    # only group members (or pastor/admin) can access
    if request.user.role not in ["pastor", "admin"] and not GroupMembership.objects.filter(
        group=group, member=request.user, is_active=True
    ).exists():
        messages.error(request, "Huruhusiwi kuona kundi hili.")
        return redirect("members:group_list")

    memberships = group.memberships.select_related("member").filter(is_active=True)
    activities = group.activities.select_related("created_by").all()[:20]

    available_members = ChurchUser.objects.filter(is_active=True).exclude(
        id__in=memberships.values_list("member_id", flat=True)
    )
    can_manage = _can_manage_group(request, group)

    context = {
        "group": group,
        "memberships": memberships,
        "activities": activities,
        "available_members": available_members,
        "can_manage": can_manage,
        "activity_form": GroupActivityForm(),
    }
    return render(request, "members/group_detail.html", context)


@login_required(login_url='members:login')
def group_create(request):
    if request.user.role not in ["pastor", "admin"]:
        messages.error(request, "Ni pastor/admin tu anaweza kuunda kundi.")
        return redirect("members:group_list")

    if request.method == "POST":
        form = ChurchGroupForm(request.POST)
        if form.is_valid():
            group = form.save()
            if group.leader:
                GroupMembership.objects.get_or_create(
                    group=group,
                    member=group.leader,
                    defaults={"role": "leader", "is_active": True},
                )
            messages.success(request, "Kundi limeundwa kikamilifu.")
            return redirect("members:group_detail", pk=group.pk)
    else:
        form = ChurchGroupForm()

    return render(request, "members/group_form.html", {"form": form})


@login_required(login_url='members:login')
@require_POST
def group_add_member(request, pk):
    group = get_object_or_404(ChurchGroup, pk=pk, is_active=True)
    if not _can_manage_group(request, group):
        messages.error(request, "Huna ruhusa ya kuongeza wanachama kwenye kundi hili.")
        return redirect("members:group_detail", pk=pk)

    member_id = request.POST.get("member_id")
    role = request.POST.get("role", "member")
    member = get_object_or_404(ChurchUser, pk=member_id)

    membership, created = GroupMembership.objects.get_or_create(
        group=group,
        member=member,
        defaults={"role": role, "is_active": True},
    )
    if not created:
        membership.role = role
        membership.is_active = True
        membership.save()

    if role == "leader" and group.leader_id != member.id:
        group.leader = member
        group.save(update_fields=["leader"])

    messages.success(request, "Mwanachama ameongezwa kwenye kundi.")
    return redirect("members:group_detail", pk=pk)


@login_required(login_url='members:login')
@require_POST
def group_add_activity(request, pk):
    group = get_object_or_404(ChurchGroup, pk=pk, is_active=True)
    if not _can_manage_group(request, group):
        messages.error(request, "Huna ruhusa ya kuweka shughuli za kundi hili.")
        return redirect("members:group_detail", pk=pk)

    form = GroupActivityForm(request.POST)
    if form.is_valid():
        activity = form.save(commit=False)
        activity.group = group
        activity.created_by = request.user
        activity.save()
        messages.success(request, "Shughuli ya kundi imehifadhiwa.")
    else:
        messages.error(request, "Imeshindikana kuhifadhi shughuli. Hakikisha umejaza vizuri.")

    return redirect("members:group_detail", pk=pk)

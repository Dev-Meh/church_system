from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_POST
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.db.models import Count, Q, Sum
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
    PastorSetPasswordForm,
    ChurchPasswordResetForm,
)
from .models import ChurchUser, ChurchGroup, GroupMembership
from .group_permissions import (
    can_access_group,
    can_assign_group_officers,
    can_manage_group_activities,
    can_manage_group_donations,
    can_manage_group_members,
    can_send_group_messages,
    can_view_group_members,
    groups_visible_to_user,
    is_group_mwenyekiti,
    is_group_plain_member,
)
from .group_services import assign_group_officer, get_group_member_ids
from .models_message import Message, MessageRecipient
from donations.models import Donation
from donations.forms import GroupMchangoEntryForm
from .language_utils import LanguageManager
from django.utils import timezone
from .permissions import (
    can_appoint_secretary,
    can_manage_members,
    can_manage_church_groups,
    can_promote_to_pastor,
    can_promote_to_admin,
    has_church_leadership,
)

def csrf_failure(request, reason=''):
    """Generic CSRF error — usionyeshe maelezo ya kiufundi."""
    return TemplateResponse(
        request,
        'registration/csrf_failure.html',
        status=403,
    )


class CustomLoginView(LoginView):
    template_name = 'auth/unified_auth.html'
    redirect_authenticated_user = True   # 👈 already logged in → go to dashboard
    authentication_form = ChurchUserLoginForm

    def dispatch(self, request, *args, **kwargs):
        from .security import is_rate_limited, rate_limit_message

        blocked, retry = is_rate_limited('login', request)
        if blocked:
            messages.error(request, rate_limit_message('login', retry))
            return self.render_to_response(self.get_context_data())
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('dashboard')

    def form_valid(self, form):
        from .security import clear_rate_limit

        clear_rate_limit('login', self.request, form.cleaned_data.get('username'))
        return super().form_valid(form)

    def form_invalid(self, form):
        from .security import is_rate_limited, rate_limit_message, record_rate_limit_failure

        username = (self.request.POST.get('username') or '').strip()
        record_rate_limit_failure('login', self.request, username)
        blocked, retry = is_rate_limited('login', self.request, username)
        if blocked:
            messages.error(self.request, rate_limit_message('login', retry))
        else:
            messages.error(
                self.request,
                'Jina la mtumiaji au nenosiri si sahihi. Jaribu tena.',
            )
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['login_form'] = self.get_form()
        context['form'] = ChurchUserRegistrationForm()  # Add registration form for template
        context['auth_mode'] = 'login'
        return context

def custom_logout(request):
    from .middleware import add_private_no_cache_headers

    request.session.pop('django_language', None)
    logout(request)
    response = redirect('members:login')
    response.delete_cookie(settings.LANGUAGE_COOKIE_NAME)
    add_private_no_cache_headers(response)
    messages.success(request, 'You have been successfully logged out.')
    return response

class RegisterView(CreateView):
    model = ChurchUser
    form_class = ChurchUserRegistrationForm
    template_name = 'auth/unified_auth.html'

    def dispatch(self, request, *args, **kwargs):
        from .security import is_rate_limited, rate_limit_message, record_rate_limit_failure

        if request.user.is_authenticated:
            return redirect('dashboard')
        if request.method == 'POST':
            blocked, retry = is_rate_limited('register', request)
            if blocked:
                messages.error(request, rate_limit_message('register', retry))
                return redirect('members:login')
        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        from .security import record_rate_limit_failure

        record_rate_limit_failure('register', self.request)
        return super().form_invalid(form)
    
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
        user = self.get_object()
        uploaded = self.request.FILES.get('profile_picture')
        old_picture = user.profile_picture if user.profile_picture else None
        response = super().form_valid(form)
        if uploaded:
            if old_picture and old_picture.name != form.instance.profile_picture.name:
                old_picture.delete(save=False)
            messages.success(self.request, 'Profile photo saved successfully.')
        else:
            messages.success(self.request, 'Profile updated successfully!')
        return response

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
    """Home: onyesha fomu ya kuingia kwenye URL fupi ('/'), au dashibodi ikiwa ameingia."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return CustomLoginView.as_view()(request)


@login_required(login_url='members:login')
@require_POST
def toggle_accountant_access(request, user_id):
    """Pastor/Admin can grant or revoke donation posting access."""
    if not has_church_leadership(request.user):
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
    if not has_church_leadership(request.user):
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


@login_required(login_url='members:login')
@require_POST
def promote_to_secretary(request, user_id):
    """Pastor/Admin can appoint a member as church secretary."""
    if not can_appoint_secretary(request.user):
        messages.error(request, 'Huna ruhusa ya kuteua katibu.')
        return redirect('dashboard')

    member_user = get_object_or_404(ChurchUser, id=user_id)
    if member_user.role != 'member':
        messages.error(request, 'Ni member tu anaweza kuteuliwa kuwa katibu.')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('members:member_list')))

    member_user.role = 'secretary'
    member_user.can_post_member_donations = False
    member_user.save(update_fields=['role', 'can_post_member_donations'])
    messages.success(
        request,
        f'{member_user.full_name} sasa ni katibu wa kanisa — anaweza kutuma ujumbe, matangazo na taarifa za michango.',
    )
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('members:member_list')))


@login_required(login_url='members:login')
@require_POST
def demote_from_secretary(request, user_id):
    """Pastor/Admin can remove secretary role."""
    if not can_appoint_secretary(request.user):
        messages.error(request, 'Huna ruhusa ya kuondoa katibu.')
        return redirect('dashboard')

    secretary_user = get_object_or_404(ChurchUser, id=user_id, role='secretary')
    secretary_user.role = 'member'
    secretary_user.save(update_fields=['role'])
    messages.success(request, f'{secretary_user.full_name} sasa ni member wa kawaida.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('members:member_list')))


@login_required(login_url='members:login')
@require_POST
def promote_to_pastor(request, user_id):
    """Admin or verified pastor appoints a member as verified pastor."""
    if not can_promote_to_pastor(request.user):
        messages.error(request, 'Huna ruhusa ya kuteua mchungaji.')
        return redirect('dashboard')

    member_user = get_object_or_404(ChurchUser, id=user_id, role='member')
    member_user.role = 'pastor'
    member_user.is_staff = True
    member_user.is_verified_pastor = True
    member_user.pastor_verification_date = timezone.now()
    member_user.save(
        update_fields=['role', 'is_staff', 'is_verified_pastor', 'pastor_verification_date']
    )
    messages.success(
        request,
        f'{member_user.full_name} sasa ni mchungaji aliyethibitishwa.',
    )
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('members:member_list')))


@login_required(login_url='members:login')
@require_POST
def demote_from_pastor(request, user_id):
    """Admin or verified pastor removes pastor role."""
    if not can_promote_to_pastor(request.user):
        messages.error(request, 'Huna ruhusa ya kuondoa cheo cha mchungaji.')
        return redirect('dashboard')

    pastor_user = get_object_or_404(ChurchUser, id=user_id, role='pastor')
    if pastor_user.pk == request.user.pk:
        messages.error(request, 'Huwezi kuondoa cheo chako mwenyewe.')
        return redirect('members:member_list')

    pastor_user.role = 'member'
    pastor_user.is_staff = False
    pastor_user.is_verified_pastor = False
    pastor_user.pastor_verification_date = None
    pastor_user.save(
        update_fields=['role', 'is_staff', 'is_verified_pastor', 'pastor_verification_date']
    )
    messages.success(request, f'{pastor_user.full_name} sasa ni member wa kawaida.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('members:member_list')))


@login_required(login_url='members:login')
@require_POST
def promote_to_admin(request, user_id):
    """Church admin grants administrator role (not via public registration)."""
    if not can_promote_to_admin(request.user):
        messages.error(request, 'Ni msimamizi wa kanisa tu anaweza kuteua admin.')
        return redirect('dashboard')

    member_user = get_object_or_404(ChurchUser, id=user_id, role='member')
    member_user.role = 'admin'
    member_user.is_staff = True
    member_user.is_verified_pastor = False
    member_user.save(update_fields=['role', 'is_staff', 'is_verified_pastor'])
    messages.success(
        request,
        f'{member_user.full_name} sasa ni msimamizi (administrator) wa mfumo.',
    )
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('members:member_list')))


@login_required(login_url='members:login')
@require_POST
def toggle_member_active(request, user_id):
    """Pastor/admin: activate or deactivate member login and membership."""
    if not can_manage_members(request.user):
        messages.error(request, 'Huna ruhusa.')
        return redirect('dashboard')

    target = get_object_or_404(
        ChurchUser, id=user_id, role__in=['member', 'accountant', 'secretary', 'pastor']
    )
    if target.pk == request.user.pk:
        messages.error(request, 'Huwezi kusimamisha akaunti yako mwenyewe.')
        return redirect('members:member_list')

    if target.is_active and target.is_active_member:
        target.is_active = False
        target.is_active_member = False
        target.save(update_fields=['is_active', 'is_active_member'])
        messages.warning(request, f'Akaunti ya {target.full_name} imesimamishwa — hawawezi kuingia.')
    else:
        target.is_active = True
        target.is_active_member = True
        target.save(update_fields=['is_active', 'is_active_member'])
        messages.success(request, f'Akaunti ya {target.full_name} imewashwa tena.')

    return _redirect_member_list(request)


def _redirect_member_list(request):
    referer = request.META.get('HTTP_REFERER', '')
    if referer and url_has_allowed_host_and_scheme(
        referer,
        allowed_hosts={request.get_host()},
    ):
        return redirect(referer)
    return redirect('members:member_list')


@login_required(login_url='members:login')
def admin_reset_password(request, user_id):
    """Pastor/admin: set password or email reset link for a member."""
    if not can_manage_members(request.user):
        messages.error(request, 'Huna ruhusa.')
        return redirect('dashboard')

    target = get_object_or_404(
        ChurchUser, id=user_id, role__in=['member', 'accountant', 'secretary', 'pastor']
    )

    if request.method == 'POST':
        action = request.POST.get('action', 'set_password')

        if action == 'send_email':
            if not target.email:
                messages.error(request, f'{target.full_name} hana barua pepe kwenye akaunti.')
            else:
                form = ChurchPasswordResetForm({'email': target.email})
                if form.is_valid():
                    form.save(
                        request=request,
                        use_https=request.is_secure(),
                        email_template_name='registration/password_reset_email.html',
                        subject_template_name='registration/password_reset_subject.txt',
                    )
                    messages.success(
                        request,
                        f'Kiungo cha kubadili nenosiri kimetumwa kwa {target.email}.',
                    )
                else:
                    messages.error(request, 'Imeshindikana kutuma barua pepe.')
            return _redirect_member_list(request)

        form = PastorSetPasswordForm(target, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Nenosiri jipya limewekwa kwa {target.full_name}.')
            return _redirect_member_list(request)
    else:
        form = PastorSetPasswordForm(target)

    return render(
        request,
        'members/admin_reset_password.html',
        {'form': form, 'target_user': target},
    )


class ChurchPasswordResetView(PasswordResetView):
    form_class = ChurchPasswordResetForm
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('members:password_reset_done')

    def post(self, request, *args, **kwargs):
        from .security import (
            is_rate_limited,
            rate_limit_message,
            record_rate_limit_failure,
        )

        blocked, retry = is_rate_limited('password_reset', request)
        if blocked:
            messages.error(request, rate_limit_message('password_reset', retry))
            return redirect('members:password_reset')
        record_rate_limit_failure('password_reset', request)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        form.save(
            request=self.request,
            use_https=self.request.is_secure(),
            domain_override=self.request.get_host(),
        )
        return redirect(self.success_url)


class ChurchPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'


class ChurchPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('members:password_reset_complete')


class ChurchPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'


@login_required(login_url='members:login')
def group_list(request):
    can_create = can_manage_church_groups(request.user)
    if can_create:
        from .group_services import ensure_default_church_groups

        created = ensure_default_church_groups()
        if created:
            messages.success(
                request,
                f"Makundi {created} ya msingi yameundwa (Vijana na/au Akina Mama). "
                "Endesha sync wanachama kutoka server ikiwa unahitaji, au hifadhi wasifu wa mwanachama.",
            )

    groups = (
        groups_visible_to_user(request.user)
        .select_related("leader", "secretary", "accountant")
        .annotate(
            member_count=Count(
                "memberships",
                filter=Q(memberships__is_active=True),
            )
        )
    )
    return render(
        request,
        "members/group_list.html",
        {
            "groups": groups,
            "can_create_groups": can_create,
        },
    )


@login_required(login_url='members:login')
def group_detail(request, pk):
    group = get_object_or_404(
        ChurchGroup.objects.select_related("leader", "secretary", "accountant"),
        pk=pk,
        is_active=True,
    )

    if not can_access_group(request.user, group):
        messages.error(request, "Huruhusiwi kuona kundi hili.")
        return redirect("members:group_list")

    can_view_members = can_view_group_members(request.user, group)
    can_manage = can_manage_group_members(request.user, group)
    can_manage_activities = can_manage_group_activities(request.user, group)

    memberships = []
    available_members = ChurchUser.objects.none()
    if can_view_members:
        memberships = group.memberships.select_related("member").filter(is_active=True)
        if can_manage:
            available_members = ChurchUser.objects.filter(is_active=True).exclude(
                id__in=memberships.values_list("member_id", flat=True)
            )

    activities = group.activities.select_related("created_by").all()[:20]

    group_matangazo = (
        Message.objects.filter(
            church_group=group,
            is_active=True,
        )
        .select_related("sender")
        .order_by("-created_at")[:15]
    )

    officer_candidates = ChurchUser.objects.none()
    if can_assign_group_officers(request.user):
        officer_candidates = ChurchUser.objects.filter(is_active=True).order_by(
            "first_name", "last_name"
        )

    context = {
        "group": group,
        "memberships": memberships,
        "activities": activities,
        "available_members": available_members,
        "officer_candidates": officer_candidates,
        "can_manage": can_manage,
        "can_manage_activities": can_manage_activities,
        "can_view_members": can_view_members,
        "is_mwenyekiti": is_group_mwenyekiti(request.user, group),
        "can_assign_officers": can_assign_group_officers(request.user),
        "can_manage_donations": can_manage_group_donations(request.user, group),
        "can_send_messages": can_send_group_messages(request.user, group),
        "is_plain_member": is_group_plain_member(request.user, group),
        "group_matangazo": group_matangazo,
        "activity_form": GroupActivityForm(),
    }
    return render(request, "members/group_detail.html", context)


@login_required(login_url='members:login')
def group_create(request):
    if not can_manage_church_groups(request.user):
        messages.error(request, "Ni mchungaji, admin, au katibu tu anaweza kuunda kundi.")
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
def group_assign_officers(request, pk):
    """Mchungaji huweka kiongozi, katibu, na mhasibu wa kundi."""
    group = get_object_or_404(ChurchGroup, pk=pk, is_active=True)
    if not can_assign_group_officers(request.user):
        messages.error(request, "Ni mchungaji/admin tu anaweza kuteua viongozi wa kundi.")
        return redirect("members:group_detail", pk=pk)

    for role in ("leader", "secretary", "accountant"):
        raw_id = request.POST.get(f"{role}_id", "").strip()
        if raw_id:
            member = get_object_or_404(ChurchUser, pk=raw_id, is_active=True)
            assign_group_officer(group, role, member)
        else:
            assign_group_officer(group, role, None)

    messages.success(request, "Mwenyekiti, katibu na mhasibu wamesasishwa.")
    return redirect("members:group_detail", pk=pk)


@login_required(login_url='members:login')
def group_donations(request, pk):
    """Mhasibu wa kundi: ingiza na ona michango ya wanachama wa kundi tu."""
    group = get_object_or_404(
        ChurchGroup.objects.select_related("accountant"),
        pk=pk,
        is_active=True,
    )
    if not can_manage_group_donations(request.user, group):
        messages.error(request, "Huna ruhusa ya kusimamia michango ya idara hii.")
        return redirect("members:group_detail", pk=pk)

    member_ids = get_group_member_ids(group)
    donations = (
        Donation.objects.filter(
            recorded_for_group=group,
            donor_id__in=member_ids,
            status="completed",
        )
        .select_related("donor")
        .order_by("-contribution_date", "-donation_date")[:50]
    )

    if request.method == "POST":
        form = GroupMchangoEntryForm(
            request.POST,
            allowed_donor_ids=member_ids,
        )
        if form.is_valid():
            donation = form.save(commit=False)
            if not donation.donor_id or donation.donor_id not in member_ids:
                messages.error(request, "Chagua mwanachama wa kundi hili.")
            else:
                donation.donor_name = donation.donor.full_name
                donation.donation_type = "other"
                donation.recorded_for_group = group
                donation.status = "completed"
                donation.processed_by = request.user
                donation.processed_date = timezone.now()
                donation.save()
                messages.success(request, "Mchango umeandikwa — mwanachama ataona kwenye wasifu wake.")
                return redirect("members:group_donations", pk=pk)
    else:
        form = GroupMchangoEntryForm(allowed_donor_ids=member_ids)

    total_michango = donations.aggregate(total=Sum("amount"))["total"] or 0

    return render(
        request,
        "members/group_donations.html",
        {
            "group": group,
            "form": form,
            "donations": donations,
            "total_michango": total_michango,
            "member_count": len(member_ids),
        },
    )


@login_required(login_url="members:login")
def group_my_donations(request, pk):
    """Mwanachama: michango yake pekee kwenye idara hii."""
    group = get_object_or_404(ChurchGroup, pk=pk, is_active=True)
    if not can_access_group(request.user, group):
        messages.error(request, "Huruhusiwi kuona idara hili.")
        return redirect("members:group_list")

    donations = (
        Donation.objects.filter(
            donor=request.user,
            recorded_for_group=group,
            status="completed",
        )
        .order_by("-contribution_date", "-donation_date")
    )

    return render(
        request,
        "members/group_my_donations.html",
        {
            "group": group,
            "donations": donations,
            "has_michango": donations.exists(),
        },
    )


@login_required(login_url='members:login')
@require_POST
def group_add_member(request, pk):
    group = get_object_or_404(ChurchGroup, pk=pk, is_active=True)
    if not can_manage_group_members(request.user, group):
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

    if role == "leader":
        assign_group_officer(group, "leader", member)
    elif role == "secretary":
        assign_group_officer(group, "secretary", member)
    elif role == "accountant":
        assign_group_officer(group, "accountant", member)

    messages.success(request, "Mwanachama ameongezwa kwenye kundi.")
    return redirect("members:group_detail", pk=pk)


@login_required(login_url='members:login')
@require_POST
def group_add_activity(request, pk):
    group = get_object_or_404(ChurchGroup, pk=pk, is_active=True)
    if not can_manage_group_activities(request.user, group):
        messages.error(request, "Ni mwenyekiti, katibu, au mchungaji tu anaweza kuweka shughuli za idara.")
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

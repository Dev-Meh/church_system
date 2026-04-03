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
from .forms import ChurchUserRegistrationForm, ChurchUserUpdateForm, ChurchUserLoginForm
from .models import ChurchUser
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

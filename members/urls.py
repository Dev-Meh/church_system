from django.urls import path
from . import views
from .dashboard_views import MemberListView, create_message, create_announcement, member_messages
from .views import ProfileView
from .language_utils import LanguageManager

app_name = 'members'

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('members/', MemberListView.as_view(), name='member_list'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    
    # Language switching
    path('language/<str:language_code>/', views.set_language_view, name='set_language'),
    
    # Test language functionality
    path('test-language/', views.test_language_view, name='test_language'),
    
    # Message URLs
    path('messages/create/', create_message, name='message_create'),
    path('announcements/create/', create_announcement, name='announcement_create'),
    path('messages/my/', member_messages, name='member_messages'),
]

from django.urls import path
from . import views
from .dashboard_views import MemberListView, create_announcement
from .message_views import MessageCreateView, member_messages, MessageListView, MessageDetailView
from .views import ProfileView

app_name = 'members'

urlpatterns = [
    # ... (existing urls)
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
    path('messages/center/', views.dashboard, name='message_center'), # Redirect to dashboard or dedicated center
    path('messages/create/', MessageCreateView.as_view(), name='message_create'),
    path('messages/list/', MessageListView.as_view(), name='message_list'),
    path('messages/<int:pk>/', MessageDetailView.as_view(), name='message_detail'),
    path('announcements/create/', create_announcement, name='announcement_create'),
    path('messages/my/', member_messages, name='member_messages'),
]

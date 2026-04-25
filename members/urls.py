from django.urls import path
from . import views
from .dashboard_views import MemberListView
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
    path('messages/my/', member_messages, name='member_messages'),
    path('groups/', views.group_list, name='group_list'),
    path('groups/create/', views.group_create, name='group_create'),
    path('groups/<int:pk>/', views.group_detail, name='group_detail'),
    path('groups/<int:pk>/add-member/', views.group_add_member, name='group_add_member'),
    path('groups/<int:pk>/add-activity/', views.group_add_activity, name='group_add_activity'),
    path('accountants/<int:user_id>/toggle-access/', views.toggle_accountant_access, name='toggle_accountant_access'),
    path('accountants/<int:user_id>/promote/', views.promote_to_accountant, name='promote_to_accountant'),
]

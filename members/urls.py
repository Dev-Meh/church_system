from django.urls import path
from . import views
from .dashboard_views import MemberListView
from .message_views import (
    MessageCreateView,
    member_messages,
    MessageListView,
    MessageDetailView,
    AnnouncementCreateView,
    message_center,
)
from .views import (
    ProfileView,
    ChurchPasswordResetView,
    ChurchPasswordResetDoneView,
    ChurchPasswordResetConfirmView,
    ChurchPasswordResetCompleteView,
)

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
    path('messages/center/', message_center, name='message_center'),
    path('messages/create/', MessageCreateView.as_view(), name='message_create'),
    path('messages/list/', MessageListView.as_view(), name='message_list'),
    path('messages/<int:pk>/', MessageDetailView.as_view(), name='message_detail'),
    path('messages/my/', member_messages, name='member_messages'),
    path('announcements/create/', AnnouncementCreateView.as_view(), name='announcement_create'),
    path('groups/', views.group_list, name='group_list'),
    path('groups/create/', views.group_create, name='group_create'),
    path('groups/<int:pk>/', views.group_detail, name='group_detail'),
    path('groups/<int:pk>/add-member/', views.group_add_member, name='group_add_member'),
    path('groups/<int:pk>/add-activity/', views.group_add_activity, name='group_add_activity'),
    path('accountants/<int:user_id>/toggle-access/', views.toggle_accountant_access, name='toggle_accountant_access'),
    path('accountants/<int:user_id>/promote/', views.promote_to_accountant, name='promote_to_accountant'),
    path('pastors/<int:user_id>/promote/', views.promote_to_pastor, name='promote_to_pastor'),
    path('pastors/<int:user_id>/demote/', views.demote_from_pastor, name='demote_from_pastor'),
    path('admins/<int:user_id>/promote/', views.promote_to_admin, name='promote_to_admin'),
    path('secretaries/<int:user_id>/promote/', views.promote_to_secretary, name='promote_to_secretary'),
    path('secretaries/<int:user_id>/demote/', views.demote_from_secretary, name='demote_from_secretary'),
    path('members/<int:user_id>/toggle-active/', views.toggle_member_active, name='toggle_member_active'),
    path('members/<int:user_id>/reset-password/', views.admin_reset_password, name='admin_reset_password'),
    path('password-reset/', ChurchPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', ChurchPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', ChurchPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', ChurchPasswordResetCompleteView.as_view(), name='password_reset_complete'),
]

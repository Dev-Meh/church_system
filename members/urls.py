from django.conf import settings
from django.urls import path
from django.views.generic import RedirectView
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
from .group_message_views import group_broadcast
from .university_student_views import (
    university_student_list,
    university_student_print,
    university_student_create,
    university_student_edit,
    university_student_detail,
    university_student_mark_completed,
)
from .views import (
    ProfileView,
    public_password_reset_disabled,
    ChurchPasswordResetConfirmView,
    ChurchPasswordResetCompleteView,
)

app_name = 'members'

urlpatterns = [
    # ... (existing urls)
    path(
        'login/',
        RedirectView.as_view(url=settings.LOGIN_URL, permanent=True),
    ),
    path('logout/', views.custom_logout, name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('members/', MemberListView.as_view(), name='member_list'),
    path('university-students/', university_student_list, name='university_student_list'),
    path('university-students/print/', university_student_print, name='university_student_print'),
    path('university-students/new/', university_student_create, name='university_student_create'),
    path('university-students/<int:pk>/', university_student_detail, name='university_student_detail'),
    path('university-students/<int:pk>/edit/', university_student_edit, name='university_student_edit'),
    path('university-students/<int:pk>/complete/', university_student_mark_completed, name='university_student_mark_completed'),
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
    path('groups/<int:pk>/officers/', views.group_assign_officers, name='group_assign_officers'),
    path('groups/<int:pk>/donations/', views.group_donations, name='group_donations'),
    path('groups/<int:pk>/my-donations/', views.group_my_donations, name='group_my_donations'),
    path('groups/<int:pk>/matangazo/', group_broadcast, name='group_broadcast'),
    path('accountants/<int:user_id>/toggle-access/', views.toggle_accountant_access, name='toggle_accountant_access'),
    path('accountants/<int:user_id>/promote/', views.promote_to_accountant, name='promote_to_accountant'),
    path('pastors/<int:user_id>/approve/', views.approve_pastor, name='approve_pastor'),
    path('pastors/<int:user_id>/promote/', views.promote_to_pastor, name='promote_to_pastor'),
    path('pastors/<int:user_id>/demote/', views.demote_from_pastor, name='demote_from_pastor'),
    path('admins/<int:user_id>/promote/', views.promote_to_admin, name='promote_to_admin'),
    path('secretaries/<int:user_id>/promote/', views.promote_to_secretary, name='promote_to_secretary'),
    path('secretaries/<int:user_id>/demote/', views.demote_from_secretary, name='demote_from_secretary'),
    path('members/<int:user_id>/approve/', views.approve_member, name='approve_member'),
    path('members/<int:user_id>/toggle-active/', views.toggle_member_active, name='toggle_member_active'),
    path('members/<int:user_id>/reset-password/', views.admin_reset_password, name='admin_reset_password'),
    path('password-reset/', views.public_password_reset_disabled, name='password_reset'),
    path('password-reset/done/', views.public_password_reset_disabled, name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', ChurchPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', ChurchPasswordResetCompleteView.as_view(), name='password_reset_complete'),
]

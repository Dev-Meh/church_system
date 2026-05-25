"""
URL configuration for church_management project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from members.views import home, dashboard, ProfileView, ProfileUpdateView
from members.university_student_views import (
    university_student_list,
    university_student_create,
    university_student_detail,
    university_student_edit,
    university_student_mark_completed,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),              # visits / → goes to login
    path('dashboard/', dashboard, name='dashboard'),
    # Wanafunzi wa chuo (majina ya URL bila namespace — pamoja na members:...)
    path('university-students/', university_student_list, name='university_student_list'),
    path('university-students/new/', university_student_create, name='university_student_create'),
    path('university-students/<int:pk>/', university_student_detail, name='university_student_detail'),
    path('university-students/<int:pk>/edit/', university_student_edit, name='university_student_edit'),
    path(
        'university-students/<int:pk>/complete/',
        university_student_mark_completed,
        name='university_student_mark_completed',
    ),
    path('members/', include('members.urls')),
    path('player/', include('members.urls_player')),  # Player URLs
    path('events/', include('events.urls')),
    path('sermons/', include('sermons.urls')),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/edit/', ProfileUpdateView.as_view(), name='profile_edit'),
    path('donations/', include('donations.urls')),
    path('api/', include('members.api_urls')),  # NEW: API endpoints
]

if settings.DEBUG or getattr(settings, 'SERVE_MEDIA_FILES', False):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
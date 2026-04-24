"""
URL configuration for church_management project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from members.views import home, dashboard, ProfileView, ProfileUpdateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),              # visits / → goes to login
    path('dashboard/', dashboard, name='dashboard'),
    path('members/', include('members.urls')),
    path('player/', include('members.urls_player')),  # Player URLs
    path('events/', include('events.urls')),
    path('sermons/', include('sermons.urls')),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/edit/', ProfileUpdateView.as_view(), name='profile_edit'),
    path('donations/', include('donations.urls')),
    path('api/', include('members.api_urls')),  # NEW: API endpoints
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import ChurchUserViewSet

router = DefaultRouter()
router.register(r'users', ChurchUserViewSet, basename='churchuser')

app_name = 'members_api'

urlpatterns = [
    path('', include(router.urls)),
]

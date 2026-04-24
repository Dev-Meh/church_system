from django.urls import path
from . import views_player

app_name = 'player'

urlpatterns = [
    path('dashboard/', views_player.PlayerDashboardView.as_view(), name='dashboard'),
]

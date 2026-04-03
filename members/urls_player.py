from django.urls import path
from . import views_player

app_name = 'player'

urlpatterns = [
    # Player Dashboard
    path('dashboard/', views_player.PlayerDashboardView.as_view(), name='dashboard'),
    
    # Media Player
    path('play/<str:content_type>/<int:content_id>/', views_player.media_player, name='media_player'),
    
    # My Content
    path('my-content/', views_player.my_content, name='my_content'),
]

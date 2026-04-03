from django.urls import path
from . import views

app_name = 'sermons'

urlpatterns = [
    # Sermon Views
    path('', views.SermonListView.as_view(), name='sermon_list'),
    path('<int:pk>/', views.SermonDetailView.as_view(), name='sermon_detail'),
    path('create/', views.SermonCreateView.as_view(), name='sermon_create'),
    path('<int:pk>/edit/', views.SermonUpdateView.as_view(), name='sermon_update'),
    path('<int:pk>/delete/', views.SermonDeleteView.as_view(), name='sermon_delete'),
    
    # Sermon Series
    path('series/', views.SermonSeriesListView.as_view(), name='series_list'),
    path('series/create/', views.SermonSeriesCreateView.as_view(), name='series_create'),
    path('series/<int:pk>/edit/', views.SermonSeriesUpdateView.as_view(), name='series_update'),
    path('series/<int:pk>/delete/', views.SermonSeriesDeleteView.as_view(), name='series_delete'),
    
    # Interactive Features
    path('<int:sermon_id>/bookmark/', views.add_bookmark, name='add_bookmark'),
    path('<int:sermon_id>/note/', views.add_note, name='add_note'),
    
    # Pastor Dashboard
    path('dashboard/', views.sermon_dashboard, name='dashboard'),
]

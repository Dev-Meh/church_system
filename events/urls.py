from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    # Event Views
    path('', views.EventListView.as_view(), name='event_list'),
    path('<int:pk>/', views.EventDetailView.as_view(), name='event_detail'),
    path('create/', views.EventCreateView.as_view(), name='event_create'),
    path('<int:pk>/edit/', views.EventUpdateView.as_view(), name='event_update'),
    path('<int:pk>/delete/', views.EventDeleteView.as_view(), name='event_delete'),
    
    # Event Registration
    path('<int:event_id>/register/', views.register_for_event, name='register'),
    path('<int:event_id>/cancel/', views.cancel_registration, name='cancel_registration'),
    
    # Event Resources
    path('<int:event_id>/resource/add/', views.EventResourceCreateView.as_view(), name='add_resource'),
    
    # Pastor Dashboard
    path('dashboard/', views.event_dashboard, name='dashboard'),
]

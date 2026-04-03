from django.urls import path
from . import views

app_name = 'donations'

urlpatterns = [
    path('', views.donation_home, name='home'),
    path('donate/', views.make_donation, name='donate'),
    path('donate/<int:campaign_id>/', views.make_donation, name='donate_to_campaign'),
    path('history/', views.DonationHistoryView.as_view(), name='history'),
    path('financial-status/', views.financial_status, name='financial_status'),
]

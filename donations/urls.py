from django.urls import path
from . import views

app_name = 'donations'

urlpatterns = [
    path('', views.donation_home, name='home'),
    path('donate/', views.make_donation, name='donate'),
    path('donate/<int:campaign_id>/', views.make_donation, name='donate_to_campaign'),
    path('history/', views.DonationHistoryView.as_view(), name='history'),
    path('history/export/', views.export_donation_history_csv, name='export_history_csv'),
    path('tithe-list/', views.TitheContributionListView.as_view(), name='tithe_list'),
    path('tithe-list/print/', views.tithe_list_print, name='tithe_list_print'),
    path('tithe-list/export/', views.export_tithe_list_csv, name='export_tithe_csv'),
    path('malimbuko-list/', views.MalimbukoContributionListView.as_view(), name='malimbuko_list'),
    path('malimbuko-list/print/', views.malimbuko_list_print, name='malimbuko_list_print'),
    path('malimbuko-list/export/', views.export_malimbuko_list_csv, name='export_malimbuko_csv'),
    path('sadaka-list/', views.OfferingContributionListView.as_view(), name='offering_list'),
    path('sadaka-list/print/', views.offering_list_print, name='offering_list_print'),
    path('sadaka-list/export/', views.export_offering_csv, name='export_offering_csv'),
    path('shukrani-list/', views.ShukraniContributionListView.as_view(), name='shukrani_list'),
    path('shukrani-list/print/', views.shukrani_list_print, name='shukrani_list_print'),
    path('shukrani-list/export/', views.export_shukrani_csv, name='export_shukrani_csv'),
    path('ahadi-list/', views.ConstructionPledgeListView.as_view(), name='pledge_list'),
    path('ahadi-list/print/', views.pledge_list_print, name='pledge_list_print'),
    path('cash-book/', views.cash_book_view, name='cash_book'),
    path('cash-book/export/', views.export_cash_book_csv, name='export_cash_book_csv'),
    path('income-allocation-report/', views.income_allocation_report_view, name='income_allocation_report'),
    path('income-allocation-report/print/', views.income_allocation_report_print, name='income_allocation_print'),
    path('reports/accountant-sheet/export/', views.export_accountant_sheet_csv, name='export_accountant_sheet_csv'),
    path('reports/construction-pledges/export/', views.export_construction_pledges_csv, name='export_construction_pledges_csv'),
    path('reports/preview/<str:report_type>/', views.donation_report_preview, name='report_preview'),
]

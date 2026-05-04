from django.contrib import admin

from .models import Donation, DonationCampaign, DonationCategory, CashBookEntry


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'donor',
        'donation_type',
        'tithe_gift_type',
        'tithe_asset_description',
        'amount',
        'payment_method',
        'status',
        'contribution_date',
        'processed_by',
    )
    list_filter = ('donation_type', 'status', 'payment_method', 'contribution_date')
    search_fields = ('donor__username', 'donor_name', 'notes', 'transaction_id')


@admin.register(DonationCampaign)
class DonationCampaignAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'target_amount', 'current_amount', 'start_date', 'end_date')
    list_filter = ('status', 'start_date', 'end_date')
    search_fields = ('title', 'description')


@admin.register(DonationCategory)
class DonationCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(CashBookEntry)
class CashBookEntryAdmin(admin.ModelAdmin):
    list_display = ('entry_date', 'entry_type', 'description', 'cash_amount', 'bank_amount', 'created_by')
    list_filter = ('entry_type', 'entry_date')
    search_fields = ('description', 'created_by__username', 'created_by__first_name', 'created_by__last_name')

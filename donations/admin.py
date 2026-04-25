from django.contrib import admin

from .models import Donation, DonationCampaign, DonationCategory


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'donor',
        'donation_type',
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

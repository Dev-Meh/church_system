from django.db import models
from django.utils import timezone
from members.models import ChurchUser

class DonationCategory(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Donation Category"
        verbose_name_plural = "Donation Categories"
    
    def __str__(self):
        return self.name

class DonationCampaign(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('draft', 'Draft'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(DonationCategory, on_delete=models.SET_NULL, null=True, related_name='campaigns')
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    image = models.ImageField(upload_to='campaign_images/', blank=True)
    is_featured = models.BooleanField(default=False)
    created_by = models.ForeignKey(ChurchUser, on_delete=models.SET_NULL, null=True, related_name='created_campaigns')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Donation Campaign"
        verbose_name_plural = "Donation Campaigns"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    @property
    def progress_percentage(self):
        if self.target_amount > 0:
            return (self.current_amount / self.target_amount) * 100
        return 0
    
    @property
    def days_remaining(self):
        if self.end_date and self.status == 'active':
            return (self.end_date - timezone.now().date()).days
        return 0
    
    @property
    def total_donations(self):
        return self.donations.count()

GROUP_PAYMENT_CHOICES = [
    ("cash", "Taslimu (cash)"),
    ("mobile_money", "Simu — M-Pesa / Tigo / Airtel"),
    ("bank_transfer", "Benki"),
    ("check", "Hundi / Cheki"),
    ("online", "Mtandaoni"),
    ("card", "Kadi"),
]

_PAYMENT_METHOD_SW = dict(GROUP_PAYMENT_CHOICES)
_GIFT_TYPE_SW = {"money": "Fedha", "asset": "Mali"}


class Donation(models.Model):
    DONATION_TYPE_CHOICES = [
        ('tithe', 'Zaka'),
        ('offering', 'Sadaka'),
        ('special', 'Mchango Maalum'),
        ('other', 'Mchango'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('mobile_money', 'Mobile Money'),
        ('check', 'Check'),
        ('online', 'Online Payment'),
        ('card', 'Credit/Debit Card'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    TITHE_GIFT_TYPE_CHOICES = [
        ('money', 'Fedha'),
        ('asset', 'Mali'),
    ]
    
    donor = models.ForeignKey(ChurchUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='donations')
    campaign = models.ForeignKey(DonationCampaign, on_delete=models.SET_NULL, null=True, blank=True, related_name='donations')
    category = models.ForeignKey(DonationCategory, on_delete=models.SET_NULL, null=True, related_name='donations')
    donation_type = models.CharField(max_length=20, choices=DONATION_TYPE_CHOICES, default='other')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True)
    donor_name = models.CharField(max_length=200, blank=True)
    donor_email = models.EmailField(blank=True)
    donor_phone = models.CharField(max_length=20, blank=True)
    is_anonymous = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    tithe_gift_type = models.CharField(max_length=10, choices=TITHE_GIFT_TYPE_CHOICES, default='money')
    tithe_asset_description = models.CharField(max_length=255, blank=True)
    contribution_date = models.DateField(default=timezone.now)
    donation_date = models.DateTimeField(auto_now_add=True)
    processed_date = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(ChurchUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_donations')
    recorded_for_group = models.ForeignKey(
        'members.ChurchGroup',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_donations',
        help_text='Kundi linalohusika (mhasibu wa kundi).',
    )

    class Meta:
        verbose_name = "Donation"
        verbose_name_plural = "Donations"
        ordering = ['-donation_date']
    
    def __str__(self):
        donor_name = self.donor_name or (self.donor.full_name if self.donor else 'Anonymous')
        return f"{donor_name} - {self.amount}"

    @property
    def payment_method_sw(self):
        """Aina ya fedha kwa Kiswahili (kutoka GROUP_PAYMENT_CHOICES)."""
        if not self.payment_method:
            return ""
        return _PAYMENT_METHOD_SW.get(
            self.payment_method,
            self.get_payment_method_display(),
        )

    @property
    def gift_type_sw(self):
        """Fedha au mali."""
        return _GIFT_TYPE_SW.get(self.tithe_gift_type, self.tithe_gift_type or "")

    @property
    def aina_ya_fedha(self):
        """
        Lebo kamili ya aina ya fedha kwa mchango: Fedha (njia ya malipo)
        au Mali (maelezo ya mali).
        """
        if self.tithe_gift_type == "asset":
            desc = (self.tithe_asset_description or "").strip()
            return f"Mali{(' — ' + desc) if desc else ''}"
        return self.payment_method_sw

    @property
    def mchango_display(self):
        """Kiasi cha mchango kilichoandikwa (TZS)."""
        if self.amount is None:
            return ""
        return f"{int(self.amount)} TZS"


class DonationNotice(models.Model):
    """Time-bound donation notice shown to members."""
    title = models.CharField(max_length=180)
    message = models.TextField()
    target_member = models.ForeignKey(
        ChurchUser,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='donation_notices',
        help_text="Leave blank to show to all members."
    )
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        ChurchUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_donation_notices'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Donation Notice"
        verbose_name_plural = "Donation Notices"
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class CashBookEntry(models.Model):
    ENTRY_TYPE_CHOICES = [
        ('dr', 'Kuweka (DR)'),
        ('cr', 'Kutoa (CR)'),
    ]

    entry_date = models.DateField(default=timezone.now)
    entry_type = models.CharField(max_length=2, choices=ENTRY_TYPE_CHOICES)
    description = models.CharField(max_length=255)
    cash_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bank_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_by = models.ForeignKey(
        ChurchUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cash_book_entries'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cash Book Entry"
        verbose_name_plural = "Cash Book Entries"
        ordering = ['-entry_date', '-created_at']

    def __str__(self):
        return f"{self.get_entry_type_display()} - {self.entry_date} - {self.description}"

class Pledge(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('overdue', 'Overdue'),
    ]
    
    FREQUENCY_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    donor = models.ForeignKey(ChurchUser, on_delete=models.CASCADE, related_name='pledges')
    campaign = models.ForeignKey(DonationCampaign, on_delete=models.SET_NULL, null=True, blank=True, related_name='pledges')
    category = models.ForeignKey(DonationCategory, on_delete=models.SET_NULL, null=True, related_name='pledges')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    installment_amount = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Pledge"
        verbose_name_plural = "Pledges"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.donor.full_name} - {self.total_amount}"
    
    @property
    def remaining_amount(self):
        return self.total_amount - self.amount_paid
    
    @property
    def progress_percentage(self):
        if self.total_amount > 0:
            return (self.amount_paid / self.total_amount) * 100
        return 0

class FinancialReport(models.Model):
    REPORT_TYPE_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom'),
    ]
    
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    total_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    report_file = models.FileField(upload_to='financial_reports/', blank=True)
    is_published = models.BooleanField(default=False)
    created_by = models.ForeignKey(ChurchUser, on_delete=models.SET_NULL, null=True, related_name='created_reports')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Financial Report"
        verbose_name_plural = "Financial Reports"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.start_date} to {self.end_date}"

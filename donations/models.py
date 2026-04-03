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

class Donation(models.Model):
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
    
    donor = models.ForeignKey(ChurchUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='donations')
    campaign = models.ForeignKey(DonationCampaign, on_delete=models.SET_NULL, null=True, blank=True, related_name='donations')
    category = models.ForeignKey(DonationCategory, on_delete=models.SET_NULL, null=True, related_name='donations')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True)
    donor_name = models.CharField(max_length=200, blank=True)
    donor_email = models.EmailField(blank=True)
    donor_phone = models.CharField(max_length=20, blank=True)
    is_anonymous = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    donation_date = models.DateTimeField(auto_now_add=True)
    processed_date = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(ChurchUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_donations')
    
    class Meta:
        verbose_name = "Donation"
        verbose_name_plural = "Donations"
        ordering = ['-donation_date']
    
    def __str__(self):
        donor_name = self.donor_name or (self.donor.full_name if self.donor else 'Anonymous')
        return f"{donor_name} - {self.amount}"

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

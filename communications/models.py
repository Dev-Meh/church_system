from django.db import models
from django.utils import timezone
from members.models import ChurchUser

class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('birthday', 'Birthday'),
        ('anniversary', 'Anniversary'),
        ('event_reminder', 'Event Reminder'),
        ('new_sermon', 'New Sermon'),
        ('prayer_request', 'Prayer Request'),
        ('announcement', 'Announcement'),
        ('system', 'System Notification'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(ChurchUser, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    is_read = models.BooleanField(default=False)
    is_email_sent = models.BooleanField(default=False)
    is_sms_sent = models.BooleanField(default=False)
    action_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.full_name}"
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

class BirthdayReminder(models.Model):
    member = models.OneToOneField(ChurchUser, on_delete=models.CASCADE, related_name='birthday_reminder')
    send_email = models.BooleanField(default=True)
    send_sms = models.BooleanField(default=False)
    days_before = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    custom_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Birthday Reminder"
        verbose_name_plural = "Birthday Reminders"
    
    def __str__(self):
        return f"{self.member.full_name} - Birthday Reminder"
    
    @property
    def next_birthday(self):
        if self.member.date_of_birth:
            today = timezone.now().date()
            birthday_this_year = self.member.date_of_birth.replace(year=today.year)
            if birthday_this_year < today:
                birthday_this_year = birthday_this_year.replace(year=today.year + 1)
            return birthday_this_year
        return None

class AnniversaryReminder(models.Model):
    ANNIVERSARY_TYPE_CHOICES = [
        ('wedding', 'Wedding Anniversary'),
        ('work', 'Work Anniversary'),
        ('membership', 'Church Membership Anniversary'),
        ('other', 'Other Anniversary'),
    ]
    
    member = models.ForeignKey(ChurchUser, on_delete=models.CASCADE, related_name='anniversary_reminders')
    anniversary_type = models.CharField(max_length=20, choices=ANNIVERSARY_TYPE_CHOICES)
    anniversary_date = models.DateField()
    send_email = models.BooleanField(default=True)
    send_sms = models.BooleanField(default=False)
    days_before = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    custom_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Anniversary Reminder"
        verbose_name_plural = "Anniversary Reminders"
        unique_together = ['member', 'anniversary_type', 'anniversary_date']
    
    def __str__(self):
        return f"{self.member.full_name} - {self.get_anniversary_type_display()}"
    
    @property
    def next_anniversary(self):
        today = timezone.now().date()
        anniversary_this_year = self.anniversary_date.replace(year=today.year)
        if anniversary_this_year < today:
            anniversary_this_year = anniversary_this_year.replace(year=today.year + 1)
        return anniversary_this_year

class CommunicationGroup(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    members = models.ManyToManyField(ChurchUser, blank=True, related_name='communication_groups')
    leader = models.ForeignKey(ChurchUser, on_delete=models.SET_NULL, null=True, related_name='led_communication_groups')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Communication Group"
        verbose_name_plural = "Communication Groups"
    
    def __str__(self):
        return self.name

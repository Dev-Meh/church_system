from django.db import models
from django.utils import timezone
from members.models import ChurchUser

class PrayerRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('praying', 'Currently Praying'),
        ('answered', 'Answered'),
        ('closed', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
        ('leadership', 'Leadership Only'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    requester = models.ForeignKey(ChurchUser, on_delete=models.CASCADE, related_name='prayer_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='public')
    is_anonymous = models.BooleanField(default=False)
    prayer_count = models.PositiveIntegerField(default=0)
    answered_date = models.DateTimeField(null=True, blank=True)
    answered_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Prayer Request"
        verbose_name_plural = "Prayer Requests"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def increment_prayer_count(self):
        self.prayer_count += 1
        self.save()

class Prayer(models.Model):
    prayer_request = models.ForeignKey(PrayerRequest, on_delete=models.CASCADE, related_name='prayers')
    prayer = models.ForeignKey(ChurchUser, on_delete=models.CASCADE, related_name='prayed_for')
    prayer_text = models.TextField(blank=True)
    prayed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Prayer"
        verbose_name_plural = "Prayers"
        unique_together = ['prayer_request', 'prayer']
    
    def __str__(self):
        return f"{self.prayer.full_name} prayed for {self.prayer_request.title}"

class Testimony(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('featured', 'Featured'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(ChurchUser, on_delete=models.CASCADE, related_name='testimonies')
    related_prayer_request = models.ForeignKey(PrayerRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='testimonies')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_anonymous = models.BooleanField(default=False)
    testimony_date = models.DateField()
    approved_by = models.ForeignKey(ChurchUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_testimonies')
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Testimony"
        verbose_name_plural = "Testimonies"
        ordering = ['-testimony_date']
    
    def __str__(self):
        return self.title

class PrayerGroup(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    leader = models.ForeignKey(ChurchUser, on_delete=models.SET_NULL, null=True, related_name='led_prayer_groups')
    members = models.ManyToManyField(ChurchUser, blank=True, related_name='prayer_groups')
    meeting_day = models.CharField(max_length=20, blank=True)
    meeting_time = models.TimeField(null=True, blank=True)
    meeting_location = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Prayer Group"
        verbose_name_plural = "Prayer Groups"
    
    def __str__(self):
        return self.name

class PrayerGroupMeeting(models.Model):
    prayer_group = models.ForeignKey(PrayerGroup, on_delete=models.CASCADE, related_name='meetings')
    date = models.DateTimeField()
    location = models.CharField(max_length=200)
    agenda = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    attendees = models.ManyToManyField(ChurchUser, blank=True, related_name='prayer_meetings_attended')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Prayer Group Meeting"
        verbose_name_plural = "Prayer Group Meetings"
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.prayer_group.name} - {self.date.strftime('%Y-%m-%d %H:%M')}"

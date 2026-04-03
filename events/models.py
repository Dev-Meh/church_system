from django.db import models
from django.utils import timezone
from members.models import ChurchUser

class Event(models.Model):
    EVENT_TYPE_CHOICES = [
        ('service', 'Church Service'),
        ('seminar', 'Seminar'),
        ('conference', 'Conference'),
        ('workshop', 'Workshop'),
        ('fellowship', 'Fellowship'),
        ('outreach', 'Outreach'),
        ('meeting', 'Meeting'),
        ('other', 'Other'),
    ]
    
    FREQUENCY_CHOICES = [
        ('once', 'One Time'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = models.CharField(max_length=200)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='once')
    is_recurring = models.BooleanField(default=False)
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    registration_required = models.BooleanField(default=False)
    registration_deadline = models.DateTimeField(null=True, blank=True)
    image = models.ImageField(upload_to='event_images/', blank=True)
    organizer = models.ForeignKey(ChurchUser, on_delete=models.SET_NULL, null=True, related_name='organized_events')
    speakers = models.ManyToManyField(ChurchUser, blank=True, related_name='speaking_events')
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Event"
        verbose_name_plural = "Events"
        ordering = ['start_date']
    
    def __str__(self):
        return self.title
    
    @property
    def is_upcoming(self):
        return self.start_date > timezone.now()
    
    @property
    def is_past(self):
        return self.end_date < timezone.now()
    
    @property
    def is_ongoing(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date
    
    @property
    def registered_count(self):
        return self.registrations.filter(status='confirmed').count()

class EventRegistration(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    participant = models.ForeignKey(ChurchUser, on_delete=models.CASCADE, related_name='event_registrations')
    registration_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Event Registration"
        verbose_name_plural = "Event Registrations"
        unique_together = ['event', 'participant']
    
    def __str__(self):
        return f"{self.participant.full_name} - {self.event.title}"

class EventAttendance(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='attendances')
    participant = models.ForeignKey(ChurchUser, on_delete=models.CASCADE, related_name='event_attendances')
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Event Attendance"
        verbose_name_plural = "Event Attendances"
        unique_together = ['event', 'participant']
    
    def __str__(self):
        return f"{self.participant.full_name} - {self.event.title}"

class EventResource(models.Model):
    RESOURCE_TYPE_CHOICES = [
        ('document', 'Document'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('link', 'Link'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='resources')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPE_CHOICES)
    file = models.FileField(upload_to='event_resources/', blank=True)
    url = models.URLField(blank=True)
    uploaded_by = models.ForeignKey(ChurchUser, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Event Resource"
        verbose_name_plural = "Event Resources"
    
    def __str__(self):
        return f"{self.title} - {self.event.title}"

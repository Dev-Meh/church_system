from django.db import models
from django.conf import settings
from django.utils import timezone

class Message(models.Model):
    """Model for pastor-to-members communication"""
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Targeting options
    send_to_all = models.BooleanField(default=True, help_text="Send to all members")
    target_roles = models.CharField(
        max_length=100, 
        blank=True, 
        help_text="Comma-separated roles (e.g., 'member,pastor,elder')"
    )
    
    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.sender.first_name} {self.sender.last_name}"
    
    @property
    def recipient_count(self):
        return self.message_recipients.filter(is_delivered=True).count()
    
    @property
    def read_count(self):
        return self.message_recipients.filter(is_read=True).count()

class MessageRecipient(models.Model):
    """Track message delivery and read status for each recipient"""
    
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='message_recipients')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    is_delivered = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Message Recipient"
        verbose_name_plural = "Message Recipients"
        unique_together = ['message', 'recipient']
    
    def __str__(self):
        return f"{self.message.title} → {self.recipient.first_name} {self.recipient.last_name}"
    
    def mark_as_delivered(self):
        self.is_delivered = True
        self.delivered_at = timezone.now()
        self.save()
    
    def mark_as_read(self):
        self.is_read = True
        self.read_at = timezone.now()
        self.save()

class Announcement(models.Model):
    """Public announcements visible to all users"""
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='announcements')
    priority = models.CharField(
        max_length=10, 
        choices=Message.PRIORITY_CHOICES, 
        default='medium'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="When announcement should expire")
    
    class Meta:
        verbose_name = "Announcement"
        verbose_name_plural = "Announcements"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    @property
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

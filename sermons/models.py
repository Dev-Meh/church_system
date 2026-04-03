from django.db import models
from django.utils import timezone
from members.models import ChurchUser

class SermonSeries(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    speaker = models.ForeignKey(ChurchUser, on_delete=models.SET_NULL, null=True, related_name='sermon_series')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    cover_image = models.ImageField(upload_to='series_covers/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Sermon Series"
        verbose_name_plural = "Sermon Series"
        ordering = ['-start_date']
    
    def __str__(self):
        return self.title
    
    @property
    def sermon_count(self):
        return self.sermons.count()

class Sermon(models.Model):
    SERMON_TYPE_CHOICES = [
        ('sunday_service', 'Sunday Service'),
        ('midweek', 'Midweek Service'),
        ('conference', 'Conference'),
        ('seminar', 'Seminar'),
        ('special', 'Special Service'),
        ('youth', 'Youth Service'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    speaker = models.ForeignKey(ChurchUser, on_delete=models.SET_NULL, null=True, related_name='sermons')
    series = models.ForeignKey(SermonSeries, on_delete=models.SET_NULL, null=True, blank=True, related_name='sermons')
    sermon_date = models.DateTimeField()
    sermon_type = models.CharField(max_length=20, choices=SERMON_TYPE_CHOICES, default='sunday_service')
    bible_references = models.TextField(help_text="Enter Bible references, separated by commas")
    audio_file = models.FileField(upload_to='sermons/audio/', blank=True)
    video_file = models.FileField(upload_to='sermons/video/', blank=True)
    transcript = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    slides = models.FileField(upload_to='sermons/slides/', blank=True)
    thumbnail = models.ImageField(upload_to='sermons/thumbnails/', blank=True)
    duration = models.DurationField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    download_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Sermon"
        verbose_name_plural = "Sermons"
        ordering = ['-sermon_date']
    
    def __str__(self):
        return f"{self.title} - {self.sermon_date.strftime('%Y-%m-%d')}"
    
    def increment_download_count(self):
        self.download_count += 1
        self.save()
    
    def increment_view_count(self):
        self.view_count += 1
        self.save()

class SermonNote(models.Model):
    sermon = models.ForeignKey(Sermon, on_delete=models.CASCADE, related_name='user_notes')
    user = models.ForeignKey(ChurchUser, on_delete=models.CASCADE, related_name='sermon_notes')
    notes = models.TextField()
    timestamp = models.DurationField(null=True, blank=True, help_text="Time position in the sermon")
    is_private = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Sermon Note"
        verbose_name_plural = "Sermon Notes"
        unique_together = ['sermon', 'user']
    
    def __str__(self):
        return f"{self.user.full_name} - {self.sermon.title}"

class SermonBookmark(models.Model):
    sermon = models.ForeignKey(Sermon, on_delete=models.CASCADE, related_name='bookmarks')
    user = models.ForeignKey(ChurchUser, on_delete=models.CASCADE, related_name='sermon_bookmarks')
    timestamp = models.DurationField(null=True, blank=True, help_text="Time position in the sermon")
    note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Sermon Bookmark"
        verbose_name_plural = "Sermon Bookmarks"
        unique_together = ['sermon', 'user', 'timestamp']
    
    def __str__(self):
        return f"{self.user.full_name} - {self.sermon.title}"

class SermonCategory(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#007bff', help_text="Hex color code")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Sermon Category"
        verbose_name_plural = "Sermon Categories"
    
    def __str__(self):
        return self.name

class SermonCategoryTag(models.Model):
    sermon = models.ForeignKey(Sermon, on_delete=models.CASCADE, related_name='categories')
    category = models.ForeignKey(SermonCategory, on_delete=models.CASCADE, related_name='sermons')
    
    class Meta:
        verbose_name = "Sermon Category Tag"
        verbose_name_plural = "Sermon Category Tags"
        unique_together = ['sermon', 'category']
    
    def __str__(self):
        return f"{self.sermon.title} - {self.category.name}"

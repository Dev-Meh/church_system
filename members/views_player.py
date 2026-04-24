from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth import get_user_model
from events.models import Event, EventRegistration
from sermons.models import Sermon, SermonSeries
from datetime import timedelta

# Get the User model
ChurchUser = get_user_model()

class PlayerDashboardView(LoginRequiredMixin, ListView):
    """Unified player dashboard for members to view all content"""
    template_name = 'members/player_dashboard.html'
    context_object_name = 'content_items'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        content_items = []
        
        # Get upcoming events
        upcoming_events = Event.objects.filter(
            is_published=True,
            start_date__gt=timezone.now()
        ).order_by('start_date')[:5]
        
        for event in upcoming_events:
            # Check if user is registered
            is_registered = EventRegistration.objects.filter(
                event=event, participant=user, status='confirmed'
            ).exists()
            
            content_items.append({
                'type': 'event',
                'title': event.title,
                'description': event.description[:200] + '...' if len(event.description) > 200 else event.description,
                'date': event.start_date,
                'image': event.image.url if event.image else None,
                'url': f'/events/{event.id}/',
                'badge': 'Upcoming',
                'badge_color': 'primary',
                'is_registered': is_registered,
                'location': event.location,
                'event_type': event.get_event_type_display(),
            })
        
        # Get recent sermons
        recent_sermons = Sermon.objects.filter(
            is_published=True
        ).order_by('-sermon_date')[:5]
        
        for sermon in recent_sermons:
            content_items.append({
                'type': 'sermon',
                'title': sermon.title,
                'description': sermon.description[:200] + '...' if len(sermon.description) > 200 else sermon.description,
                'date': sermon.sermon_date,
                'image': sermon.thumbnail.url if sermon.thumbnail else None,
                'url': f'/sermons/{sermon.id}/',
                'badge': 'Sermon',
                'badge_color': 'success',
                'speaker': sermon.speaker.full_name if sermon.speaker else 'Unknown',
                'duration': sermon.duration,
                'has_audio': bool(sermon.audio_file),
                'has_video': bool(sermon.video_file),
            })
        
        # Get unread messages
        unread_messages = MessageRecipient.objects.filter(
            recipient=user,
            is_read=False,
            message__is_active=True
        ).order_by('-message__created_at')[:5]
        
        for recipient in unread_messages:
            content_items.append({
                'type': 'message',
                'title': recipient.message.title,
                'description': recipient.message.content[:200] + '...' if len(recipient.message.content) > 200 else recipient.message.content,
                'date': recipient.message.created_at,
                'image': None,
                'url': f'/members/messages/',
                'badge': 'New Message',
                'badge_color': 'warning',
                'sender': recipient.message.sender.full_name,
                'priority': recipient.message.get_priority_display(),
            })
        
        # Get active announcements
        active_announcements = Announcement.objects.filter(
            is_active=True
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        ).order_by('-created_at')[:3]
        
        for announcement in active_announcements:
            content_items.append({
                'type': 'announcement',
                'title': announcement.title,
                'description': announcement.content[:200] + '...' if len(announcement.content) > 200 else announcement.content,
                'date': announcement.created_at,
                'image': None,
                'url': f'/announcements/{announcement.id}/',
                'badge': 'Announcement',
                'badge_color': 'info',
                'author': announcement.author.full_name if announcement.author else 'Church Admin',
                'priority': announcement.get_priority_display(),
            })
        
        # Sort all items by date (newest first)
        content_items.sort(key=lambda x: x['date'], reverse=True)
        return content_items

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Create media items for the template
        recent_media = []
        for item in self.get_queryset()[:5]:  # Get first 5 items as media
            media_item = {
                'id': item.get('id', 1),  # Default ID for template
                'title': item['title'],
                'upload_date': item['date'],
                'duration': item.get('duration', '--:--'),
                'thumbnail': item.get('image'),
                'type': item['type'],
                'url': item['url'],
            }
            recent_media.append(media_item)
        
        # Get counts for each content type
        context['recent_media'] = recent_media
        context['total_media_count'] = len(recent_media)
        context['user_media_count'] = 0  # Placeholder
        context['favorite_media'] = []  # Placeholder
        
        context['upcoming_events_count'] = Event.objects.filter(
            is_published=True,
            start_date__gt=timezone.now()
        ).count()
        
        context['sermons_count'] = Sermon.objects.filter(is_published=True).count()
        
        context['unread_messages_count'] = MessageRecipient.objects.filter(
            recipient=user,
            is_read=False,
            message__is_active=True
        ).count()
        
        context['active_announcements_count'] = Announcement.objects.filter(
            is_active=True
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        ).count()
        
        # Get featured content
        context['featured_sermon'] = Sermon.objects.filter(
            is_published=True, is_featured=True
        ).first()
        
        context['featured_event'] = Event.objects.filter(
            is_published=True,
            start_date__gt=timezone.now()
        ).order_by('start_date').first()
        
        return context

@login_required
def media_player(request, content_type, content_id):
    """Unified media player for sermons and events"""
    user = request.user
    content = None
    template = 'members/media_player.html'
    
    if content_type == 'sermon':
        content = get_object_or_404(Sermon, id=content_id, is_published=True)
        # Increment view count
        content.increment_view_count()
        
        context = {
            'content_type': 'sermon',
            'sermon': content,
            'title': content.title,
            'audio_url': content.audio_file.url if content.audio_file else None,
            'video_url': content.video_file.url if content.video_file else None,
            'transcript': content.transcript,
            'notes': content.notes,
            'bible_references': content.bible_references,
            'speaker': content.speaker.full_name if content.speaker else 'Unknown',
            'sermon_date': content.sermon_date,
            'duration': content.duration,
            'series': content.series,
        }
        
    elif content_type == 'event':
        content = get_object_or_404(Event, id=content_id, is_published=True)
        
        # Check if user is registered
        is_registered = EventRegistration.objects.filter(
            event=content, participant=user, status='confirmed'
        ).exists()
        
        context = {
            'content_type': 'event',
            'event': content,
            'title': content.title,
            'description': content.description,
            'start_date': content.start_date,
            'end_date': content.end_date,
            'location': content.location,
            'is_registered': is_registered,
            'registration_required': content.registration_required,
            'max_participants': content.max_participants,
            'registered_count': content.registered_count,
            'resources': content.resources.all(),
        }
        
    else:
        return render(request, 'members/player_error.html', {
            'error': 'Invalid content type'
        })
    
    return render(request, template, context)

@login_required
def my_content(request):
    """Personalized content view for the logged-in member"""
    user = request.user
    
    # Get user's registered events
    my_events = EventRegistration.objects.filter(
        participant=user, status='confirmed'
    ).select_related('event').order_by('event__start_date')
    
    # Get user's sermon bookmarks and notes
    from sermons.models import SermonBookmark, SermonNote
    my_bookmarks = SermonBookmark.objects.filter(user=user).select_related('sermon').order_by('-created_at')
    my_notes = SermonNote.objects.filter(user=user).select_related('sermon').order_by('-created_at')
    
    # Get user's messages
    my_messages = MessageRecipient.objects.filter(
        recipient=user, message__is_active=True
    ).select_related('message', 'message__sender').order_by('-message__created_at')
    
    context = {
        'my_events': my_events,
        'my_bookmarks': my_bookmarks,
        'my_notes': my_notes,
        'my_messages': my_messages,
        'total_events': my_events.count(),
        'total_bookmarks': my_bookmarks.count(),
        'total_notes': my_notes.count(),
        'total_messages': my_messages.count(),
        'unread_messages': my_messages.filter(is_read=False).count(),
    }
    
    return render(request, 'members/my_content.html', context)

from .language_utils import LanguageManager
from .permissions import (
    can_manage_church_communications,
    can_create_church_announcements,
    has_church_leadership,
)
from .app_nav import resolve_active_nav


def language_context(request):
    """Add language context to all templates"""
    current_language = LanguageManager.get_current_language(request)
    supported_languages = LanguageManager.get_supported_languages()

    return {
        'current_language': current_language,
        'supported_languages': supported_languages,
        'language_info': LanguageManager.get_language_info(current_language),
    }


def church_permissions_context(request):
    user = request.user
    return {
        'can_manage_communications': (
            can_manage_church_communications(user) if user.is_authenticated else False
        ),
        'can_create_announcements': (
            can_create_church_announcements(user) if user.is_authenticated else False
        ),
        'has_leadership': (
            has_church_leadership(user) if user.is_authenticated else False
        ),
    }


def app_shell_context(request):
    user = request.user
    if not user.is_authenticated:
        return {
            'active_nav': '',
            'show_content_player_nav': False,
            'nav_events_count': 0,
            'nav_sermons_count': 0,
            'nav_prayers_count': 0,
            'nav_messages_count': 0,
            'sent_messages_count': 0,
        }

    from events.models import Event
    from sermons.models import Sermon
    from prayers.models import PrayerRequest
    from .models_message import MessageRecipient, Message

    match = request.resolver_match
    app_name = getattr(match, 'app_name', '') or ''
    url_name = getattr(match, 'url_name', '') or ''

    sent_messages_count = 0
    if can_manage_church_communications(user):
        sent_messages_count = Message.objects.filter(sender=user).count()

    show_content_player_nav = user.role not in ('member',)

    return {
        'active_nav': resolve_active_nav(app_name, url_name),
        'show_content_player_nav': show_content_player_nav,
        'nav_events_count': Event.objects.filter(is_published=True).count(),
        'nav_sermons_count': Sermon.objects.filter(is_published=True).count(),
        'nav_prayers_count': PrayerRequest.objects.filter(
            visibility__in=['public', 'leadership'],
        ).exclude(status='closed').count(),
        'nav_messages_count': MessageRecipient.objects.filter(recipient=user).count(),
        'sent_messages_count': sent_messages_count,
    }

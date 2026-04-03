from django.utils import translation
from django.conf import settings
from django.urls import reverse

from .i18n_strings import EXTRA_EN, EXTRA_SW

class LanguageManager:
    """Handle language switching and management for the church system"""
    
    SUPPORTED_LANGUAGES = {
        'en': {
            'code': 'en',
            'name': 'English',
            'native_name': 'English',
            'flag': '🇬🇧',
            'direction': 'ltr'
        },
        'sw': {
            'code': 'sw',
            'name': 'Swahili',
            'native_name': 'Kiswahili',
            'flag': '🇹🇿',
            'direction': 'ltr'
        }
    }
    
    @classmethod
    def get_supported_languages(cls):
        """Get list of supported languages"""
        return list(cls.SUPPORTED_LANGUAGES.values())
    
    @classmethod
    def get_language_info(cls, language_code):
        """Get language information by code"""
        return cls.SUPPORTED_LANGUAGES.get(language_code, cls.SUPPORTED_LANGUAGES['en'])
    
    @classmethod
    def set_language(cls, request, language_code):
        """Activate language for this request and persist preference in session."""
        if language_code in cls.SUPPORTED_LANGUAGES:
            request.session['django_language'] = language_code
            translation.activate(language_code)
            request.LANGUAGE_CODE = cls.normalize_language_code(
                translation.get_language() or language_code
            )
            return True
        return False
    
    @staticmethod
    def normalize_language_code(code):
        """Map Django language codes (e.g. en-us) to our app keys en / sw."""
        if not code:
            return 'en'
        primary = str(code).split('-')[0].lower()
        if primary == 'en':
            return 'en'
        if primary == 'sw':
            return 'sw'
        return primary if primary in LanguageManager.SUPPORTED_LANGUAGES else 'en'
    
    @classmethod
    def get_current_language(cls, request):
        """Prefer LocaleMiddleware (cookie), then session, then settings."""
        code = getattr(request, 'LANGUAGE_CODE', None)
        if not code:
            code = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
        if not code:
            code = request.session.get('django_language')
        if not code:
            code = settings.LANGUAGE_CODE
        return cls.normalize_language_code(code)
    
    @classmethod
    def get_language_switch_url(cls, request, language_code):
        """Get URL for language switching"""
        return reverse('members:set_language', kwargs={'language_code': language_code})

# Translation dictionary for common terms
TRANSLATIONS = {
    'en': {
        # Navigation
        'dashboard': 'Dashboard',
        'members': 'Members',
        'sermons': 'Sermons',
        'messages': 'Messages',
        'donations': 'Donations',
        'events': 'Events',
        'settings': 'Settings',
        'logout': 'Logout',
        
        # Common actions
        'create': 'Create',
        'edit': 'Edit',
        'delete': 'Delete',
        'save': 'Save',
        'cancel': 'Cancel',
        'submit': 'Submit',
        'search': 'Search',
        'filter': 'Filter',
        
        # Church specific
        'pastor': 'Pastor',
        'elder': 'Elder',
        'deacon': 'Deacon',
        'member': 'Member',
        'admin': 'Administrator',
        
        # Messages
        'send_message': 'Send Message',
        'message_title': 'Message Title',
        'message_content': 'Message Content',
        'send_to_all': 'Send to All Members',
        'send_to_roles': 'Send to Specific Roles',
        
        # Dashboard
        'total_members': 'Total Members',
        'active_members': 'Active Members',
        'new_members': 'New Members',
        'total_donations': 'Total Donations',
        'recent_activity': 'Recent Activity',
        
        # Forms
        'first_name': 'First Name',
        'last_name': 'Last Name',
        'email': 'Email',
        'phone_number': 'Phone Number',
        'date_of_birth': 'Date of Birth',
        'address': 'Address',
        'city': 'City',
        'country': 'Country',
        
        # Status messages
        'success': 'Success',
        'error': 'Error',
        'warning': 'Warning',
        'info': 'Information',
        
        # Dashboard specific
        'main_dashboard': 'Main Dashboard',
        'statistics': 'Statistics',
        'welcome_back': 'Welcome back',
        'pastoral_quick_actions': 'Pastoral Quick Actions',
        'communication': 'Communication',
        'member_management': 'Member Management',
        'administration': 'Administration',
        
        # Sermons
        'all_sermons': 'All Sermons',
        'create_sermon': 'Create Sermon',
        'sermon_series': 'Sermon Series',
        
        # Quick Actions
        'quick_actions': 'Quick Actions',
        'create_message': 'Create Message',
        'view_messages': 'View Messages',
        'admin_panel': 'Admin Panel',
        'all_members': 'All Members',
        'edit_profile': 'Edit Profile',
    },
    'sw': {
        # Navigation
        'dashboard': 'Dashibodi',
        'members': 'Wanachama',
        'sermons': 'Mahubiri',
        'messages': 'Ujumbe',
        'donations': 'Michango',
        'events': 'Matukio',
        'settings': 'Mipangilio',
        'logout': 'Toka',
        
        # Common actions
        'create': 'Unda',
        'edit': 'Hariri',
        'delete': 'Futa',
        'save': 'Hifadhi',
        'cancel': 'Ghairi',
        'submit': 'Wasilisha',
        'search': 'Tafuta',
        'filter': 'Chuja',
        
        # Church specific
        'pastor': 'Mchungaji',
        'elder': 'Mzee wa Kanisa',
        'deacon': 'Mshirika',
        'member': 'Mwanachama',
        'admin': 'Msimamizi',
        
        # Messages
        'send_message': 'Tuma Ujumbe',
        'message_title': 'Kichwa cha Ujumbe',
        'message_content': 'Maudhui ya Ujumbe',
        'send_to_all': 'Tuma kwa Wanachama Wote',
        'send_to_roles': 'Tuma kwa Viti Maalum',
        
        # Dashboard
        'total_members': 'Jumla ya Wanachama',
        'active_members': 'Wanachama Walio Hai',
        'new_members': 'Wanachama Wapya',
        'total_donations': 'Jumla ya Michango',
        'recent_activity': 'Shughuli za Karibuni',
        
        # Forms
        'first_name': 'Jina la Kwanza',
        'last_name': 'Jina la Mwisho',
        'email': 'Barua pepe',
        'phone_number': 'Namba ya Simu',
        'date_of_birth': 'Tarehe ya Kuzaliwa',
        'address': 'Anwani',
        'city': 'Jiji',
        'country': 'Nchi',
        
        # Status messages
        'success': 'Mafanikio',
        'error': 'Kosa',
        'warning': 'Onyo',
        'info': 'Maelezo',
        
        # Dashboard specific
        'main_dashboard': 'Dashibodi Kuu',
        'statistics': 'Takwimu',
        'welcome_back': 'Karibu tena',
        'pastoral_quick_actions': 'Hatua za Haraka za Mchungaji',
        'communication': 'Mawasiliano',
        'member_management': 'Usimamizi wa Wanachama',
        'administration': 'Utawala',
        
        # Sermons
        'all_sermons': 'Mahubiri Yote',
        'create_sermon': 'Unda Hubo',
        'sermon_series': 'Mfululizo wa Mahubiri',
        
        # Quick Actions
        'quick_actions': 'Hatua za Haraka',
        'create_message': 'Unda Ujumbe',
        'view_messages': 'Ona Ujumbe',
        'admin_panel': 'Bodi ya Utawala',
        'all_members': 'Wanachama Wote',
        'edit_profile': 'Haribu Wasifu',
    },
}

TRANSLATIONS['en'].update(EXTRA_EN)
TRANSLATIONS['sw'].update(EXTRA_SW)


def get_translation(key, language_code='en'):
    """Get translation for a key in specified language"""
    return TRANSLATIONS.get(language_code, {}).get(key, key)

def t(key, request=None):
    """Translation function for templates"""
    if request:
        language_code = LanguageManager.get_current_language(request)
    else:
        language_code = 'en'
    return get_translation(key, language_code)

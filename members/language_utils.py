from django.conf import settings
from django.utils import translation
from django.contrib import messages

class LanguageManager:
    """Manage language switching and translations"""
    
    SUPPORTED_LANGUAGES = {
        'en': {
            'code': 'en',
            'name': 'English',
            'native_name': 'English',
            'flag': '🇬🇧',
            'direction': 'ltr',
        },
        'sw': {
            'code': 'sw',
            'name': 'Swahili',
            'native_name': 'Kiswahili',
            'flag': '🇹🇿',
            'direction': 'ltr',
        }
    }
    
    TRANSLATIONS = {
        # Navigation and common terms
        'dashboard': {'en': 'Dashboard', 'sw': 'Dashibodi'},
        'members': {'en': 'Members', 'sw': 'Wanachama'},
        'messages': {'en': 'Messages', 'sw': 'Ujumbe'},
        'sermons': {'en': 'Sermons', 'sw': 'Mahubiri'},
        'donations': {'en': 'Donations', 'sw': 'Michango'},
        'events': {'en': 'Events', 'sw': 'Matukio'},
        'profile': {'en': 'Profile', 'sw': 'Wasifu'},
        'settings': {'en': 'Settings', 'sw': 'Mipangilio'},
        'logout': {'en': 'Logout', 'sw': 'Toka'},
        'login': {'en': 'Login', 'sw': 'Ingia'},
        
        # Form labels and buttons
        'send': {'en': 'Send', 'sw': 'Tuma'},
        'cancel': {'en': 'Cancel', 'sw': 'Ghairi'},
        'save': {'en': 'Save', 'sw': 'Hifadhi'},
        'edit': {'en': 'Edit', 'sw': 'Hariri'},
        'delete': {'en': 'Delete', 'sw': 'Futa'},
        'create': {'en': 'Create', 'sw': 'Unda'},
        'update': {'en': 'Update', 'sw': 'Sasisha'},
        'view': {'en': 'View', 'sw': 'Ona'},
        'back': {'en': 'Back', 'sw': 'Rudi'},
        
        # Dashboard specific labels
        'total_donations': {'en': 'Total Donations', 'sw': 'Jumla ya Michango'},
        'donations_made': {'en': 'Donations Made', 'sw': 'Michango Iliyotolewa'},
        'member_since': {'en': 'Member Since', 'sw': 'Mwanachama Tangu'},
        'recent_donations_panel': {'en': 'Recent Donations', 'sw': 'Michango ya Karibuni'},
        'make_donation': {'en': 'Make Donation', 'sw': 'Toa Michango'},
        'edit_profile': {'en': 'Edit Profile', 'sw': 'Hariri Wasifu'},
        'member_dashboard_title': {'en': 'Member Dashboard', 'sw': 'Dashibodi ya Mwanachama'},
        'quick_actions': {'en': 'Quick Actions', 'sw': 'Hatua za Haraka'},
        'send_message': {'en': 'Send Message', 'sw': 'Tuma Ujumbe'},
        'main_menu': {'en': 'Main Menu', 'sw': 'Menyu Kuu'},
        'main_dashboard': {'en': 'Main Dashboard', 'sw': 'Dashibodi Kuu'},
        
        # Navigation items
        'create_message': {'en': 'Create Message', 'sw': 'Unda Ujumbe'},
        'view_messages': {'en': 'View Messages', 'sw': 'Ona Ujumbe'},
        'all_members': {'en': 'All Members', 'sw': 'Wanachama Wote'},
        'create_sermon': {'en': 'Create Sermon', 'sw': 'Unda Hubo'},
        'series_label': {'en': 'Series', 'sw': 'Mfululizo'},
        'admin_panel': {'en': 'Admin Panel', 'sw': 'Bodi ya Utawala'},
        
        # Message center navigation
        'message_center_nav': {'en': 'Message Center', 'sw': 'Kituo cha Ujumbe'},
        'new_message_nav': {'en': 'New Message', 'sw': 'Ujumbe Mpya'},
        'sent_messages_nav': {'en': 'Sent Messages', 'sw': 'Ujumbe Uliotumwa'},
        
        # Pastor quick actions
        'create_message_to_congregation': {'en': 'Create Message to Congregation', 'sw': 'Unda Ujumbe kwa Jumuiya'},
        'create_announcement': {'en': 'Create Announcement', 'sw': 'Unda Tangazo'},
        'view_all_members_directory': {'en': 'View All Members Directory', 'sw': 'Ona Orodha ya Wanachama Wote'},
        'financial_reports_overview': {'en': 'Financial Reports & Overview', 'sw': 'Ripoti za Fedha na Muhtasari'},
        
        # Message related
        'message_title': {'en': 'Message Title', 'sw': 'Kichwa cha Ujumbe'},
        'message_content': {'en': 'Message Content', 'sw': 'Maudhui ya Ujumbe'},
        'send_message': {'en': 'Send Message', 'sw': 'Tuma Ujumbe'},
        'my_messages': {'en': 'My Messages', 'sw': 'Ujumbe Wangu'},
        'all_messages': {'en': 'All Messages', 'sw': 'Ujumbe Zote'},
        'unread_messages': {'en': 'Unread', 'sw': 'Zisizosomwa'},
        'delivered_messages': {'en': 'Delivered', 'sw': 'Zimetumwa'},
        'recent_messages': {'en': 'Recent Messages', 'sw': 'Ujumbe wa Karibuni'},
        
        # Message form labels
        'compose_message_title': {'en': 'Compose Message', 'sw': 'Andika Ujumbe'},
        'message_recipients_label': {'en': 'Message Recipients', 'sw': 'Wapokeaji wa Ujumbe'},
        'message_broadcast_help': {'en': 'Broadcast a message to all church members', 'sw': 'Tuma ujumbe kwa wanachama wote wa kanisa'},
        'message_details_header': {'en': 'Message Details', 'sw': 'Maelezo ya Ujumbe'},
        'delivery_rate_label': {'en': 'Delivery Rate', 'sw': 'Kiwango cha Uwasilishaji'},
        'tracking_label': {'en': 'Tracking', 'sw': 'Ufuatiliaji'},
        
        # Status messages
        'no_active_members': {'en': 'No active members found', 'sw': 'Hakuna wanachama walio hai'},
        
        # Form labels
        'message_title_label': {'en': 'Message Title', 'sw': 'Kichwa cha Ujumbe'},
        'priority_level_label': {'en': 'Priority Level', 'sw': 'Kiwango cha Kipaumbele'},
        'send_to_all_label': {'en': 'Send to All Members', 'sw': 'Tuma kwa Wanachama Wote'},
        'recipients': {'en': 'Recipients', 'sw': 'Wapokeaji'},
        'target_roles': {'en': 'Target Roles (if not sending to all)', 'sw': 'Viti Malengo (kama hautumii kwa wote)'},
        'send_message_btn': {'en': 'Send Message', 'sw': 'Tuma Ujumbe'},
        
        # Sermon related
        'all_sermons': {'en': 'All Sermons', 'sw': 'Mahubiri Yote'},
        'featured_sermons': {'en': 'Featured Sermons', 'sw': 'Mahubiri Yanayopendwa'},
        'sermon_series': {'en': 'Sermon Series', 'sw': 'Mfululizo wa Mahubiri'},
        'listen': {'en': 'Listen', 'sw': 'Sikiliza'},
        'download': {'en': 'Download', 'sw': 'Pakua'},
        
        # Status and feedback
        'success': {'en': 'Success', 'sw': 'Mafanikio'},
        'error': {'en': 'Error', 'sw': 'Kosa'},
        'loading': {'en': 'Loading', 'sw': 'Inapakia'},
        'no_data': {'en': 'No data available', 'sw': 'Hakuna data inapatikana'},
        'confirm': {'en': 'Are you sure?', 'sw': 'Una uhakika?'},
        'yes': {'en': 'Yes', 'sw': 'Ndio'},
        'no': {'en': 'No', 'sw': 'Hapana'},
        
        # Dashboard stats
        'total_members': {'en': 'Total Members', 'sw': 'Jumla ya Wanachama'},
        'active_members': {'en': 'Active Members', 'sw': 'Wanachama Wenye Vitendo'},
        'new_members': {'en': 'New Members', 'sw': 'Wanachama Wapya'},
        'total_donations': {'en': 'Total Donations', 'sw': 'Jumla ya Michango'},
        'this_month': {'en': 'This Month', 'sw': 'Mwezi Huu'},
    }
    
    @classmethod
    def get_supported_languages(cls):
        """Get all supported languages"""
        return cls.SUPPORTED_LANGUAGES
    
    @classmethod
    def get_language_info(cls, language_code):
        """Get language information by code"""
        return cls.SUPPORTED_LANGUAGES.get(language_code, cls.SUPPORTED_LANGUAGES['en'])
    
    @classmethod
    def get_current_language(cls, request):
        """Get current language from session or default"""
        return request.session.get('django_language', 'en')
    
    @classmethod
    def set_language(cls, request, language_code):
        """Set language in session"""
        if language_code in cls.SUPPORTED_LANGUAGES:
            request.session['django_language'] = language_code
            request.session.modified = True
            return True
        return False
    
    @classmethod
    def get_translation(cls, key, language_code='en'):
        """Get translation for a key"""
        normalized_key = (key or "").strip()

        # Direct hit
        if normalized_key in cls.TRANSLATIONS:
            return cls.TRANSLATIONS[normalized_key].get(language_code, normalized_key)

        # Common typo tolerance, e.g. "sermon_title_labe" -> "sermon_title_label"
        if normalized_key.endswith("labe"):
            candidate = f"{normalized_key}l"
            if candidate in cls.TRANSLATIONS:
                return cls.TRANSLATIONS[candidate].get(language_code, candidate)

        # Friendly fallback instead of exposing raw translation key
        return normalized_key.replace("_", " ").strip().capitalize() or key

def get_translation(key, language_code='en'):
    """Helper function to get translation"""
    return LanguageManager.get_translation(key, language_code)

from .language_utils import LanguageManager

def language_context(request):
    """Add language context to all templates"""
    current_language = LanguageManager.get_current_language(request)
    supported_languages = LanguageManager.get_supported_languages()
    
    return {
        'current_language': current_language,
        'supported_languages': supported_languages,
        'language_info': LanguageManager.get_language_info(current_language)
    }

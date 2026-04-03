from django import template

from ..language_utils import LanguageManager, get_translation

register = template.Library()


@register.simple_tag(takes_context=True)
def church_t(context, key):
    """Translate a key using session/cookie language (same catalog as language_utils)."""
    request = context.get("request")
    lang = LanguageManager.get_current_language(request) if request else "en"
    return get_translation(key, lang)

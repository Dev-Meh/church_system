from django import template

from ..language_utils import LanguageManager, get_translation

register = template.Library()


@register.simple_tag(takes_context=True)
def church_t(context, key):
    """Translate a key using session/cookie language (same catalog as language_utils)."""
    request = context.get("request")
    lang = LanguageManager.get_current_language(request) if request else "en"
    return get_translation(key, lang)


@register.simple_tag(takes_context=True)
def church_dtype(context, code):
    """Translate donation type code (tithe, offering, special, other)."""
    request = context.get("request")
    lang = LanguageManager.get_current_language(request) if request else "en"
    return get_translation(f"dtype_{code}", lang)


@register.simple_tag(takes_context=True)
def church_pmethod(context, method_code):
    """Translate payment method code."""
    request = context.get("request")
    lang = LanguageManager.get_current_language(request) if request else "en"
    return get_translation(f"pmethod_{method_code}", lang)


@register.simple_tag(takes_context=True)
def church_pledge_status(context, status_code):
    """Translate pledge status code."""
    request = context.get("request")
    lang = LanguageManager.get_current_language(request) if request else "en"
    return get_translation(f"pledge_status_{status_code}", lang)

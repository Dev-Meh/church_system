from django import template

from ..language_utils import LanguageManager, get_translation

register = template.Library()


@register.simple_tag(takes_context=True)
def church_t(context, key, **fmt):
    """Translate a key using session/cookie language (same catalog as language_utils)."""
    request = context.get("request")
    lang = LanguageManager.get_current_language(request) if request else "en"
    text = get_translation(key, lang)
    if fmt:
        try:
            return text.format(**fmt)
        except (KeyError, ValueError):
            return text
    return text


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


@register.simple_tag(takes_context=True)
def church_uni_status(context, status_code):
    """Translate university student status code."""
    request = context.get("request")
    lang = LanguageManager.get_current_language(request) if request else "en"
    return get_translation(f"uni_status_{status_code}", lang)


@register.simple_tag(takes_context=True)
def church_uni_level(context, level_code):
    """Translate university education level code."""
    request = context.get("request")
    lang = LanguageManager.get_current_language(request) if request else "en"
    return get_translation(f"uni_level_{level_code}", lang)


@register.simple_tag(takes_context=True)
def church_group_title(context, group):
    """Translate church group type display title."""
    request = context.get("request")
    lang = LanguageManager.get_current_language(request) if request else "en"
    code = getattr(group, "group_type", None)
    if code:
        label = get_translation(f"grp_type_{code}", lang)
        if label and not label.startswith("Grp type"):
            return label
    return getattr(group, "name", str(group))


@register.simple_tag(takes_context=True)
def church_grole(context, role_code):
    """Translate group membership role code."""
    request = context.get("request")
    lang = LanguageManager.get_current_language(request) if request else "en"
    return get_translation(f"grp_role_{role_code}", lang)

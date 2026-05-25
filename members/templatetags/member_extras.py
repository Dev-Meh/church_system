from django import template

register = template.Library()


@register.filter
def aina_ya_fedha(donation):
    """Kiswahili: aina ya fedha (hutumia Donation.aina_ya_fedha)."""
    if donation is None:
        return ""
    return getattr(donation, "aina_ya_fedha", "") or ""


@register.inclusion_tag('members/includes/user_avatar.html')
def user_avatar(user, size=36, css_class=''):
    initials = '?'
    if user and getattr(user, 'is_authenticated', False):
        first = (getattr(user, 'first_name', '') or '').strip()[:1]
        last = (getattr(user, 'last_name', '') or '').strip()[:1]
        initials = f'{first}{last}'.upper()
        if not initials:
            username = (getattr(user, 'username', '') or '').strip()
            initials = (username[:2] or '?').upper()
    return {
        'user': user,
        'size': size,
        'css_class': css_class,
        'initials': initials,
    }

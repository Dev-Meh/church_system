"""Maswali ya ujumbe: kanisa zima vs matangazo ya idara."""

from .models_message import MessageRecipient


def member_inbox_queryset(user, group=None):
    """
    group=None → ujumbe wa kanisa zima tu (church_group tupu).
    group=ChurchGroup → matangazo ya idara hiyo pekee.
    """
    qs = (
        MessageRecipient.objects.filter(
            recipient=user,
            message__is_active=True,
        )
        .select_related("message", "message__sender", "message__church_group")
        .order_by("-message__created_at")
    )
    if group is not None:
        return qs.filter(message__church_group=group)
    return qs.filter(message__church_group__isnull=True)


def church_inbox_unread_count(user):
    return member_inbox_queryset(user, group=None).filter(is_read=False).count()

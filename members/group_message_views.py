"""Matangazo ya idara (katibu / mwenyekiti wa kundi)."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .group_permissions import can_access_group, can_send_group_messages
from .group_services import get_group_member_ids
from .message_forms import GroupMessageForm
from .models import ChurchGroup, ChurchUser
from .models_message import Message, MessageRecipient
from .sms_service import sms_service


def _group_recipients(group):
    return ChurchUser.objects.filter(
        id__in=get_group_member_ids(group),
        is_active=True,
    )


@login_required(login_url="members:login")
def group_broadcast(request, pk):
    """Katibu au mwenyekiti hutuma matangazo kwa wanachama wa idara."""
    group = get_object_or_404(ChurchGroup, pk=pk, is_active=True)
    if not can_access_group(request.user, group):
        messages.error(request, "Huruhusiwi kuona idara hii.")
        return redirect("members:group_list")
    if not can_send_group_messages(request.user, group):
        messages.error(request, "Ni katibu au mwenyekiti tu anaweza kutuma matangazo.")
        return redirect("members:group_detail", pk=pk)

    recipients = _group_recipients(group)
    sent_messages = Message.objects.filter(
        church_group=group,
        sender=request.user,
    ).order_by("-created_at")[:15]

    if request.method == "POST":
        form = GroupMessageForm(request.POST)
        if form.is_valid():
            recipient_list = list(recipients)
            if not recipient_list:
                messages.error(
                    request,
                    "Hakuna wanachama hai kwenye idara hii. Endesha "
                    "python manage.py sync_group_memberships au ongeza wanachama.",
                )
            else:
                msg = form.save(commit=False)
                msg.sender = request.user
                msg.church_group = group
                msg.send_to_all = True
                msg.target_roles = ""
                msg.save()

                rows = [
                    MessageRecipient(
                        message=msg,
                        recipient=recipient,
                        is_delivered=True,
                        delivered_at=timezone.now(),
                    )
                    for recipient in recipient_list
                ]
                MessageRecipient.objects.bulk_create(rows)

                sms_text = (
                    f"{group.display_title}: {msg.title}\n{msg.content[:100]}..."
                )
                for recipient in recipient_list:
                    if recipient.phone_number:
                        sms_service.send_sms(recipient.phone_number, sms_text)

                messages.success(
                    request,
                    f"Matangazo yametumwa kwa wanachama {len(rows)} wa "
                    f"{group.display_title}.",
                )
                return redirect("members:group_broadcast", pk=pk)
    else:
        form = GroupMessageForm()

    return render(
        request,
        "members/group_broadcast.html",
        {
            "group": group,
            "form": form,
            "recipient_count": recipients.count(),
            "sent_messages": sent_messages,
        },
    )

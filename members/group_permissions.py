"""Permissions for church groups (leaders, katibu, mhasibu wa kundi)."""

from django.db.models import Q

from .models import ChurchGroup, GroupMembership
from .group_services import get_group_member_ids
from .permissions import has_church_leadership


def is_church_wide_accountant(user):
    return (
        getattr(user, "role", None) == "accountant"
        and bool(getattr(user, "can_post_member_donations", False))
    )


def groups_led_or_staffed(user):
    """Groups where user is leader, secretary, or accountant."""
    if not user or not user.is_authenticated:
        return ChurchGroup.objects.none()
    return ChurchGroup.objects.filter(is_active=True).filter(
        Q(leader=user) | Q(secretary=user) | Q(accountant=user)
    )


def groups_accounted_by(user):
    return ChurchGroup.objects.filter(is_active=True, accountant=user)


def groups_visible_to_user(user):
    if has_church_leadership(user):
        return ChurchGroup.objects.filter(is_active=True)
    from .permissions import can_manage_church_groups

    if can_manage_church_groups(user):
        return ChurchGroup.objects.filter(is_active=True)
    q = Q(memberships__member=user, memberships__is_active=True)
    q |= Q(leader=user) | Q(secretary=user) | Q(accountant=user)
    return ChurchGroup.objects.filter(is_active=True).filter(q).distinct()


def can_access_group(user, group):
    if has_church_leadership(user):
        return True
    if group.leader_id == user.id:
        return True
    if group.secretary_id == user.id:
        return True
    if group.accountant_id == user.id:
        return True
    return GroupMembership.objects.filter(
        group=group, member=user, is_active=True
    ).exists()


def can_assign_group_officers(user):
    return has_church_leadership(user)


def is_group_mwenyekiti(user, group):
    """Mwenyekiti wa kundi (FK au cheo leader kwenye uanachama)."""
    if not user or not user.is_authenticated:
        return False
    if group.leader_id == user.id:
        return True
    return GroupMembership.objects.filter(
        group=group,
        member=user,
        role="leader",
        is_active=True,
    ).exists()


def can_view_group_members(user, group):
    """
    Orodha ya wanachama: mwenyekiti, katibu, mhasibu, msaidizi, mchungaji tu.
    Mwanachama wa kawaida (cheo member) haioni orodha ya wenzake.
    """
    if has_church_leadership(user):
        return True
    if is_group_mwenyekiti(user, group):
        return True
    if group.secretary_id == user.id or group.accountant_id == user.id:
        return True
    return GroupMembership.objects.filter(
        group=group,
        member=user,
        role="assistant",
        is_active=True,
    ).exists()


def can_manage_group_members(user, group):
    """Kuongeza wanachama: mwenyekiti na uongozi wa kanisa pekee."""
    if has_church_leadership(user):
        return True
    return is_group_mwenyekiti(user, group)


def is_group_katibu(user, group):
    if not user or not user.is_authenticated:
        return False
    if group.secretary_id == user.id:
        return True
    return GroupMembership.objects.filter(
        group=group,
        member=user,
        role="secretary",
        is_active=True,
    ).exists()


def is_group_accountant_for(user, group):
    if not user or not user.is_authenticated:
        return False
    if group.accountant_id == user.id:
        return True
    return GroupMembership.objects.filter(
        group=group,
        member=user,
        role="accountant",
        is_active=True,
    ).exists()


def is_group_plain_member(user, group):
    """Mwanachama wa kawaida wa idara (si mwenyekiti, katibu, wala mhasibu)."""
    if not can_access_group(user, group):
        return False
    if (
        is_group_mwenyekiti(user, group)
        or is_group_katibu(user, group)
        or is_group_accountant_for(user, group)
    ):
        return False
    return has_church_leadership(user) is False


def can_manage_group_donations(user, group):
    """Mhasibu wa kundi na mwenyekiti: ingiza na simamia michango ya wanachama."""
    if has_church_leadership(user) or is_church_wide_accountant(user):
        return True
    if is_group_mwenyekiti(user, group) or is_group_accountant_for(user, group):
        return True
    return False


def can_send_group_messages(user, group):
    """Katibu na mwenyekiti: matangazo kwa wanachama wa idara."""
    if has_church_leadership(user):
        return True
    if is_group_mwenyekiti(user, group) or is_group_katibu(user, group):
        return True
    return False


def can_manage_group_activities(user, group):
    """Mwenyekiti, katibu, na uongozi wa kanisa: kuandika shughuli za idara."""
    if has_church_leadership(user):
        return True
    if is_group_mwenyekiti(user, group) or is_group_katibu(user, group):
        return True
    return False


def is_group_only_accountant(user):
    """Mhasibu wa kundi tu — si mhasibu wa kanisa zima."""
    if not user or not user.is_authenticated:
        return False
    if is_church_wide_accountant(user):
        return False
    return groups_accounted_by(user).exists()


def get_scoped_donor_ids_for_user(user):
    """
    Church accountant / leadership: None (means no filter = all).
    Group accountant: only member IDs from their group(s).
    """
    if has_church_leadership(user) or is_church_wide_accountant(user):
        return None
    groups = groups_accounted_by(user)
    if not groups.exists():
        return []
    member_ids = set()
    for group in groups:
        member_ids.update(get_group_member_ids(group))
    return list(member_ids)


def can_record_group_donations(user, group):
    return can_manage_group_donations(user, group)


def donations_queryset_for_user(user, base_qs):
    """Filter donations for group-only accountants."""
    donor_ids = get_scoped_donor_ids_for_user(user)
    if donor_ids is None:
        return base_qs
    if not donor_ids:
        return base_qs.none()
    return base_qs.filter(
        Q(donor_id__in=donor_ids)
        | Q(recorded_for_group__accountant=user)
    )

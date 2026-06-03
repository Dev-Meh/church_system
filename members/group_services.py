"""Default church groups, auto-membership rules, and officer sync."""

from django.db import transaction

from .models import ChurchGroup, GroupMembership, ChurchUser

# Vijana: chini ya miaka 40 (lazima tarehe ya kuzaliwa iwe kwenye wasifu)
YOUTH_MAX_AGE = 40
# Akina mama: jinsia ya kike
WOMEN_GENDER = "F"
OFFICER_MEMBERSHIP_ROLES = frozenset(
    {"leader", "assistant", "secretary", "accountant"}
)

AUTO_CHURCH_GROUPS = [
    {
        "name": "Idara ya Vijana (CFD'S)",
        "group_type": "youth",
        "description": "Idara ya vijana wa kanisa — shughuli, mafundisho, na huduma.",
    },
    {
        "name": "Idara ya Wanawake (WWM)",
        "group_type": "women",
        "description": "Idara ya wanawake — maombi, huduma, na mikutano.",
    },
]

LEGACY_GROUP_NAMES = {
    "youth": "Kundi la Vijana PHM-ARCC",
    "women": "Kundi la Akina Mama PHM-ARCC",
}


def ensure_default_church_groups():
    """Create or update default youth and women departments (idempotent)."""
    created = 0
    for data in AUTO_CHURCH_GROUPS:
        group = ChurchGroup.objects.filter(group_type=data["group_type"]).first()
        if group:
            updated_fields = []
            if group.name != data["name"]:
                group.name = data["name"]
                updated_fields.append("name")
            if group.description != data["description"]:
                group.description = data["description"]
                updated_fields.append("description")
            if updated_fields:
                group.save(update_fields=updated_fields)
            continue

        legacy_name = LEGACY_GROUP_NAMES.get(data["group_type"])
        if legacy_name:
            legacy_group = ChurchGroup.objects.filter(name=legacy_name).first()
            if legacy_group:
                legacy_group.name = data["name"]
                legacy_group.group_type = data["group_type"]
                legacy_group.description = data["description"]
                legacy_group.save(
                    update_fields=["name", "group_type", "description"]
                )
                continue

        ChurchGroup.objects.create(
            name=data["name"],
            group_type=data["group_type"],
            description=data["description"],
            is_active=True,
        )
        created += 1
    return created


def get_auto_youth_group():
    return ChurchGroup.objects.filter(
        group_type="youth", is_active=True
    ).order_by("pk").first()


def get_auto_women_group():
    return ChurchGroup.objects.filter(
        group_type="women", is_active=True
    ).order_by("pk").first()


def member_qualifies_for_youth(member):
    """Vijana: umri chini ya miaka 40 (kutoka date_of_birth)."""
    if not member or not member.is_active:
        return False
    if not member.date_of_birth:
        return False
    age = member.age
    return age is not None and age < YOUTH_MAX_AGE


def member_qualifies_for_women(member):
    """Akina mama: jinsia ya kike."""
    if not member or not member.is_active:
        return False
    return (member.gender or "").upper() == WOMEN_GENDER


def _apply_auto_membership(member, group, qualifies):
    """Ongeza/ondoa mwanachama wa kawaida; usiguse viongozi waliyoteuliwa."""
    if not group:
        return
    membership = GroupMembership.objects.filter(group=group, member=member).first()
    if qualifies:
        if membership:
            if membership.role in OFFICER_MEMBERSHIP_ROLES:
                if not membership.is_active:
                    membership.is_active = True
                    membership.save(update_fields=["is_active"])
                return
            membership.role = "member"
            membership.is_active = True
            membership.save(update_fields=["role", "is_active"])
        else:
            GroupMembership.objects.create(
                group=group,
                member=member,
                role="member",
                is_active=True,
            )
        return
    if membership and membership.role == "member":
        membership.is_active = False
        membership.save(update_fields=["is_active"])


@transaction.atomic
def sync_member_auto_groups(member):
    """Weka mwanachama kwenye Vijana / Akina Mama kulingana na umri na jinsia."""
    if not member or not member.pk:
        return
    ensure_default_church_groups()
    youth_group = get_auto_youth_group()
    women_group = get_auto_women_group()
    _apply_auto_membership(member, youth_group, member_qualifies_for_youth(member))
    _apply_auto_membership(member, women_group, member_qualifies_for_women(member))


def sync_all_auto_group_memberships():
    """Sawazisha wanachama wote (baada ya migrate au mabadiliko ya sheria)."""
    ensure_default_church_groups()
    count = 0
    for member in ChurchUser.objects.filter(is_active=True):
        sync_member_auto_groups(member)
        count += 1
    return count


def get_group_member_ids(group):
    return list(
        group.memberships.filter(is_active=True).values_list("member_id", flat=True)
    )


@transaction.atomic
def assign_group_officer(group, role, member=None):
    """
    role: leader | secretary | accountant
    Updates group FK and membership row.
    """
    membership_role = role
    if role == "leader":
        group.leader = member
        field = "leader"
    elif role == "secretary":
        group.secretary = member
        field = "secretary"
    elif role == "accountant":
        group.accountant = member
        field = "accountant"
    else:
        raise ValueError(f"Unknown officer role: {role}")

    group.save(update_fields=[field])

    if member:
        GroupMembership.objects.update_or_create(
            group=group,
            member=member,
            defaults={"role": membership_role, "is_active": True},
        )
    else:
        GroupMembership.objects.filter(group=group, role=membership_role).update(
            is_active=False
        )

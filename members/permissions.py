COMMUNICATION_ROLES = frozenset({'pastor', 'admin', 'secretary'})
ANNOUNCEMENT_ROLES = frozenset({'pastor', 'admin'})
DONATION_NOTICE_ROLES = frozenset({'pastor', 'admin', 'secretary'})
APPOINT_SECRETARY_ROLES = frozenset({'pastor', 'admin'})


def _role(user):
    if not user or not getattr(user, 'is_authenticated', False):
        return None
    return getattr(user, 'role', None)


def is_church_admin(user):
    return _role(user) == 'admin'


def is_verified_pastor(user):
    return _role(user) == 'pastor' and bool(getattr(user, 'is_verified_pastor', False))


def has_church_leadership(user):
    """Admin or pastor who has been approved."""
    return is_church_admin(user) or is_verified_pastor(user)


def can_promote_to_pastor(user):
    """Only admin or an already verified pastor may appoint pastors."""
    return is_church_admin(user) or is_verified_pastor(user)


def can_promote_to_admin(user):
    """Only church administrators may grant admin role."""
    return is_church_admin(user) or bool(getattr(user, 'is_superuser', False))


def can_manage_church_communications(user):
    """Pastor, admin, or church secretary may send messages to members."""
    if _role(user) == 'secretary':
        return True
    return has_church_leadership(user)


def can_create_church_announcements(user):
    """Public announcements: verified pastor or admin only."""
    return has_church_leadership(user)


def can_publish_donation_notice(user):
    """Donation notices: leadership, secretary, or accountant with access."""
    if _role(user) in DONATION_NOTICE_ROLES:
        if _role(user) == 'pastor':
            return is_verified_pastor(user)
        return True
    return (
        _role(user) == 'accountant'
        and bool(getattr(user, 'can_post_member_donations', False))
    )


def can_appoint_secretary(user):
    return has_church_leadership(user)


def can_manage_members(user):
    """Verified pastor or admin: member list, activate/deactivate, reset passwords."""
    return has_church_leadership(user)

"""Duplicate registration checks for public member signup."""

from __future__ import annotations

from .models import ChurchUser


def normalize_phone(phone: str) -> str:
    """Last 9 digits for TZ-style numbers (+255 / 0 prefix)."""
    digits = ''.join(c for c in (phone or '') if c.isdigit())
    if len(digits) >= 9:
        return digits[-9:]
    return digits


def member_with_email_exists(email: str) -> bool:
    email = (email or '').strip()
    if not email:
        return False
    return ChurchUser.objects.filter(email__iexact=email).exists()


def member_with_phone_exists(phone: str) -> bool:
    target = normalize_phone(phone)
    if len(target) < 9:
        return False
    for existing in ChurchUser.objects.exclude(phone_number='').values_list('phone_number', flat=True):
        if normalize_phone(existing) == target:
            return True
    return False


def member_with_identity_exists(*, first_name: str, last_name: str, date_of_birth) -> bool:
    fn = (first_name or '').strip()
    ln = (last_name or '').strip()
    if not fn or not ln or not date_of_birth:
        return False
    return ChurchUser.objects.filter(
        first_name__iexact=fn,
        last_name__iexact=ln,
        date_of_birth=date_of_birth,
    ).exists()

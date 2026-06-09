"""Wanafunzi wa chuo — utambuzi wa kiotomatiki wa waliohitimu."""

from django.db.models import F, Q
from django.utils import timezone

from .models import UniversityStudentRecord

# Masomo kwa kawaida huanza na kuisha mwezi wa 11 (Novemba).
ACADEMIC_GRADUATION_MONTH = 11


def graduation_season_has_ended(expected_completion_year, reference_date=None):
    """
    Je, mwanafunzi tayari amepita msimu wa kuhitimu?

    Mfano: expected_completion_year=2026 → anabaki \"anasoma\" hadi Novemba 2026,
    kisha anaweza kuwekwa \"amehitimu\" kuanzia Desemba 2026 (au mwaka unaofuata).
    """
    if not expected_completion_year:
        return False
    ref = reference_date or timezone.localdate()
    if ref.year > expected_completion_year:
        return True
    if ref.year == expected_completion_year and ref.month > ACADEMIC_GRADUATION_MONTH:
        return True
    return False


def _graduation_due_query(reference_date):
    """Q filter: wanafunzi ambao msimu wa kuhitimu umekwisha."""
    year = reference_date.year
    month = reference_date.month
    due = Q(expected_completion_year__lt=year)
    if month > ACADEMIC_GRADUATION_MONTH:
        due |= Q(expected_completion_year=year)
    return due


def promote_due_university_graduates(reference_date=None):
    """
    Weka status=completed kwa wanafunzi ambao mwaka wa kutarajiwa kuhitimu umekwisha
    (baada ya mwezi wa 11 wa mwaka huo).

    Mwanafunzi anabaki kwenye orodha ya waliohitimu; rekodi haifutwi.
    """
    ref = reference_date or timezone.localdate()
    return UniversityStudentRecord.objects.filter(
        status="studying",
        expected_completion_year__isnull=False,
    ).filter(_graduation_due_query(ref)).update(
        status="completed",
        year_completed=F("expected_completion_year"),
        updated_at=timezone.now(),
    )

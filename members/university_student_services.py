"""Wanafunzi wa chuo — utambuzi wa kiotomatiki wa waliohitimu na mwaka wa mwisho."""

from django.db.models import F, Q
from django.utils import timezone

from .models import UniversityStudentRecord

# Masomo kwa kawaida huanza na kuisha mwezi wa 11 (Novemba).
ACADEMIC_GRADUATION_MONTH = 11

# Muda wa masomo (miaka) kutoka mwaka wa kuanza hadi kuhitimu Novemba.
LEVEL_DURATION_YEARS = {
    "certificate": 1,
    "diploma": 2,
    "degree": 3,
    "masters": 2,
    "phd": 4,
    "other": 3,
}


def infer_expected_completion_year(record):
    """Kokotoa mwaka wa kuhitimu kutoka mwaka wa kuanza + kiwango cha elimu."""
    if not record.year_started:
        return None
    duration = LEVEL_DURATION_YEARS.get(record.level, 3)
    return record.year_started + duration


def effective_completion_year(record):
    """Mwaka wa kuhitimu uliotumika (uliyojazwa au ukokotwaji)."""
    if record.expected_completion_year:
        return record.expected_completion_year
    return infer_expected_completion_year(record)


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


def backfill_missing_completion_years():
    """
    Jaza expected_completion_year kwa rekodi zisizokuwa na mwaka wa kuhitimu
    lakini zina mwaka wa kuanza (kutoka kiwango cha elimu).
    """
    updated = 0
    candidates = UniversityStudentRecord.objects.filter(
        expected_completion_year__isnull=True,
        year_started__isnull=False,
    )
    for record in candidates.iterator():
        inferred = infer_expected_completion_year(record)
        if not inferred:
            continue
        record.expected_completion_year = inferred
        record.save(update_fields=["expected_completion_year", "updated_at"])
        updated += 1
    return updated


def revert_premature_graduations(reference_date=None):
    """
    Rudisha wanafunzi waliyowekwa 'amehitimu' mapema (kabla ya Novemba kuisha).
    """
    ref = reference_date or timezone.localdate()
    reverted = 0
    for record in UniversityStudentRecord.objects.filter(status="completed").iterator():
        completion = effective_completion_year(record)
        if completion and not graduation_season_has_ended(completion, ref):
            record.status = "studying"
            record.year_completed = None
            record.save(update_fields=["status", "year_completed", "updated_at"])
            reverted += 1
    return reverted


def promote_due_university_graduates(reference_date=None):
    """
    Weka status=completed kwa wanafunzi ambao mwaka wa kutarajiwa kuhitimu umekwisha
    (baada ya mwezi wa 11 wa mwaka huo).
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


def sync_university_student_records(reference_date=None):
    """Endesha backfill, rudisha waliohitimu mapema, kisha weka waliohitimu halali."""
    ref = reference_date or timezone.localdate()
    backfilled = backfill_missing_completion_years()
    reverted = revert_premature_graduations(ref)
    promoted = promote_due_university_graduates(ref)
    return {
        "backfilled": backfilled,
        "reverted": reverted,
        "promoted": promoted,
    }

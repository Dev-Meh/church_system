"""Wanafunzi wa chuo — utambuzi wa kiotomatiki wa waliohitimu."""

from django.db.models import F
from django.utils import timezone

from .models import UniversityStudentRecord


def promote_due_university_graduates(reference_year=None):
    """
    Weka status=completed kwa wanafunzi ambao mwaka wa kutarajiwa kuhitimu umefika.

    Mwanafunzi anabaki kwenye orodha ya waliohitimu; rekodi haifutwi.
    """
    year = reference_year if reference_year is not None else timezone.now().year
    return UniversityStudentRecord.objects.filter(
        status="studying",
        expected_completion_year__isnull=False,
        expected_completion_year__lte=year,
    ).update(
        status="completed",
        year_completed=F("expected_completion_year"),
        updated_at=timezone.now(),
    )

"""Create default PHM-ARCC church groups (Vijana na Akina Mama)."""

from django.core.management.base import BaseCommand

from members.group_services import (
    AUTO_CHURCH_GROUPS,
    YOUTH_MAX_AGE,
    WOMEN_GENDER,
    ensure_default_church_groups,
    sync_all_auto_group_memberships,
)


class Command(BaseCommand):
    help = "Unda makundi ya msingi na sawazisha wanachama (umri/jinsia)."

    def handle(self, *args, **options):
        created = ensure_default_church_groups()
        for data in AUTO_CHURCH_GROUPS:
            self.stdout.write(f"  · {data['name']}")
        synced = sync_all_auto_group_memberships()
        self.stdout.write(
            self.style.SUCCESS(
                f"Makundi mapya: {created}. Wanachama waliosawazishwa: {synced}. "
                f"(Vijana: chini ya miaka {YOUTH_MAX_AGE}, Akina Mama: jinsia {WOMEN_GENDER})"
            )
        )

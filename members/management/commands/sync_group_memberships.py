"""Sawazisha wanachama kwenye Vijana (<40) na Akina Mama (jinsia ya kike)."""

from django.core.management.base import BaseCommand

from members.group_services import (
    YOUTH_MAX_AGE,
    WOMEN_GENDER,
    sync_all_auto_group_memberships,
)


class Command(BaseCommand):
    help = (
        f"Weka wanachama kwenye Vijana (umri < {YOUTH_MAX_AGE}) "
        f"na Akina Mama (jinsia {WOMEN_GENDER})."
    )

    def handle(self, *args, **options):
        total = sync_all_auto_group_memberships()
        self.stdout.write(
            self.style.SUCCESS(
                f"Imekamilika. Wanachama waliosawazishwa: {total}."
            )
        )

from django.core.management.base import BaseCommand

from members.university_student_services import sync_university_student_records


class Command(BaseCommand):
    help = (
        "Sawazisha wanafunzi wa chuo: jaza mwaka wa kuhitimu, "
        "rudisha waliohitimu mapema, weka waliohitimu halali."
    )

    def handle(self, *args, **options):
        sync = sync_university_student_records()
        if any(sync.values()):
            self.stdout.write(
                self.style.SUCCESS(
                    "Imesawazishwa: "
                    f"jazwa={sync['backfilled']}, "
                    f"rudishwa={sync['reverted']}, "
                    f"hitimu={sync['promoted']}."
                )
            )
        else:
            self.stdout.write("Hakuna mabadiliko ya kusawazisha leo.")

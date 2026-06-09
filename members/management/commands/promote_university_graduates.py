from django.core.management.base import BaseCommand

from members.university_student_services import promote_due_university_graduates


class Command(BaseCommand):
    help = (
        "Weka wanafunzi wa chuo kuwa waliohitimu baada ya Novemba "
        "ya mwaka wa kutarajiwa kuhitimu."
    )

    def handle(self, *args, **options):
        count = promote_due_university_graduates()
        if count:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Wanafunzi {count} wametambuliwa kama waliohitimu."
                )
            )
        else:
            self.stdout.write("Hakuna wanafunzi waliokamilisha kipindi cha kuhitimu leo.")

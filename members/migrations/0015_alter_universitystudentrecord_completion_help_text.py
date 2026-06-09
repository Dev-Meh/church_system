from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0014_rename_youth_women_departments"),
    ]

    operations = [
        migrations.AlterField(
            model_name="universitystudentrecord",
            name="year_started",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Mwaka alipoanza masomo (kwa kawaida Novemba). Mfano: 2023.",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="universitystudentrecord",
            name="year_completed",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Mwaka alihitimu (Novemba ya mwaka huo). Mfano: 2026.",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="universitystudentrecord",
            name="expected_completion_year",
            field=models.PositiveIntegerField(
                blank=True,
                help_text=(
                    "Mwaka wa kutarajiwa kuhitimu (Novemba). "
                    "Mfano: alianza 2023, atahitimu Novemba 2026 → weka 2026."
                ),
                null=True,
            ),
        ),
    ]

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0011_message_church_group"),
    ]

    operations = [
        migrations.CreateModel(
            name="UniversityStudentRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("institution", models.CharField(max_length=200, verbose_name="Chuo / Chuo kikuu")),
                ("course", models.CharField(max_length=200, verbose_name="Kozi / Programu")),
                ("faculty", models.CharField(blank=True, max_length=200, verbose_name="Kitivo / Somo")),
                (
                    "level",
                    models.CharField(
                        choices=[
                            ("certificate", "Cheti"),
                            ("diploma", "Diploma"),
                            ("degree", "Shahada (Digrii)"),
                            ("masters", "Uzamili"),
                            ("phd", "PhD"),
                            ("other", "Nyingine"),
                        ],
                        default="degree",
                        max_length=20,
                    ),
                ),
                ("year_started", models.PositiveIntegerField(blank=True, null=True)),
                ("year_completed", models.PositiveIntegerField(blank=True, help_text="Mwaka wa kuhitimu (jaza mwanafunzi anapomaliza).", null=True)),
                ("expected_completion_year", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("studying", "Anasoma"),
                            ("completed", "Amehitimu"),
                            ("paused", "Amesimama"),
                        ],
                        default="studying",
                        max_length=20,
                    ),
                ),
                ("notes", models.TextField(blank=True, help_text="Maelezo ya ziada kwa mchungaji.")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "member",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="university_records",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "recorded_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="university_records_recorded",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Rekodi ya Mwanafunzi wa Chuo",
                "verbose_name_plural": "Wanafunzi wa Chuo",
                "ordering": ["-updated_at"],
            },
        ),
    ]

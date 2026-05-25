import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0009_churchgroup_officers'),
        ('donations', '0006_cashbookentry'),
    ]

    operations = [
        migrations.AddField(
            model_name='donation',
            name='recorded_for_group',
            field=models.ForeignKey(
                blank=True,
                help_text='Kundi linalohusika (mhasibu wa kundi).',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='recorded_donations',
                to='members.churchgroup',
            ),
        ),
    ]

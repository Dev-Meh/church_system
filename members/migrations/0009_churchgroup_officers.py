import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0008_expand_church_group_types'),
    ]

    operations = [
        migrations.AddField(
            model_name='churchgroup',
            name='accountant',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='accountant_church_groups',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Mhasibu wa kundi',
            ),
        ),
        migrations.AddField(
            model_name='churchgroup',
            name='secretary',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='secretary_church_groups',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Katibu wa kundi',
            ),
        ),
        migrations.AlterField(
            model_name='groupmembership',
            name='role',
            field=models.CharField(
                choices=[
                    ('leader', 'Kiongozi'),
                    ('assistant', 'Msaidizi'),
                    ('secretary', 'Katibu'),
                    ('accountant', 'Mhasibu'),
                    ('member', 'Mwanachama'),
                ],
                default='member',
                max_length=20,
            ),
        ),
    ]

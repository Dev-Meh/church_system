from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0006_churchuser_can_post_member_donations'),
    ]

    operations = [
        migrations.AlterField(
            model_name='churchuser',
            name='role',
            field=models.CharField(
                choices=[
                    ('member', 'Church Member'),
                    ('pastor', 'Pastor'),
                    ('secretary', 'Church Secretary'),
                    ('elder', 'Church Elder'),
                    ('deacon', 'Deacon'),
                    ('accountant', 'Accountant'),
                    ('admin', 'Administrator'),
                ],
                default='member',
                max_length=20,
            ),
        ),
    ]

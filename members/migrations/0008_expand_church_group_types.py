from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0007_churchuser_secretary_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='churchgroup',
            name='group_type',
            field=models.CharField(
                choices=[
                    ('youth', 'Vijana'),
                    ('women', 'Akina Mama'),
                    ('choir', 'Kwaya'),
                    ('men', 'Akina Baba'),
                    ('elders', 'Wazee'),
                    ('children', 'Watoto'),
                    ('worship', 'Ibada / Worship'),
                    ('other', 'Kundi Lingine'),
                ],
                max_length=20,
            ),
        ),
    ]

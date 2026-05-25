from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0009_churchgroup_officers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='churchgroup',
            name='leader',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                related_name='led_church_groups',
                to='members.churchuser',
                verbose_name='Mwenyekiti wa kundi',
            ),
        ),
        migrations.AlterField(
            model_name='groupmembership',
            name='role',
            field=models.CharField(
                choices=[
                    ('leader', 'Mwenyekiti'),
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

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('donations', '0004_donationnotice'),
    ]

    operations = [
        migrations.AddField(
            model_name='donation',
            name='tithe_asset_description',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='donation',
            name='tithe_gift_type',
            field=models.CharField(
                choices=[('money', 'Pesa'), ('asset', 'Mali')],
                default='money',
                max_length=10,
            ),
        ),
    ]

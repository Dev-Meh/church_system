from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0006_churchuser_can_post_member_donations'),
        ('donations', '0005_donation_tithe_gift_type_and_asset_description'),
    ]

    operations = [
        migrations.CreateModel(
            name='CashBookEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('entry_date', models.DateField(default=django.utils.timezone.now)),
                ('entry_type', models.CharField(choices=[('dr', 'Kuweka (DR)'), ('cr', 'Kutoa (CR)')], max_length=2)),
                ('description', models.CharField(max_length=255)),
                ('cash_amount', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('bank_amount', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cash_book_entries', to='members.churchuser')),
            ],
            options={
                'verbose_name': 'Cash Book Entry',
                'verbose_name_plural': 'Cash Book Entries',
                'ordering': ['-entry_date', '-created_at'],
            },
        ),
    ]

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0006_churchuser_can_post_member_donations'),
        ('donations', '0003_donation_contribution_date_donation_donation_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='DonationNotice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=180)),
                ('message', models.TextField()),
                ('start_date', models.DateField(default=django.utils.timezone.now)),
                ('end_date', models.DateField()),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_donation_notices', to='members.churchuser')),
                ('target_member', models.ForeignKey(blank=True, help_text='Leave blank to show to all members.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='donation_notices', to='members.churchuser')),
            ],
            options={
                'verbose_name': 'Donation Notice',
                'verbose_name_plural': 'Donation Notices',
                'ordering': ['-created_at'],
            },
        ),
    ]

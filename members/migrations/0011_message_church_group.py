from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0010_rename_leader_label_mwenyekiti"),
    ]

    operations = [
        migrations.AddField(
            model_name="message",
            name="church_group",
            field=models.ForeignKey(
                blank=True,
                help_text="Matangazo ya idara; tupu = kanisa zima",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="messages",
                to="members.churchgroup",
            ),
        ),
    ]

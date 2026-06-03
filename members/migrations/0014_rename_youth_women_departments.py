from django.db import migrations, models


def rename_default_departments(apps, schema_editor):
    ChurchGroup = apps.get_model("members", "ChurchGroup")
    renames = {
        "youth": {
            "old_names": ("Kundi la Vijana PHM-ARCC",),
            "new_name": "Idara ya Vijana (CFD'S)",
            "description": (
                "Idara ya vijana wa kanisa — shughuli, mafundisho, na huduma."
            ),
        },
        "women": {
            "old_names": ("Kundi la Akina Mama PHM-ARCC",),
            "new_name": "Idara ya Wanawake (WWM)",
            "description": "Idara ya wanawake — maombi, huduma, na mikutano.",
        },
    }
    for group_type, data in renames.items():
        group = ChurchGroup.objects.filter(group_type=group_type).first()
        if not group:
            for old_name in data["old_names"]:
                group = ChurchGroup.objects.filter(name=old_name).first()
                if group:
                    break
        if group:
            group.name = data["new_name"]
            group.group_type = group_type
            group.description = data["description"]
            group.save(update_fields=["name", "group_type", "description"])


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0013_alter_universitystudentrecord_faculty"),
    ]

    operations = [
        migrations.AlterField(
            model_name="churchgroup",
            name="group_type",
            field=models.CharField(
                choices=[
                    ("youth", "Idara ya Vijana (CFD'S)"),
                    ("women", "Idara ya Wanawake (WWM)"),
                    ("choir", "Kwaya"),
                    ("men", "Akina Baba"),
                    ("elders", "Wazee"),
                    ("children", "Watoto"),
                    ("worship", "Ibada / Worship"),
                    ("other", "Kundi Lingine"),
                ],
                max_length=20,
            ),
        ),
        migrations.RunPython(rename_default_departments, migrations.RunPython.noop),
    ]

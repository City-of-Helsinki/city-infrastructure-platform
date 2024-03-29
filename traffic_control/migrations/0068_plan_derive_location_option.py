# Generated by Django 3.2.20 on 2023-08-17 13:44

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("traffic_control", "0067_plan_diary_number_and_drawing_number"),
    ]

    operations = [
        # To avoid breaking behavior of pre-existing Plans, we set derive_location = True
        migrations.AddField(
            model_name="plan",
            name="derive_location",
            field=models.BooleanField(
                default=True,
                help_text="Derive the plan location (geometry area) from the locations of related devices. Enable this if the plan does not have a predefined location.",
                verbose_name="Derive location from devices",
            ),
        ),
        # Set derive_location = False as default for new Plans
        migrations.AlterField(
            model_name="plan",
            name="derive_location",
            field=models.BooleanField(
                default=False,
                help_text="Derive the plan location (geometry area) from the locations of related devices. Enable this if the plan does not have a predefined location.",
                verbose_name="Derive location from devices",
            ),
        ),
    ]

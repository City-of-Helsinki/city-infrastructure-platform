from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("traffic_control", "0069_plan_multiple_drawing_numbers"),
    ]

    operations = [
        migrations.RenameField(
            model_name="plan",
            old_name="plan_number",
            new_name="decision_id",
        ),
        migrations.AlterField(
            model_name="plan",
            name="decision_id",
            field=models.CharField(
                help_text="Year and verdict section separated with a dash",
                max_length=16,
                verbose_name="Decision id",
            ),
        ),
    ]

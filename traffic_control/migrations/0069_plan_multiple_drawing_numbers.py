import django.contrib.postgres.fields
import django.core.validators
from django.db import migrations, models


def to_drawing_numbers(apps, schema_editor):
    plan_model = apps.get_model("traffic_control", "Plan")
    db_alias = schema_editor.connection.alias

    plans = plan_model.objects.using(db_alias).all()

    for plan in plans:
        if plan.drawing_number is not None:
            numbers = plan.drawing_number.split(",")
            plan.drawing_numbers = [number.strip() for number in numbers]
            plan.save()


def reverse_drawing_numbers(apps, schema_editor):
    plan_model = apps.get_model("traffic_control", "Plan")
    db_alias = schema_editor.connection.alias

    plans = plan_model.objects.using(db_alias).all()

    for plan in plans:
        if plan.drawing_numbers is not None and len(plan.drawing_numbers) > 0:
            plan.drawing_number = ",".join(plan.drawing_numbers)
            plan.save()


class Migration(migrations.Migration):
    dependencies = [
        ("traffic_control", "0068_plan_derive_location_option"),
    ]

    operations = [
        migrations.AddField(
            model_name="plan",
            name="drawing_numbers",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(
                    max_length=20,
                    validators=[
                        django.core.validators.RegexValidator(
                            "^[a-zA-Z0-9-_ ]+$", "A drawing number must not contain special characters"
                        ),
                    ],
                ),
                blank=True,
                default=list,
                help_text="Drawing numbers related to the plan separated with a comma",
                size=100,
                verbose_name="Drawing numbers",
            ),
        ),
        migrations.RunPython(to_drawing_numbers, reverse_drawing_numbers),
        migrations.RemoveField(
            model_name="plan",
            name="drawing_number",
        ),
    ]

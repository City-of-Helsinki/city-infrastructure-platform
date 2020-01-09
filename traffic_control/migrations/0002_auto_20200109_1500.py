# Generated by Django 3.0.1 on 2020-01-09 13:00

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("traffic_control", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="trafficsignreal",
            name="created_by",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="created_by_traffic_sign_real_set",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="trafficsignreal",
            name="deleted_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="deleted_by_traffic_sign_real_set",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="trafficsignreal",
            name="lifecycle",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="traffic_control.Lifecycle",
            ),
        ),
        migrations.AddField(
            model_name="trafficsignreal",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="traffic_control.TrafficSignReal",
            ),
        ),
        migrations.AddField(
            model_name="trafficsignreal",
            name="traffic_sign_plan",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="traffic_control.TrafficSignPlan",
            ),
        ),
        migrations.AddField(
            model_name="trafficsignreal",
            name="updated_by",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="updated_by_traffic_sign_real_set",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="trafficsignplan",
            name="code",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="traffic_control.TrafficSignCode",
            ),
        ),
        migrations.AddField(
            model_name="trafficsignplan",
            name="created_by",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="created_by_traffic_sign_plan_set",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="trafficsignplan",
            name="deleted_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="deleted_by_traffic_sign_plan_set",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="trafficsignplan",
            name="lifecycle",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="traffic_control.Lifecycle",
            ),
        ),
        migrations.AddField(
            model_name="trafficsignplan",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="traffic_control.TrafficSignPlan",
            ),
        ),
        migrations.AddField(
            model_name="trafficsignplan",
            name="updated_by",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="updated_by_traffic_sign_plan_set",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]

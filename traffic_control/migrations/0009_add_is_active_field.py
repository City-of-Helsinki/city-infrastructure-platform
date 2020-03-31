# Generated by Django 2.2.10 on 2020-03-30 12:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("traffic_control", "0008_update_traffic_sign_real"),
    ]

    operations = [
        migrations.AddField(
            model_name="barrierplan",
            name="is_active",
            field=models.BooleanField(default=True, verbose_name="Active"),
        ),
        migrations.AddField(
            model_name="barrierreal",
            name="is_active",
            field=models.BooleanField(default=True, verbose_name="Active"),
        ),
        migrations.AddField(
            model_name="mountplan",
            name="is_active",
            field=models.BooleanField(default=True, verbose_name="Active"),
        ),
        migrations.AddField(
            model_name="mountreal",
            name="is_active",
            field=models.BooleanField(default=True, verbose_name="Active"),
        ),
        migrations.AddField(
            model_name="roadmarkingplan",
            name="is_active",
            field=models.BooleanField(default=True, verbose_name="Active"),
        ),
        migrations.AddField(
            model_name="roadmarkingreal",
            name="is_active",
            field=models.BooleanField(default=True, verbose_name="Active"),
        ),
        migrations.AddField(
            model_name="signpostplan",
            name="is_active",
            field=models.BooleanField(default=True, verbose_name="Active"),
        ),
        migrations.AddField(
            model_name="signpostreal",
            name="is_active",
            field=models.BooleanField(default=True, verbose_name="Active"),
        ),
        migrations.AddField(
            model_name="trafficlightplan",
            name="is_active",
            field=models.BooleanField(default=True, verbose_name="Active"),
        ),
        migrations.AddField(
            model_name="trafficlightreal",
            name="is_active",
            field=models.BooleanField(default=True, verbose_name="Active"),
        ),
        migrations.AddField(
            model_name="trafficsignplan",
            name="is_active",
            field=models.BooleanField(default=True, verbose_name="Active"),
        ),
        migrations.AddField(
            model_name="trafficsignreal",
            name="is_active",
            field=models.BooleanField(default=True, verbose_name="Active"),
        ),
    ]

# Generated by Django 2.2.14 on 2020-08-05 12:26

import django.contrib.gis.db.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("traffic_control", "0017_operational_area"),
    ]

    operations = [
        migrations.AlterField(
            model_name="plan",
            name="location",
            field=django.contrib.gis.db.models.fields.MultiPolygonField(
                blank=True, null=True, srid=3879, verbose_name="Location (2D)"
            ),
        ),
    ]

# Generated by Django 2.2.13 on 2020-07-03 07:51

import enumfields.fields
from django.db import migrations, models

import traffic_control.enums
import traffic_control.models.additional_sign
import traffic_control.models.common
import traffic_control.models.traffic_sign


class Migration(migrations.Migration):

    dependencies = [
        ("traffic_control", "0009_add_road_marking_source_id_source_name"),
    ]

    operations = [
        migrations.RenameField(
            model_name="trafficsignreal",
            old_name="allu_decision_id",
            new_name="permit_decision_id",
        ),
        migrations.AlterField(
            model_name="trafficsignplan",
            name="height",
            field=models.IntegerField(blank=True, null=True, verbose_name="Height"),
        ),
        migrations.AlterField(
            model_name="trafficsignreal",
            name="color",
            field=enumfields.fields.EnumIntegerField(
                blank=True,
                default=1,
                enum=traffic_control.models.additional_sign.Color,
                null=True,
                verbose_name="Color",
            ),
        ),
        migrations.AlterField(
            model_name="trafficsignreal",
            name="height",
            field=models.IntegerField(blank=True, null=True, verbose_name="Height"),
        ),
        migrations.AlterField(
            model_name="trafficsignreal",
            name="location_specifier",
            field=enumfields.fields.EnumIntegerField(
                blank=True,
                default=1,
                enum=traffic_control.models.traffic_sign.LocationSpecifier,
                null=True,
                verbose_name="Location specifier",
            ),
        ),
    ]

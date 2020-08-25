# Generated by Django 2.2.13 on 2020-06-26 12:57

import enumfields.fields
from django.db import migrations

import traffic_control.models.common


class Migration(migrations.Migration):

    dependencies = [
        ("traffic_control", "0004_device_type_target_model"),
    ]

    operations = [
        migrations.AddField(
            model_name="trafficcontroldevicetype",
            name="type",
            field=enumfields.fields.EnumField(
                blank=True,
                enum=traffic_control.models.common.TrafficControlDeviceTypeType,
                max_length=50,
                null=True,
                verbose_name="Type",
            ),
        ),
    ]

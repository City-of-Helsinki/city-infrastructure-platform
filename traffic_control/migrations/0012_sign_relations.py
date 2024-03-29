# Generated by Django 2.2.13 on 2020-07-06 06:40

import django.db.models.deletion
from django.db import migrations, models

import traffic_control.enums
import traffic_control.models.common


class Migration(migrations.Migration):

    dependencies = [
        ("traffic_control", "0011_update_additional_traffic_sign_models"),
    ]

    operations = [
        migrations.AddField(
            model_name="additionalsignplan",
            name="mount_plan",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="traffic_control.MountPlan",
                verbose_name="Mount Plan",
            ),
        ),
        migrations.AddField(
            model_name="additionalsignplan",
            name="mount_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="traffic_control.MountType",
                verbose_name="Mount type",
            ),
        ),
        migrations.AddField(
            model_name="additionalsignreal",
            name="mount_real",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="traffic_control.MountReal",
                verbose_name="Mount Real",
            ),
        ),
        migrations.AddField(
            model_name="additionalsignreal",
            name="mount_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="traffic_control.MountType",
                verbose_name="Mount type",
            ),
        ),
        migrations.AlterField(
            model_name="additionalsigncontentplan",
            name="device_type",
            field=models.ForeignKey(
                limit_choices_to=models.Q(
                    models.Q(
                        ("target_model", None),
                        (
                            "target_model",
                            traffic_control.enums.DeviceTypeTargetModel(
                                "traffic_sign"
                            ),
                        ),
                        _connector="OR",
                    )
                ),
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="traffic_control.TrafficControlDeviceType",
                verbose_name="Device type",
            ),
        ),
        migrations.AlterField(
            model_name="additionalsigncontentreal",
            name="device_type",
            field=models.ForeignKey(
                limit_choices_to=models.Q(
                    models.Q(
                        ("target_model", None),
                        (
                            "target_model",
                            traffic_control.enums.DeviceTypeTargetModel(
                                "traffic_sign"
                            ),
                        ),
                        _connector="OR",
                    )
                ),
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="traffic_control.TrafficControlDeviceType",
                verbose_name="Device type",
            ),
        ),
        migrations.AlterField(
            model_name="trafficsignreal",
            name="device_type",
            field=models.ForeignKey(
                limit_choices_to=models.Q(
                    models.Q(
                        ("target_model", None),
                        (
                            "target_model",
                            traffic_control.enums.DeviceTypeTargetModel(
                                "traffic_sign"
                            ),
                        ),
                        _connector="OR",
                    )
                ),
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="traffic_control.TrafficControlDeviceType",
                verbose_name="Device type",
            ),
        ),
    ]

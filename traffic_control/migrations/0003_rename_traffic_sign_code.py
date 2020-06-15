# Generated by Django 2.2.13 on 2020-06-12 10:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("traffic_control", "0002_on_delete_rules"),
    ]

    operations = [
        migrations.RenameField(
            model_name="BarrierPlan", old_name="type", new_name="device_type"
        ),
        migrations.RenameField(
            model_name="BarrierReal", old_name="type", new_name="device_type"
        ),
        migrations.RenameField(
            model_name="RoadMarkingPlan", old_name="code", new_name="device_type"
        ),
        migrations.RenameField(
            model_name="RoadMarkingReal", old_name="code", new_name="device_type"
        ),
        migrations.RenameField(
            model_name="SignpostPlan", old_name="code", new_name="device_type"
        ),
        migrations.RenameField(
            model_name="SignpostReal", old_name="code", new_name="device_type"
        ),
        migrations.RenameField(
            model_name="TrafficLightPlan", old_name="code", new_name="device_type"
        ),
        migrations.RenameField(
            model_name="TrafficLightReal", old_name="code", new_name="device_type"
        ),
        migrations.RenameField(
            model_name="TrafficSignPlan", old_name="code", new_name="device_type"
        ),
        migrations.RenameField(
            model_name="TrafficSignReal", old_name="code", new_name="device_type"
        ),
        migrations.RenameModel(
            old_name="TrafficSignCode", new_name="TrafficControlDeviceType"
        ),
        migrations.AlterModelOptions(
            name="TrafficControlDeviceType",
            options={
                "verbose_name": "Traffic Control Device Type",
                "verbose_name_plural": "Traffic Control Device Types",
            },
        ),
        migrations.AlterField(
            model_name="BarrierPlan",
            name="device_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="traffic_control.TrafficControlDeviceType",
                verbose_name="Device type",
            ),
        ),
        migrations.AlterField(
            model_name="BarrierReal",
            name="device_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="traffic_control.TrafficControlDeviceType",
                verbose_name="Device type",
            ),
        ),
        migrations.AlterField(
            model_name="RoadMarkingPlan",
            name="device_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="traffic_control.TrafficControlDeviceType",
                verbose_name="Device Type",
            ),
        ),
        migrations.AlterField(
            model_name="RoadMarkingReal",
            name="device_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="traffic_control.TrafficControlDeviceType",
                verbose_name="Device type",
            ),
        ),
        migrations.AlterField(
            model_name="SignpostPlan",
            name="device_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="traffic_control.TrafficControlDeviceType",
                verbose_name="Device type",
            ),
        ),
        migrations.AlterField(
            model_name="SignpostReal",
            name="device_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="traffic_control.TrafficControlDeviceType",
                verbose_name="Device type",
            ),
        ),
        migrations.AlterField(
            model_name="TrafficLightPlan",
            name="device_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="traffic_control.TrafficControlDeviceType",
                verbose_name="Device type",
            ),
        ),
        migrations.AlterField(
            model_name="TrafficLightReal",
            name="device_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="traffic_control.TrafficControlDeviceType",
                verbose_name="Device type",
            ),
        ),
        migrations.AlterField(
            model_name="TrafficSignPlan",
            name="device_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="traffic_control.TrafficControlDeviceType",
                verbose_name="Device type",
            ),
        ),
        migrations.AlterField(
            model_name="TrafficSignReal",
            name="device_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="traffic_control.TrafficControlDeviceType",
                verbose_name="Device type",
            ),
        ),
        migrations.AlterModelTable(
            name="TrafficControlDeviceType", table="traffic_control_device_type",
        ),
    ]

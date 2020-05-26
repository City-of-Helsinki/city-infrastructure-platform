# Generated by Django 2.2.12 on 2020-05-26 06:27

from django.db import migrations
import enumfields.fields
import traffic_control.models.traffic_light


class Migration(migrations.Migration):

    dependencies = [
        ("traffic_control", "0012_lane_enums"),
    ]

    operations = [
        migrations.AddField(
            model_name="trafficlightplan",
            name="push_button",
            field=enumfields.fields.EnumIntegerField(
                blank=True,
                enum=traffic_control.models.traffic_light.PushButton,
                null=True,
                verbose_name="Push button",
            ),
        ),
        migrations.AddField(
            model_name="trafficlightplan",
            name="vehicle_recognition",
            field=enumfields.fields.EnumIntegerField(
                blank=True,
                enum=traffic_control.models.traffic_light.VehicleRecognition,
                null=True,
                verbose_name="Vehicle recognition",
            ),
        ),
        migrations.AddField(
            model_name="trafficlightreal",
            name="push_button",
            field=enumfields.fields.EnumIntegerField(
                blank=True,
                enum=traffic_control.models.traffic_light.PushButton,
                null=True,
                verbose_name="Push button",
            ),
        ),
        migrations.AddField(
            model_name="trafficlightreal",
            name="vehicle_recognition",
            field=enumfields.fields.EnumIntegerField(
                blank=True,
                enum=traffic_control.models.traffic_light.VehicleRecognition,
                null=True,
                verbose_name="Vehicle recognition",
            ),
        ),
        migrations.AlterField(
            model_name="trafficlightplan",
            name="type",
            field=enumfields.fields.EnumField(
                blank=True,
                enum=traffic_control.models.traffic_light.TrafficLightType,
                max_length=10,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="trafficlightreal",
            name="type",
            field=enumfields.fields.EnumField(
                blank=True,
                enum=traffic_control.models.traffic_light.TrafficLightType,
                max_length=10,
                null=True,
            ),
        ),
    ]
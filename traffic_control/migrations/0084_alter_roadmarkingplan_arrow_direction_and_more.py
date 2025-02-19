# Generated by Django 4.2.15 on 2024-10-14 09:23

from django.db import migrations
import enumfields.fields
import traffic_control.models.road_marking


class Migration(migrations.Migration):

    dependencies = [
        ('traffic_control', '0083_additionalsignreal_traffic_control_additionalsignreal_unique_additional_sign_plan_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='roadmarkingplan',
            name='arrow_direction',
            field=enumfields.fields.EnumIntegerField(blank=True, enum=traffic_control.models.road_marking.ArrowDirection, help_text='Direction of the arrow on the road.', null=True, verbose_name='Arrow direction'),
        ),
        migrations.AlterField(
            model_name='roadmarkingreal',
            name='arrow_direction',
            field=enumfields.fields.EnumIntegerField(blank=True, enum=traffic_control.models.road_marking.ArrowDirection, help_text='Direction of the arrow on the road.', null=True, verbose_name='Arrow direction'),
        ),
    ]

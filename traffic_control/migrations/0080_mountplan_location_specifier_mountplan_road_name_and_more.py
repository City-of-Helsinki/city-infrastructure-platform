# Generated by Django 4.2.15 on 2024-08-29 13:39

from django.db import migrations, models
import enumfields.fields
import traffic_control.models.mount


class Migration(migrations.Migration):

    dependencies = [
        ('traffic_control', '0079_additionalsignrealfile_additionalsignplanfile'),
    ]

    operations = [
        migrations.AddField(
            model_name='mountplan',
            name='location_specifier',
            field=enumfields.fields.EnumIntegerField(blank=True, enum=traffic_control.models.mount.LocationSpecifier, help_text='Specifies where the mount is in relation to the road.', null=True, verbose_name='Location specifier'),
        ),
        migrations.AddField(
            model_name='mountplan',
            name='road_name',
            field=models.CharField(blank=True, help_text='Name of the road this mount is installed at.', max_length=254, null=True, verbose_name='Road name'),
        ),
        migrations.AddField(
            model_name='mountreal',
            name='location_specifier',
            field=enumfields.fields.EnumIntegerField(blank=True, enum=traffic_control.models.mount.LocationSpecifier, help_text='Specifies where the mount is in relation to the road.', null=True, verbose_name='Location specifier'),
        ),
        migrations.AddField(
            model_name='mountreal',
            name='road_name',
            field=models.CharField(blank=True, help_text='Name of the road this mount is installed at.', max_length=254, null=True, verbose_name='Road name'),
        ),
        migrations.AddField(
            model_name='mountreal',
            name='scanned_at',
            field=models.DateTimeField(blank=True, help_text='Date and time on which this mount was last scanned at.', null=True, verbose_name='Scanned at'),
        ),
        migrations.AddField(
            model_name='signpostreal',
            name='scanned_at',
            field=models.DateTimeField(blank=True, help_text='Date and time on which this signpost was last scanned at.', null=True, verbose_name='Scanned at'),
        ),
    ]

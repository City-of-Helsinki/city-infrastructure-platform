# Generated by Django 3.2.17 on 2023-02-08 12:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('traffic_control', '0063_nullable_traffic_control_device_types'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mountplan',
            name='mount_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='traffic_control.mounttype', verbose_name='Mount type'),
        ),
        migrations.AlterField(
            model_name='mountreal',
            name='mount_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='traffic_control.mounttype', verbose_name='Mount type'),
        ),
    ]

# Generated by Django 3.2.14 on 2022-08-11 14:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('traffic_control', '0053_mount_base_null'),
    ]

    operations = [
        migrations.AlterField(
            model_name='additionalsignreal',
            name='installed_by',
            field=models.CharField(blank=True, help_text='Name of the organization who installed this sign.', max_length=254, null=True, verbose_name='Installed by'),
        ),
    ]

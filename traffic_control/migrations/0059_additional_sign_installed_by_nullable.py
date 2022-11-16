# Generated by Django 3.2.16 on 2022-11-16 16:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('traffic_control', '0058_additional_sign_migrate_device_type_value'),
    ]

    operations = [
        migrations.AlterField(
            model_name='additionalsignreal',
            name='installed_by',
            field=models.CharField(blank=True, help_text='Name of the organization who installed this sign.', max_length=254, null=True, verbose_name='Installed by'),
        ),
    ]
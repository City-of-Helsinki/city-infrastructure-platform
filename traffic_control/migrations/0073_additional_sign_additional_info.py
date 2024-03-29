# Generated by Django 3.2.22 on 2023-11-07 11:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('traffic_control', '0072_additional_sign_missing_content'),
    ]

    operations = [
        migrations.AddField(
            model_name='additionalsignplan',
            name='additional_information',
            field=models.TextField(blank=True, default='', help_text='Additional information related to this device.', verbose_name='Additional information'),
        ),
        migrations.AddField(
            model_name='additionalsignreal',
            name='additional_information',
            field=models.TextField(blank=True, default='', help_text='Additional information related to this device.', verbose_name='Additional information'),
        ),
    ]

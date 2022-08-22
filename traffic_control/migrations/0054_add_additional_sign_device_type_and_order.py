# Generated by Django 3.2.14 on 2022-08-17 12:29

from django.db import migrations, models
import django.db.models.deletion
import traffic_control.enums


class Migration(migrations.Migration):

    dependencies = [
        ('traffic_control', '0053_add_additional_sign_content_jsonfield'),
    ]

    operations = [
        migrations.AddField(
            model_name='additionalsignplan',
            name='device_type',
            field=models.ForeignKey(limit_choices_to=models.Q(models.Q(('target_model', None), ('target_model', traffic_control.enums.DeviceTypeTargetModel['ADDITIONAL_SIGN']), _connector='OR')), null=True, on_delete=django.db.models.deletion.PROTECT, to='traffic_control.trafficcontroldevicetype', verbose_name='Device type'),
        ),
        migrations.AddField(
            model_name='additionalsignplan',
            name='order',
            field=models.SmallIntegerField(default=1, help_text='The order of the sign in relation to the signs at the same point. Order from top to bottom, from left to right starting at 1.', verbose_name='Order'),
        ),
        migrations.AddField(
            model_name='additionalsignreal',
            name='device_type',
            field=models.ForeignKey(limit_choices_to=models.Q(models.Q(('target_model', None), ('target_model', traffic_control.enums.DeviceTypeTargetModel['ADDITIONAL_SIGN']), _connector='OR')), null=True, on_delete=django.db.models.deletion.PROTECT, to='traffic_control.trafficcontroldevicetype', verbose_name='Device type'),
        ),
        migrations.AddField(
            model_name='additionalsignreal',
            name='order',
            field=models.SmallIntegerField(default=1, help_text='The order of the sign in relation to the signs at the same point. Order from top to bottom, from left to right starting at 1.', verbose_name='Order'),
        ),
    ]
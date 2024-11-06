# Generated by Django 4.2.16 on 2024-11-05 10:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('traffic_control', '0086_alter_plan_decision_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='additionalsignreal',
            name='parent',
            field=models.ForeignKey(help_text='The traffic sign to which this additional sign is associated.', on_delete=django.db.models.deletion.PROTECT, related_name='additional_signs', to='traffic_control.trafficsignreal', verbose_name='Parent Traffic Sign Real'),
        ),
    ]

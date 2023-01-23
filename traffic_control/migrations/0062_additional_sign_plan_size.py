# Generated by Django 3.2.16 on 2023-01-23 09:15

from django.db import migrations
import enumfields.fields
import traffic_control.enums


class Migration(migrations.Migration):

    dependencies = [
        ('traffic_control', '0061_defaults_from_model_to_admin_form_initial_values'),
    ]

    operations = [
        migrations.AddField(
            model_name='additionalsignplan',
            name='size',
            field=enumfields.fields.EnumField(blank=True, enum=traffic_control.enums.Size, max_length=1, null=True, verbose_name='Size'),
        ),
    ]
# Generated by Django 3.2.12 on 2022-04-28 12:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('city_furniture', '0007_group_responsible_entity'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='groupresponsibleentity',
            name='group',
        ),
        migrations.RemoveField(
            model_name='groupresponsibleentity',
            name='responsible_entities',
        ),
        migrations.RemoveField(
            model_name='responsibleentity',
            name='parent',
        ),
    ]
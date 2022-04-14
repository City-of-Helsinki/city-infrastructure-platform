# Generated by Django 3.2.12 on 2022-04-13 15:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('city_furniture', '0004_responsible_entity_organization_level'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='furnituresignpostplan',
            name='project_id',
        ),
        migrations.RemoveField(
            model_name='furnituresignpostreal',
            name='project_id',
        ),
        migrations.AlterField(
            model_name='furnituresignpostplan',
            name='additional_material_url',
            field=models.CharField(blank=True, help_text='Additional material about the device. This should be publicly available.', max_length=254, null=True, verbose_name='Additional material URL'),
        ),
        migrations.AlterField(
            model_name='furnituresignpostreal',
            name='additional_material_url',
            field=models.CharField(blank=True, help_text='Additional material about the device. This should be publicly available.', max_length=254, null=True, verbose_name='Additional material URL'),
        ),
    ]
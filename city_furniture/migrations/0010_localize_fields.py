# Generated by Django 3.2.12 on 2022-05-03 13:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('city_furniture', '0009_move_responsible_entity'),
    ]

    operations = [
        migrations.RenameField(
            model_name='cityfurnituredevicetype',
            old_name='description',
            new_name='description_fi',
        ),
        migrations.RenameField(
            model_name='furnituresignpostplan',
            old_name='location_name',
            new_name='location_name_fi',
        ),
        migrations.RenameField(
            model_name='furnituresignpostreal',
            old_name='location_name',
            new_name='location_name_fi',
        ),
        migrations.AlterField(
            model_name='furnituresignpostplan',
            name='location_name_fi',
            field=models.CharField(blank=True, help_text="Verbose name for the signpost's location, e.g. street, park or island.", max_length=254, null=True, verbose_name='Finnish location name'),
        ),
        migrations.AlterField(
            model_name='furnituresignpostreal',
            name='location_name_fi',
            field=models.CharField(blank=True, help_text="Verbose name for the signpost's location, e.g. street, park or island.", max_length=254, null=True, verbose_name='Finnish location name'),
        ),
        migrations.AlterField(
            model_name='cityfurnituredevicetype',
            name='description_fi',
            field=models.CharField(blank=True, max_length=254, null=True, verbose_name='Finnish Description'),
        ),
        migrations.AddField(
            model_name='cityfurnituredevicetype',
            name='description_en',
            field=models.CharField(blank=True, max_length=254, null=True, verbose_name='English Description'),
        ),
        migrations.AddField(
            model_name='cityfurnituredevicetype',
            name='description_sw',
            field=models.CharField(blank=True, max_length=254, null=True, verbose_name='Swedish Description'),
        ),
        migrations.AddField(
            model_name='furnituresignpostplan',
            name='location_name_en',
            field=models.CharField(blank=True, max_length=254, null=True, verbose_name='English location name'),
        ),
        migrations.AddField(
            model_name='furnituresignpostplan',
            name='location_name_sw',
            field=models.CharField(blank=True, max_length=254, null=True, verbose_name='Swedish location name'),
        ),
        migrations.AddField(
            model_name='furnituresignpostreal',
            name='location_name_en',
            field=models.CharField(blank=True, max_length=254, null=True, verbose_name='English location name'),
        ),
        migrations.AddField(
            model_name='furnituresignpostreal',
            name='location_name_sw',
            field=models.CharField(blank=True, max_length=254, null=True, verbose_name='Swedish location name'),
        ),
    ]
# Generated by Django 4.2.15 on 2024-09-20 12:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('city_furniture', '0017_alter_furnituresignpostplan_created_by_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='furnituresignpostplan',
            name='height',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='The height of the sign from the ground, measured from the bottom in centimeters.', max_digits=5, null=True, verbose_name='Height'),
        ),
        migrations.AlterField(
            model_name='furnituresignpostreal',
            name='height',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='The height of the sign from the ground, measured from the bottom in centimeters.', max_digits=5, null=True, verbose_name='Height'),
        ),
    ]
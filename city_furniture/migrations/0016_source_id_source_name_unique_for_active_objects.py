# Generated by Django 3.2.23 on 2024-01-04 11:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('city_furniture', '0015_nullable_direction'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='furnituresignpostplan',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='furnituresignpostreal',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='furnituresignpostplan',
            constraint=models.UniqueConstraint(condition=models.Q(('is_active', True)), fields=('source_name', 'source_id'), name='city_furniture_furnituresignpostplan_unique_source_name_id'),
        ),
        migrations.AddConstraint(
            model_name='furnituresignpostreal',
            constraint=models.UniqueConstraint(condition=models.Q(('is_active', True)), fields=('source_name', 'source_id'), name='city_furniture_furnituresignpostreal_unique_source_name_id'),
        ),
    ]

# Generated by Django 3.2.12 on 2022-04-28 12:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('traffic_control', '0048_move_responsible_entity'),
        ('users', '0006_responsible_entity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='responsible_entities',
            field=models.ManyToManyField(blank=True, help_text="Responsible entities that this user is belongs to. This gives the users write permission to devices that belong to the Responsible Entities or any Responsible Entity that's hierarchically under the selected ones.", related_name='users', to='traffic_control.ResponsibleEntity', verbose_name='Responsible entities'),
        ),
    ]

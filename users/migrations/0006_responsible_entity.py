# Generated by Django 3.2.12 on 2022-04-19 11:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('city_furniture', '0006_responsible_entity_mptt'),
        ('users', '0005_alter_user_first_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='bypass_responsible_entity',
            field=models.BooleanField(default=False, help_text='Disable responsible entity permission checks for this user.', verbose_name='Bypass responsible entity'),
        ),
        migrations.AddField(
            model_name='user',
            name='responsible_entities',
            field=models.ManyToManyField(blank=True, help_text="Responsible entities that this user is belongs to. This gives the users write permission to devices that belong to the Responsible Entities or any Responsible Entity that's hierarchically under the selected ones.", related_name='users', to='city_furniture.ResponsibleEntity', verbose_name='Responsible entities'),
        ),
    ]

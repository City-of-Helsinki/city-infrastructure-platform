# Generated by Django 4.2.16 on 2024-12-15 15:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_help_texts'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='additional_information',
            field=models.TextField(blank=True, default='', help_text='Additional information related to this user.', verbose_name='Additional information'),
        ),
    ]

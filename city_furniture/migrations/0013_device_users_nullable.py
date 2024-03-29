# Generated by Django 3.2.18 on 2023-02-24 13:58

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('city_furniture', '0012_defaults_from_model_to_admin_form_initial_values'),
    ]

    operations = [
        migrations.AlterField(
            model_name='furnituresignpostplan',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_by_furnituresignpostplan_set', to=settings.AUTH_USER_MODEL, verbose_name='Created by'),
        ),
        migrations.AlterField(
            model_name='furnituresignpostplan',
            name='deleted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deleted_by_furnituresignpostplan_set', to=settings.AUTH_USER_MODEL, verbose_name='Deleted by'),
        ),
        migrations.AlterField(
            model_name='furnituresignpostplan',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_by_furnituresignpostplan_set', to=settings.AUTH_USER_MODEL, verbose_name='Updated by'),
        ),
        migrations.AlterField(
            model_name='furnituresignpostreal',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_by_furnituresignpostreal_set', to=settings.AUTH_USER_MODEL, verbose_name='Created by'),
        ),
        migrations.AlterField(
            model_name='furnituresignpostreal',
            name='deleted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deleted_by_furnituresignpostreal_set', to=settings.AUTH_USER_MODEL, verbose_name='Deleted by'),
        ),
        migrations.AlterField(
            model_name='furnituresignpostreal',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_by_furnituresignpostreal_set', to=settings.AUTH_USER_MODEL, verbose_name='Updated by'),
        ),
        migrations.AlterField(
            model_name='furnituresignpostrealoperation',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_by_furnituresignpostrealoperation_set', to=settings.AUTH_USER_MODEL, verbose_name='Created by'),
        ),
        migrations.AlterField(
            model_name='furnituresignpostrealoperation',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_by_furnituresignpostrealoperation_set', to=settings.AUTH_USER_MODEL, verbose_name='Updated by'),
        ),
    ]

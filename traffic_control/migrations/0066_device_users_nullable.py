# Generated by Django 3.2.18 on 2023-02-24 13:58

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('traffic_control', '0065_plan_remove_planner_and_decision_maker'),
    ]

    operations = [
        migrations.AlterField(
            model_name='additionalsignplan',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_by_additionalsignplan_set', to=settings.AUTH_USER_MODEL, verbose_name='Created by'),
        ),
        migrations.AlterField(
            model_name='additionalsignplan',
            name='deleted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deleted_by_additionalsignplan_set', to=settings.AUTH_USER_MODEL, verbose_name='Deleted by'),
        ),
        migrations.AlterField(
            model_name='additionalsignplan',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_by_additionalsignplan_set', to=settings.AUTH_USER_MODEL, verbose_name='Updated by'),
        ),
        migrations.AlterField(
            model_name='additionalsignreal',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_by_additionalsignreal_set', to=settings.AUTH_USER_MODEL, verbose_name='Created by'),
        ),
        migrations.AlterField(
            model_name='additionalsignreal',
            name='deleted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deleted_by_additionalsignreal_set', to=settings.AUTH_USER_MODEL, verbose_name='Deleted by'),
        ),
        migrations.AlterField(
            model_name='additionalsignreal',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_by_additionalsignreal_set', to=settings.AUTH_USER_MODEL, verbose_name='Updated by'),
        ),
        migrations.AlterField(
            model_name='additionalsignrealoperation',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_by_additionalsignrealoperation_set', to=settings.AUTH_USER_MODEL, verbose_name='Created by'),
        ),
        migrations.AlterField(
            model_name='additionalsignrealoperation',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_by_additionalsignrealoperation_set', to=settings.AUTH_USER_MODEL, verbose_name='Updated by'),
        ),
        migrations.AlterField(
            model_name='barrierplan',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_by_barrierplan_set', to=settings.AUTH_USER_MODEL, verbose_name='Created by'),
        ),
        migrations.AlterField(
            model_name='barrierplan',
            name='deleted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deleted_by_barrierplan_set', to=settings.AUTH_USER_MODEL, verbose_name='Deleted by'),
        ),
        migrations.AlterField(
            model_name='barrierplan',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_by_barrierplan_set', to=settings.AUTH_USER_MODEL, verbose_name='Updated by'),
        ),
        migrations.AlterField(
            model_name='barrierreal',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_by_barrierreal_set', to=settings.AUTH_USER_MODEL, verbose_name='Created by'),
        ),
        migrations.AlterField(
            model_name='barrierreal',
            name='deleted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deleted_by_barrierreal_set', to=settings.AUTH_USER_MODEL, verbose_name='Deleted by'),
        ),
        migrations.AlterField(
            model_name='barrierreal',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_by_barrierreal_set', to=settings.AUTH_USER_MODEL, verbose_name='Updated by'),
        ),
        migrations.AlterField(
            model_name='barrierrealoperation',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_by_barrierrealoperation_set', to=settings.AUTH_USER_MODEL, verbose_name='Created by'),
        ),
        migrations.AlterField(
            model_name='barrierrealoperation',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_by_barrierrealoperation_set', to=settings.AUTH_USER_MODEL, verbose_name='Updated by'),
        ),
        migrations.AlterField(
            model_name='mountplan',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_by_mountplan_set', to=settings.AUTH_USER_MODEL, verbose_name='Created by'),
        ),
        migrations.AlterField(
            model_name='mountplan',
            name='deleted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deleted_by_mountplan_set', to=settings.AUTH_USER_MODEL, verbose_name='Deleted by'),
        ),
        migrations.AlterField(
            model_name='mountplan',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_by_mountplan_set', to=settings.AUTH_USER_MODEL, verbose_name='Updated by'),
        ),
        migrations.AlterField(
            model_name='mountreal',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_by_mountreal_set', to=settings.AUTH_USER_MODEL, verbose_name='Created by'),
        ),
        migrations.AlterField(
            model_name='mountreal',
            name='deleted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deleted_by_mountreal_set', to=settings.AUTH_USER_MODEL, verbose_name='Deleted by'),
        ),
        migrations.AlterField(
            model_name='mountreal',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_by_mountreal_set', to=settings.AUTH_USER_MODEL, verbose_name='Updated by'),
        ),
        migrations.AlterField(
            model_name='mountrealoperation',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_by_mountrealoperation_set', to=settings.AUTH_USER_MODEL, verbose_name='Created by'),
        ),
        migrations.AlterField(
            model_name='mountrealoperation',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_by_mountrealoperation_set', to=settings.AUTH_USER_MODEL, verbose_name='Updated by'),
        ),
        migrations.AlterField(
            model_name='plan',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_by_plan_set', to=settings.AUTH_USER_MODEL, verbose_name='Created by'),
        ),
        migrations.AlterField(
            model_name='plan',
            name='deleted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deleted_by_plan_set', to=settings.AUTH_USER_MODEL, verbose_name='Deleted by'),
        ),
        migrations.AlterField(
            model_name='plan',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_by_plan_set', to=settings.AUTH_USER_MODEL, verbose_name='Updated by'),
        ),
        migrations.AlterField(
            model_name='roadmarkingplan',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_by_roadmarkingplan_set', to=settings.AUTH_USER_MODEL, verbose_name='Created by'),
        ),
        migrations.AlterField(
            model_name='roadmarkingplan',
            name='deleted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deleted_by_roadmarkingplan_set', to=settings.AUTH_USER_MODEL, verbose_name='Deleted by'),
        ),
        migrations.AlterField(
            model_name='roadmarkingplan',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_by_roadmarkingplan_set', to=settings.AUTH_USER_MODEL, verbose_name='Updated by'),
        ),
        migrations.AlterField(
            model_name='roadmarkingreal',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_by_roadmarkingreal_set', to=settings.AUTH_USER_MODEL, verbose_name='Created by'),
        ),
        migrations.AlterField(
            model_name='roadmarkingreal',
            name='deleted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deleted_by_roadmarkingreal_set', to=settings.AUTH_USER_MODEL, verbose_name='Deleted by'),
        ),
        migrations.AlterField(
            model_name='roadmarkingreal',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_by_roadmarkingreal_set', to=settings.AUTH_USER_MODEL, verbose_name='Updated by'),
        ),
        migrations.AlterField(
            model_name='roadmarkingrealoperation',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_by_roadmarkingrealoperation_set', to=settings.AUTH_USER_MODEL, verbose_name='Created by'),
        ),
        migrations.AlterField(
            model_name='roadmarkingrealoperation',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_by_roadmarkingrealoperation_set', to=settings.AUTH_USER_MODEL, verbose_name='Updated by'),
        ),
        migrations.AlterField(
            model_name='signpostplan',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_by_signpostplan_set', to=settings.AUTH_USER_MODEL, verbose_name='Created by'),
        ),
        migrations.AlterField(
            model_name='signpostplan',
            name='deleted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deleted_by_signpostplan_set', to=settings.AUTH_USER_MODEL, verbose_name='Deleted by'),
        ),
        migrations.AlterField(
            model_name='signpostplan',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_by_signpostplan_set', to=settings.AUTH_USER_MODEL, verbose_name='Updated by'),
        ),
        migrations.AlterField(
            model_name='signpostreal',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_by_signpostreal_set', to=settings.AUTH_USER_MODEL, verbose_name='Created by'),
        ),
        migrations.AlterField(
            model_name='signpostreal',
            name='deleted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deleted_by_signpostreal_set', to=settings.AUTH_USER_MODEL, verbose_name='Deleted by'),
        ),
        migrations.AlterField(
            model_name='signpostreal',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_by_signpostreal_set', to=settings.AUTH_USER_MODEL, verbose_name='Updated by'),
        ),
        migrations.AlterField(
            model_name='signpostrealoperation',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_by_signpostrealoperation_set', to=settings.AUTH_USER_MODEL, verbose_name='Created by'),
        ),
        migrations.AlterField(
            model_name='signpostrealoperation',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_by_signpostrealoperation_set', to=settings.AUTH_USER_MODEL, verbose_name='Updated by'),
        ),
        migrations.AlterField(
            model_name='trafficlightplan',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_by_trafficlightplan_set', to=settings.AUTH_USER_MODEL, verbose_name='Created by'),
        ),
        migrations.AlterField(
            model_name='trafficlightplan',
            name='deleted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deleted_by_trafficlightplan_set', to=settings.AUTH_USER_MODEL, verbose_name='Deleted by'),
        ),
        migrations.AlterField(
            model_name='trafficlightplan',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_by_trafficlightplan_set', to=settings.AUTH_USER_MODEL, verbose_name='Updated by'),
        ),
        migrations.AlterField(
            model_name='trafficlightreal',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_by_trafficlightreal_set', to=settings.AUTH_USER_MODEL, verbose_name='Created by'),
        ),
        migrations.AlterField(
            model_name='trafficlightreal',
            name='deleted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deleted_by_trafficlightreal_set', to=settings.AUTH_USER_MODEL, verbose_name='Deleted by'),
        ),
        migrations.AlterField(
            model_name='trafficlightreal',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_by_trafficlightreal_set', to=settings.AUTH_USER_MODEL, verbose_name='Updated by'),
        ),
        migrations.AlterField(
            model_name='trafficlightrealoperation',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_by_trafficlightrealoperation_set', to=settings.AUTH_USER_MODEL, verbose_name='Created by'),
        ),
        migrations.AlterField(
            model_name='trafficlightrealoperation',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_by_trafficlightrealoperation_set', to=settings.AUTH_USER_MODEL, verbose_name='Updated by'),
        ),
        migrations.AlterField(
            model_name='trafficsignplan',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_by_trafficsignplan_set', to=settings.AUTH_USER_MODEL, verbose_name='Created by'),
        ),
        migrations.AlterField(
            model_name='trafficsignplan',
            name='deleted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deleted_by_trafficsignplan_set', to=settings.AUTH_USER_MODEL, verbose_name='Deleted by'),
        ),
        migrations.AlterField(
            model_name='trafficsignplan',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_by_trafficsignplan_set', to=settings.AUTH_USER_MODEL, verbose_name='Updated by'),
        ),
        migrations.AlterField(
            model_name='trafficsignreal',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_by_trafficsignreal_set', to=settings.AUTH_USER_MODEL, verbose_name='Created by'),
        ),
        migrations.AlterField(
            model_name='trafficsignreal',
            name='deleted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deleted_by_trafficsignreal_set', to=settings.AUTH_USER_MODEL, verbose_name='Deleted by'),
        ),
        migrations.AlterField(
            model_name='trafficsignreal',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_by_trafficsignreal_set', to=settings.AUTH_USER_MODEL, verbose_name='Updated by'),
        ),
        migrations.AlterField(
            model_name='trafficsignrealoperation',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_by_trafficsignrealoperation_set', to=settings.AUTH_USER_MODEL, verbose_name='Created by'),
        ),
        migrations.AlterField(
            model_name='trafficsignrealoperation',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_by_trafficsignrealoperation_set', to=settings.AUTH_USER_MODEL, verbose_name='Updated by'),
        ),
    ]

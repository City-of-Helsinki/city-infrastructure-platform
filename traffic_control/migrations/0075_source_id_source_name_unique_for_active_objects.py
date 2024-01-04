# Generated by Django 3.2.23 on 2024-01-04 11:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('traffic_control', '0074_nullable_direction'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='additionalsignplan',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='additionalsignreal',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='barrierplan',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='barrierreal',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='mountplan',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='mountreal',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='plan',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='roadmarkingplan',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='roadmarkingreal',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='signpostplan',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='signpostreal',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='trafficlightplan',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='trafficlightreal',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='trafficsignplan',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='trafficsignreal',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='additionalsignplan',
            constraint=models.UniqueConstraint(condition=models.Q(('is_active', True)), fields=('source_name', 'source_id'), name='traffic_control_additionalsignplan_unique_source_name_id'),
        ),
        migrations.AddConstraint(
            model_name='additionalsignreal',
            constraint=models.UniqueConstraint(condition=models.Q(('is_active', True)), fields=('source_name', 'source_id'), name='traffic_control_additionalsignreal_unique_source_name_id'),
        ),
        migrations.AddConstraint(
            model_name='barrierplan',
            constraint=models.UniqueConstraint(condition=models.Q(('is_active', True)), fields=('source_name', 'source_id'), name='traffic_control_barrierplan_unique_source_name_id'),
        ),
        migrations.AddConstraint(
            model_name='barrierreal',
            constraint=models.UniqueConstraint(condition=models.Q(('is_active', True)), fields=('source_name', 'source_id'), name='traffic_control_barrierreal_unique_source_name_id'),
        ),
        migrations.AddConstraint(
            model_name='mountplan',
            constraint=models.UniqueConstraint(condition=models.Q(('is_active', True)), fields=('source_name', 'source_id'), name='traffic_control_mountplan_unique_source_name_id'),
        ),
        migrations.AddConstraint(
            model_name='mountreal',
            constraint=models.UniqueConstraint(condition=models.Q(('is_active', True)), fields=('source_name', 'source_id'), name='traffic_control_mountreal_unique_source_name_id'),
        ),
        migrations.AddConstraint(
            model_name='plan',
            constraint=models.UniqueConstraint(condition=models.Q(('is_active', True)), fields=('source_name', 'source_id'), name='traffic_control_plan_unique_source_name_id'),
        ),
        migrations.AddConstraint(
            model_name='roadmarkingplan',
            constraint=models.UniqueConstraint(condition=models.Q(('is_active', True)), fields=('source_name', 'source_id'), name='traffic_control_roadmarkingplan_unique_source_name_id'),
        ),
        migrations.AddConstraint(
            model_name='roadmarkingreal',
            constraint=models.UniqueConstraint(condition=models.Q(('is_active', True)), fields=('source_name', 'source_id'), name='traffic_control_roadmarkingreal_unique_source_name_id'),
        ),
        migrations.AddConstraint(
            model_name='signpostplan',
            constraint=models.UniqueConstraint(condition=models.Q(('is_active', True)), fields=('source_name', 'source_id'), name='traffic_control_signpostplan_unique_source_name_id'),
        ),
        migrations.AddConstraint(
            model_name='signpostreal',
            constraint=models.UniqueConstraint(condition=models.Q(('is_active', True)), fields=('source_name', 'source_id'), name='traffic_control_signpostreal_unique_source_name_id'),
        ),
        migrations.AddConstraint(
            model_name='trafficlightplan',
            constraint=models.UniqueConstraint(condition=models.Q(('is_active', True)), fields=('source_name', 'source_id'), name='traffic_control_trafficlightplan_unique_source_name_id'),
        ),
        migrations.AddConstraint(
            model_name='trafficlightreal',
            constraint=models.UniqueConstraint(condition=models.Q(('is_active', True)), fields=('source_name', 'source_id'), name='traffic_control_trafficlightreal_unique_source_name_id'),
        ),
        migrations.AddConstraint(
            model_name='trafficsignplan',
            constraint=models.UniqueConstraint(condition=models.Q(('is_active', True)), fields=('source_name', 'source_id'), name='traffic_control_trafficsignplan_unique_source_name_id'),
        ),
        migrations.AddConstraint(
            model_name='trafficsignreal',
            constraint=models.UniqueConstraint(condition=models.Q(('is_active', True)), fields=('source_name', 'source_id'), name='traffic_control_trafficsignreal_unique_source_name_id'),
        ),
    ]

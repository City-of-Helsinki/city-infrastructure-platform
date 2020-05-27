# Generated by Django 2.2.12 on 2020-05-27 07:06

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("traffic_control", "0013_traffic_light_enums"),
    ]

    operations = [
        migrations.CreateModel(
            name="MountType",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("code", models.CharField(max_length=128, verbose_name="Code")),
                (
                    "description",
                    models.CharField(max_length=256, verbose_name="Description"),
                ),
                (
                    "digiroad_code",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="Digiroad code"
                    ),
                ),
                (
                    "digiroad_description",
                    models.CharField(
                        blank=True, max_length=256, verbose_name="Digiroad description"
                    ),
                ),
            ],
            options={
                "verbose_name": "Mount type",
                "verbose_name_plural": "Mount types",
                "db_table": "mount_type",
            },
        ),
        migrations.RenameField(
            model_name="mountplan", old_name="type", new_name="_type",
        ),
        migrations.AddField(
            model_name="mountplan",
            name="type",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="traffic_control.MountType",
                verbose_name="Mount type",
            ),
        ),
        migrations.RenameField(
            model_name="mountreal", old_name="type", new_name="_type",
        ),
        migrations.AddField(
            model_name="mountreal",
            name="type",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="traffic_control.MountType",
                verbose_name="Mount type",
            ),
        ),
        migrations.RenameField(
            model_name="signpostplan", old_name="mount_type", new_name="_mount_type",
        ),
        migrations.AddField(
            model_name="signpostplan",
            name="mount_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="traffic_control.MountType",
                verbose_name="Mount type",
            ),
        ),
        migrations.RenameField(
            model_name="signpostreal", old_name="mount_type", new_name="_mount_type",
        ),
        migrations.AddField(
            model_name="signpostreal",
            name="mount_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="traffic_control.MountType",
                verbose_name="Mount type",
            ),
        ),
        migrations.RenameField(
            model_name="trafficlightplan",
            old_name="mount_type",
            new_name="_mount_type",
        ),
        migrations.AddField(
            model_name="trafficlightplan",
            name="mount_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="traffic_control.MountType",
                verbose_name="Mount type",
            ),
        ),
        migrations.RenameField(
            model_name="trafficlightreal",
            old_name="mount_type",
            new_name="_mount_type",
        ),
        migrations.AddField(
            model_name="trafficlightreal",
            name="mount_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="traffic_control.MountType",
                verbose_name="Mount type",
            ),
        ),
        migrations.RenameField(
            model_name="trafficsignplan", old_name="mount_type", new_name="_mount_type",
        ),
        migrations.RenameField(
            model_name="trafficsignplan",
            old_name="mount_type_fi",
            new_name="_mount_type_fi",
        ),
        migrations.AddField(
            model_name="trafficsignplan",
            name="mount_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="traffic_control.MountType",
                verbose_name="Mount type",
            ),
        ),
        migrations.RenameField(
            model_name="trafficsignreal", old_name="mount_type", new_name="_mount_type",
        ),
        migrations.RenameField(
            model_name="trafficsignreal",
            old_name="mount_type_fi",
            new_name="_mount_type_fi",
        ),
        migrations.AddField(
            model_name="trafficsignreal",
            name="mount_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="traffic_control.MountType",
                verbose_name="Mount type",
            ),
        ),
    ]

# Generated by Django 2.2.9 on 2020-01-17 05:36

from django.conf import settings
import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Lifecycle",
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
                ("status", models.CharField(max_length=32, verbose_name="Status")),
                (
                    "description",
                    models.CharField(
                        blank=True,
                        max_length=254,
                        null=True,
                        verbose_name="Description",
                    ),
                ),
            ],
            options={
                "verbose_name": "Lifecycle",
                "verbose_name_plural": "Lifecycles",
                "db_table": "lifecycle",
            },
        ),
        migrations.CreateModel(
            name="TrafficSignCode",
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
                ("code", models.CharField(max_length=32, verbose_name="Code")),
                (
                    "description",
                    models.CharField(
                        blank=True,
                        max_length=254,
                        null=True,
                        verbose_name="Description",
                    ),
                ),
            ],
            options={
                "verbose_name": "Traffic Sign Code",
                "verbose_name_plural": "Traffic Sign Codes",
                "db_table": "traffic_sign_code",
            },
        ),
        migrations.CreateModel(
            name="TrafficSignPlan",
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
                (
                    "location_xy",
                    django.contrib.gis.db.models.fields.PointField(
                        srid=3879, verbose_name="Location (2D)"
                    ),
                ),
                (
                    "height",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=5,
                        null=True,
                        verbose_name="Height",
                    ),
                ),
                (
                    "direction",
                    models.IntegerField(
                        blank=True, default=0, null=True, verbose_name="Direction"
                    ),
                ),
                (
                    "value",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="Traffic Sign Code value"
                    ),
                ),
                (
                    "mount_id",
                    models.IntegerField(blank=True, null=True, verbose_name="Mount id"),
                ),
                (
                    "mount_type",
                    models.CharField(
                        choices=[
                            ("PORTAL", "Portal"),
                            ("POST", "Post"),
                            ("WALL", "Wall"),
                            ("WIRE", "Wire"),
                            ("BRIDGE", "Bridge"),
                            ("OTHER", "Other"),
                        ],
                        default="OTHER",
                        max_length=10,
                        verbose_name="Mount",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Created at"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Updated at"),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Deleted at"
                    ),
                ),
                (
                    "validity_period_start",
                    models.DateField(
                        blank=True, null=True, verbose_name="Validity period start"
                    ),
                ),
                (
                    "validity_period_end",
                    models.DateField(
                        blank=True, null=True, verbose_name="Validity period end"
                    ),
                ),
                (
                    "seasonal_validity_period_start",
                    models.DateField(
                        blank=True,
                        null=True,
                        verbose_name="Seasonal validity period start",
                    ),
                ),
                (
                    "seasonal_validity_period_end",
                    models.DateField(
                        blank=True,
                        null=True,
                        verbose_name="Seasonal validity period end",
                    ),
                ),
                (
                    "owner",
                    models.CharField(
                        blank=True, max_length=254, null=True, verbose_name="Owner"
                    ),
                ),
                (
                    "txt",
                    models.CharField(
                        blank=True, max_length=254, null=True, verbose_name="Txt"
                    ),
                ),
                ("decision_date", models.DateField(verbose_name="Decision date")),
                (
                    "decision_id",
                    models.CharField(
                        blank=True,
                        max_length=254,
                        null=True,
                        verbose_name="Decision id",
                    ),
                ),
                (
                    "plan_link",
                    models.CharField(
                        blank=True, max_length=254, null=True, verbose_name="Plan link"
                    ),
                ),
                (
                    "size",
                    models.CharField(
                        choices=[("S", "Small"), ("M", "Medium"), ("L", "Large")],
                        default="M",
                        max_length=1,
                        verbose_name="Size",
                    ),
                ),
                (
                    "reflection_class",
                    models.CharField(
                        choices=[("R1", "r1"), ("R2", "r2"), ("R3", "r3")],
                        default="R1",
                        max_length=2,
                        verbose_name="Reflection",
                    ),
                ),
                (
                    "surface_class",
                    models.CharField(
                        choices=[("CONVEX", "Convex"), ("FLAT", "Flat")],
                        default="FLAT",
                        max_length=6,
                        verbose_name="Surface",
                    ),
                ),
                (
                    "color",
                    models.IntegerField(
                        choices=[(1, "Blue"), (2, "Yellow")],
                        default=1,
                        verbose_name="Color",
                    ),
                ),
                (
                    "road_name",
                    models.CharField(
                        blank=True, max_length=254, null=True, verbose_name="Road name"
                    ),
                ),
                (
                    "lane_number",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="Lane number"
                    ),
                ),
                (
                    "lane_type",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="Lane type"
                    ),
                ),
                (
                    "location_specifier",
                    models.IntegerField(
                        blank=True,
                        choices=[
                            (1, "Right side"),
                            (2, "Left side"),
                            (3, "Above"),
                            (4, "Middle"),
                            (5, "Vertical"),
                            (6, "Outside"),
                        ],
                        default=1,
                        null=True,
                        verbose_name="Location specifier",
                    ),
                ),
                (
                    "affect_area",
                    django.contrib.gis.db.models.fields.PolygonField(
                        blank=True,
                        null=True,
                        srid=3879,
                        verbose_name="Affect area (2D)",
                    ),
                ),
                (
                    "code",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="traffic_control.TrafficSignCode",
                        verbose_name="Traffic Sign Code",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="created_by_traffic_sign_plan_set",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Created by",
                    ),
                ),
                (
                    "deleted_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="deleted_by_traffic_sign_plan_set",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Deleted by",
                    ),
                ),
                (
                    "lifecycle",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="traffic_control.Lifecycle",
                        verbose_name="Lifecycle",
                    ),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="traffic_control.TrafficSignPlan",
                        verbose_name="Parent Traffic Sign Plan",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="updated_by_traffic_sign_plan_set",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Updated by",
                    ),
                ),
            ],
            options={
                "verbose_name": "Traffic Sign Plan",
                "verbose_name_plural": "Traffic Sign Plans",
                "db_table": "traffic_sign_plan",
            },
        ),
        migrations.CreateModel(
            name="TrafficSignReal",
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
                (
                    "location_xy",
                    django.contrib.gis.db.models.fields.PointField(
                        srid=3879, verbose_name="Location (2D)"
                    ),
                ),
                (
                    "height",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=5,
                        null=True,
                        verbose_name="Height",
                    ),
                ),
                (
                    "direction",
                    models.IntegerField(
                        blank=True, default=0, null=True, verbose_name="Direction"
                    ),
                ),
                (
                    "value",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="Traffic Sign Code value"
                    ),
                ),
                (
                    "mount_id",
                    models.IntegerField(blank=True, null=True, verbose_name="Mount id"),
                ),
                (
                    "mount_type",
                    models.CharField(
                        choices=[
                            ("PORTAL", "Portal"),
                            ("POST", "Post"),
                            ("WALL", "Wall"),
                            ("WIRE", "Wire"),
                            ("BRIDGE", "Bridge"),
                            ("OTHER", "Other"),
                        ],
                        default="OTHER",
                        max_length=10,
                        verbose_name="Mount",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Created at"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Updated at"),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Deleted at"
                    ),
                ),
                (
                    "validity_period_start",
                    models.DateField(
                        blank=True, null=True, verbose_name="Validity period start"
                    ),
                ),
                (
                    "validity_period_end",
                    models.DateField(
                        blank=True, null=True, verbose_name="Validity period end"
                    ),
                ),
                (
                    "seasonal_validity_period_start",
                    models.DateField(
                        blank=True,
                        null=True,
                        verbose_name="Seasonal validity period start",
                    ),
                ),
                (
                    "seasonal_validity_period_end",
                    models.DateField(
                        blank=True,
                        null=True,
                        verbose_name="Seasonal validity period end",
                    ),
                ),
                (
                    "owner",
                    models.CharField(
                        blank=True, max_length=254, null=True, verbose_name="Owner"
                    ),
                ),
                (
                    "manufacturer",
                    models.CharField(
                        blank=True,
                        max_length=254,
                        null=True,
                        verbose_name="Manufacturer",
                    ),
                ),
                (
                    "rfid",
                    models.CharField(
                        blank=True, max_length=254, null=True, verbose_name="RFID"
                    ),
                ),
                (
                    "txt",
                    models.CharField(
                        blank=True, max_length=254, null=True, verbose_name="Txt"
                    ),
                ),
                (
                    "installation_date",
                    models.DateField(verbose_name="Installation date"),
                ),
                (
                    "installation_status",
                    models.CharField(
                        choices=[
                            ("ACTIVE", "Active"),
                            ("COVERED", "Covered"),
                            ("FALLEN", "Fallen"),
                            ("MISSING", "Missing"),
                            ("OTHER", "Other"),
                        ],
                        default="ACTIVE",
                        max_length=10,
                        verbose_name="Installation status",
                    ),
                ),
                (
                    "installation_id",
                    models.CharField(max_length=254, verbose_name="Installation id"),
                ),
                (
                    "installation_details",
                    models.CharField(
                        blank=True,
                        max_length=254,
                        null=True,
                        verbose_name="Installation details",
                    ),
                ),
                (
                    "condition",
                    models.IntegerField(
                        choices=[
                            (1, "Very bad"),
                            (2, "Bad"),
                            (3, "Average"),
                            (4, "Good"),
                            (5, "Very good"),
                        ],
                        default=4,
                        verbose_name="Condition",
                    ),
                ),
                (
                    "allu_decision_id",
                    models.CharField(max_length=254, verbose_name="Decision id (Allu)"),
                ),
                (
                    "size",
                    models.CharField(
                        choices=[("S", "Small"), ("M", "Medium"), ("L", "Large")],
                        default="M",
                        max_length=1,
                        verbose_name="Size",
                    ),
                ),
                (
                    "reflection_class",
                    models.CharField(
                        choices=[("R1", "r1"), ("R2", "r2"), ("R3", "r3")],
                        default="R1",
                        max_length=2,
                        verbose_name="Reflection",
                    ),
                ),
                (
                    "surface_class",
                    models.CharField(
                        choices=[("CONVEX", "Convex"), ("FLAT", "Flat")],
                        default="FLAT",
                        max_length=6,
                        verbose_name="Surface",
                    ),
                ),
                (
                    "color",
                    models.IntegerField(
                        choices=[(1, "Blue"), (2, "Yellow")],
                        default=1,
                        verbose_name="Color",
                    ),
                ),
                (
                    "road_name",
                    models.CharField(
                        blank=True, max_length=254, null=True, verbose_name="Road name"
                    ),
                ),
                (
                    "lane_number",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="Lane number"
                    ),
                ),
                (
                    "lane_type",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="Lane type"
                    ),
                ),
                (
                    "location_specifier",
                    models.IntegerField(
                        blank=True,
                        choices=[
                            (1, "Right side"),
                            (2, "Left side"),
                            (3, "Above"),
                            (4, "Middle"),
                            (5, "Vertical"),
                            (6, "Outside"),
                        ],
                        default=1,
                        null=True,
                        verbose_name="Location specifier",
                    ),
                ),
                (
                    "affect_area",
                    django.contrib.gis.db.models.fields.PolygonField(
                        blank=True,
                        null=True,
                        srid=3879,
                        verbose_name="Affect area (2D)",
                    ),
                ),
                (
                    "code",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="traffic_control.TrafficSignCode",
                        verbose_name="Traffic Sign Code",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="created_by_traffic_sign_real_set",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Created by",
                    ),
                ),
                (
                    "deleted_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="deleted_by_traffic_sign_real_set",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Deleted by",
                    ),
                ),
                (
                    "lifecycle",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="traffic_control.Lifecycle",
                        verbose_name="Lifecycle",
                    ),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="traffic_control.TrafficSignReal",
                        verbose_name="Parent Traffic Sign Real",
                    ),
                ),
                (
                    "traffic_sign_plan",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="traffic_control.TrafficSignPlan",
                        verbose_name="Traffic Sign Plan",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="updated_by_traffic_sign_real_set",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Updated by",
                    ),
                ),
            ],
            options={
                "verbose_name": "Traffic Sign Real",
                "verbose_name_plural": "Traffic Sign Reals",
                "db_table": "traffic_sign_real",
            },
        ),
    ]

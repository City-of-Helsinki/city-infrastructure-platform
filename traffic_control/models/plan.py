import uuid
from itertools import chain
from typing import List

from auditlog.registry import auditlog
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.contrib.postgres.fields import ArrayField
from django.core.validators import RegexValidator
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from traffic_control.geometry_utils import get_3d_geometry
from traffic_control.mixins.models import (
    BoundaryCheckedLocationMixin,
    SoftDeleteModel,
    SourceControlModel,
    UserControlModel,
)


class Plan(BoundaryCheckedLocationMixin, SourceControlModel, SoftDeleteModel, UserControlModel):
    # Permissions
    ADD_PERMISSION = "traffic_control.add_plan"
    CHANGE_PERMISSION = "traffic_control.change_plan"
    DELETE_PERMISSION = "traffic_control.delete_plan"
    VIEW_PERMISSION = "traffic_control.view_plan"

    id = models.UUIDField(primary_key=True, unique=True, editable=False, default=uuid.uuid4)

    name = models.CharField(verbose_name=_("Name"), max_length=512)
    decision_id = models.CharField(
        verbose_name=_("Decision id"),
        max_length=16,
        help_text=_("Year and verdict section separated with a dash"),
    )
    diary_number = models.CharField(
        verbose_name=_("Diary number"),
        max_length=20,
        unique=False,
        # Diary number will be required field in the future
        null=True,
        blank=True,
    )
    drawing_numbers = ArrayField(
        models.CharField(
            max_length=20,
            validators=[
                RegexValidator(
                    r"^[a-zA-Z0-9-_ ]+$",
                    _("A drawing number must not contain special characters"),
                ),
            ],
        ),
        verbose_name=_("Drawing numbers"),
        null=False,
        blank=True,
        default=list,
        size=100,
        help_text=_("Drawing numbers related to the plan separated with a comma"),
    )
    derive_location = models.BooleanField(
        verbose_name=_("Derive location from devices"),
        help_text=_(
            "Derive the plan location (geometry area) from the locations of related devices. "
            "Enable this if the plan does not have a predefined location."
        ),
        default=False,
    )
    location = models.MultiPolygonField(_("Location (3D)"), dim=3, srid=settings.SRID, null=True, blank=True)

    decision_date = models.DateField(
        _("Decision date"),
        blank=True,
        null=True,
        help_text=_("Date on which a decision was made on the plan."),
    )

    decision_url = models.URLField(
        _("Decision url"),
        max_length=500,
        blank=True,
        null=True,
        help_text=_("URL to decision web page"),
    )

    class Meta:
        db_table = "plan"
        verbose_name = _("Plan")
        verbose_name_plural = _("Plans")
        constraints = [
            models.UniqueConstraint(
                fields=["source_name", "source_id"],
                condition=models.Q(is_active=True),
                name="%(app_label)s_%(class)s_unique_source_name_id",
            ),
            models.UniqueConstraint(
                fields=["diary_number"],
                condition=models.Q(is_active=True),
                name="%(app_label)s_%(class)s_unique_diary_number_id",
            ),
        ]

    def __str__(self):
        return f"{self.decision_id} {self.name}"

    @property
    def convex_hull_location(self):
        """This always forces 3d geometry.
        In WFS CustomGeoJsonRenderer checks if this property exists for an instance."""
        return get_3d_geometry(self.location.convex_hull, 0.0)

    def save(self, *args, **kwargs):
        # Make drawing numbers a unique sorted list
        self.drawing_numbers = sorted(set(self.drawing_numbers or []))

        # Check if decision_date has changed on an existing object
        is_creating = self._state.adding
        original_decision_date = None
        if not is_creating:
            # Store original decision_date from memory if available, otherwise fetch
            if hasattr(self, "_loaded_values") and "decision_date" in self._loaded_values:
                original_decision_date = self._loaded_values["decision_date"]
            else:
                # As a fallback, fetch from DB if not already loaded
                original_decision_date = Plan.objects.get(pk=self.pk).decision_date

        super().save(*args, **kwargs)

        decision_date_changed = not is_creating and original_decision_date != self.decision_date
        if decision_date_changed:
            self._update_related_device_validity_periods()

    @transaction.atomic
    def _update_related_device_validity_periods(self):
        """
        Update the validity_period_start of all related device plans
        to match this plan's decision_date.
        """
        related_devices = self._get_related_device_plans()
        for device in related_devices:
            # This assumes device models have a 'validity_period_start' field
            if hasattr(device, "validity_period_start"):
                device.validity_period_start = self.decision_date
                device.save(update_fields=["validity_period_start"])

    def _get_related_device_plans(self):
        """
        Get a list of all device plan objects related to this plan instance.
        """
        return list(
            chain(
                self.barrier_plans.all(),
                self.mount_plans.all(),
                self.road_marking_plans.all(),
                self.signpost_plans.all(),
                self.traffic_light_plans.all(),
                self.traffic_sign_plans.all(),
                self.additional_sign_plans.all(),
                self.furniture_signpost_plans.all(),
            )
        )

    def _get_related_locations(self) -> List[Point]:
        """
        Get list of Points related to plan instance
        """
        return list(
            chain(
                self.barrier_plans.values_list("location", flat=True),
                self.mount_plans.values_list("location", flat=True),
                self.road_marking_plans.values_list("location", flat=True),
                self.signpost_plans.values_list("location", flat=True),
                self.traffic_light_plans.values_list("location", flat=True),
                self.traffic_sign_plans.values_list("location", flat=True),
                self.additional_sign_plans.values_list("location", flat=True),
                self.furniture_signpost_plans.values_list("location", flat=True),
            )
        )

    def derive_location_from_related_plans(self, buffer: int = 5):
        """
        Derive unified location polygon based on related plan models.
        Buffer the individual points with N meters.

        :param buffer: Buffer radius
        """
        locations = self._get_related_locations()
        if len(locations) == 0:
            self.location = None
        else:
            location_polygons = MultiPolygon(
                [p.buffer(buffer).convex_hull for p in locations],
                srid=settings.SRID,
            )
            area = location_polygons.convex_hull
            assert isinstance(area, Polygon)
            coords_3d = [(*pt, 0) for pt in area.coords[0]]
            area_3d = Polygon(coords_3d, srid=settings.SRID)
            self.location = MultiPolygon(area_3d, srid=settings.SRID)
        self.save(update_fields=["location"])


auditlog.register(Plan)

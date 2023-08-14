import uuid
from itertools import chain
from typing import List

from auditlog.registry import auditlog
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.utils.translation import gettext_lazy as _

from traffic_control.mixins.models import SoftDeleteModel, SourceControlModel, UserControlModel


class Plan(SourceControlModel, SoftDeleteModel, UserControlModel):
    # Permissions
    ADD_PERMISSION = "traffic_control.add_plan"
    CHANGE_PERMISSION = "traffic_control.change_plan"
    DELETE_PERMISSION = "traffic_control.delete_plan"
    VIEW_PERMISSION = "traffic_control.view_plan"

    id = models.UUIDField(primary_key=True, unique=True, editable=False, default=uuid.uuid4)

    name = models.CharField(verbose_name=_("Name"), max_length=512)
    plan_number = models.CharField(
        verbose_name=_("Plan number"),
        max_length=16,
        help_text=_("Year and verdict section separated with a dash"),
    )
    diary_number = models.CharField(
        verbose_name=_("Diary number"),
        max_length=20,
        unique=True,
        # Diary number will be required field in the future
        null=True,
        blank=True,
    )
    drawing_number = models.CharField(
        verbose_name=_("Drawing number"),
        max_length=20,
        null=True,
        blank=True,
    )
    location = models.MultiPolygonField(_("Location (3D)"), dim=3, srid=settings.SRID, null=True, blank=True)

    class Meta:
        db_table = "plan"
        verbose_name = _("Plan")
        verbose_name_plural = _("Plans")
        unique_together = ["source_name", "source_id"]

    def __str__(self):
        return f"{self.plan_number} {self.name}"

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
                [p.buffer(buffer) for p in self._get_related_locations()],
                srid=settings.SRID,
            )
            area = location_polygons.convex_hull
            coords_3d = [(*pt, 0) for pt in area.coords[0]]
            area_3d = Polygon(coords_3d, srid=settings.SRID)
            self.location = MultiPolygon(area_3d, srid=settings.SRID)
        self.save(update_fields=["location"])


auditlog.register(Plan)

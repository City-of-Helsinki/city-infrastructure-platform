from django.contrib.gis import admin

from ..constants import HELSINKI_LATITUDE, HELSINKI_LONGITUDE
from ..mixins import SoftDeleteAdminMixin, UserStampedAdminMixin
from ..models import (
    RoadMarkingPlan,
    RoadMarkingPlanFile,
    RoadMarkingReal,
    RoadMarkingRealFile,
)
from .audit_log import AuditLogHistoryAdmin

__all__ = (
    "RoadMarkingPlanAdmin",
    "RoadMarkingPlanFileInline",
    "RoadMarkingRealAdmin",
    "RoadMarkingRealFileInline",
)


class RoadMarkingPlanFileInline(admin.TabularInline):
    model = RoadMarkingPlanFile


@admin.register(RoadMarkingPlan)
class RoadMarkingPlanAdmin(
    SoftDeleteAdminMixin, UserStampedAdminMixin, admin.OSMGeoAdmin, AuditLogHistoryAdmin
):
    default_lon = HELSINKI_LONGITUDE
    default_lat = HELSINKI_LATITUDE
    default_zoom = 12
    list_display = (
        "id",
        "code",
        "lifecycle",
        "location",
        "decision_date",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    ordering = ("-created_at",)
    inlines = (RoadMarkingPlanFileInline,)


class RoadMarkingRealFileInline(admin.TabularInline):
    model = RoadMarkingRealFile


@admin.register(RoadMarkingReal)
class RoadMarkingRealAdmin(
    SoftDeleteAdminMixin, UserStampedAdminMixin, admin.OSMGeoAdmin, AuditLogHistoryAdmin
):
    default_lon = HELSINKI_LONGITUDE
    default_lat = HELSINKI_LATITUDE
    default_zoom = 12
    list_display = (
        "id",
        "code",
        "lifecycle",
        "location",
        "installation_date",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    ordering = ("-created_at",)
    inlines = (RoadMarkingRealFileInline,)

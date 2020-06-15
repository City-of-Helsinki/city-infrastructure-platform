from django.contrib.gis import admin

from ..constants import HELSINKI_LATITUDE, HELSINKI_LONGITUDE
from ..mixins import SoftDeleteAdminMixin, UserStampedAdminMixin
from ..models import (
    TrafficLightPlan,
    TrafficLightPlanFile,
    TrafficLightReal,
    TrafficLightRealFile,
)
from .audit_log import AuditLogHistoryAdmin

__all__ = (
    "TrafficLightPlanAdmin",
    "TrafficLightPlanFileInline",
    "TrafficLightRealAdmin",
    "TrafficLightRealFileInline",
)


class TrafficLightPlanFileInline(admin.TabularInline):
    model = TrafficLightPlanFile


@admin.register(TrafficLightPlan)
class TrafficLightPlanAdmin(
    SoftDeleteAdminMixin, UserStampedAdminMixin, admin.OSMGeoAdmin, AuditLogHistoryAdmin
):
    default_lon = HELSINKI_LONGITUDE
    default_lat = HELSINKI_LATITUDE
    default_zoom = 12
    list_display = (
        "id",
        "device_type",
        "txt",
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
    inlines = (TrafficLightPlanFileInline,)


class TrafficLightRealFileInline(admin.TabularInline):
    model = TrafficLightRealFile


@admin.register(TrafficLightReal)
class TrafficLightRealAdmin(
    SoftDeleteAdminMixin, UserStampedAdminMixin, admin.OSMGeoAdmin, AuditLogHistoryAdmin
):
    default_lon = HELSINKI_LONGITUDE
    default_lat = HELSINKI_LATITUDE
    default_zoom = 12
    list_display = (
        "id",
        "device_type",
        "txt",
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
    inlines = (TrafficLightRealFileInline,)

from django.contrib.gis import admin

from ..constants import HELSINKI_LATITUDE, HELSINKI_LONGITUDE
from ..mixins import SoftDeleteAdminMixin, UserStampedAdminMixin
from ..models import MountPlan, MountPlanFile, MountReal, MountRealFile, PortalType
from .audit_log import AuditLogHistoryAdmin
from .traffic_sign import OrderedTrafficSignRealInline

__all__ = (
    "MountPlanAdmin",
    "MountPlanFileInline",
    "MountRealAdmin",
    "MountRealFileInline",
    "PortalTypeAdmin",
)


class MountPlanFileInline(admin.TabularInline):
    model = MountPlanFile


@admin.register(MountPlan)
class MountPlanAdmin(
    SoftDeleteAdminMixin, UserStampedAdminMixin, admin.OSMGeoAdmin, AuditLogHistoryAdmin
):
    default_lon = HELSINKI_LONGITUDE
    default_lat = HELSINKI_LATITUDE
    default_zoom = 12
    list_display = (
        "id",
        "type",
        "lifecycle",
        "location",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    ordering = ("-created_at",)
    inlines = (MountPlanFileInline,)


class MountRealFileInline(admin.TabularInline):
    model = MountRealFile


@admin.register(MountReal)
class MountRealAdmin(
    SoftDeleteAdminMixin, UserStampedAdminMixin, admin.OSMGeoAdmin, AuditLogHistoryAdmin
):
    default_lon = HELSINKI_LONGITUDE
    default_lat = HELSINKI_LATITUDE
    default_zoom = 12
    list_display = (
        "id",
        "type",
        "lifecycle",
        "location",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    ordering = ("-created_at",)
    inlines = (MountRealFileInline, OrderedTrafficSignRealInline)


@admin.register(PortalType)
class PortalTypeAdmin(AuditLogHistoryAdmin):
    list_display = (
        "structure",
        "build_type",
        "model",
    )
    ordering = ("structure", "build_type", "model")
    actions = None

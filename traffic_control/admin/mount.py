from django.contrib.gis import admin

from ..mixins import SoftDeleteAdminMixin, UserStampedAdminMixin
from ..models import MountPlan, MountPlanFile, MountReal, PortalType
from .audit_log import AuditLogHistoryAdmin
from .traffic_sign import OrderedTrafficSignRealInline

__all__ = (
    "MountPlanAdmin",
    "MountPlanFileInline",
    "MountRealAdmin",
    "PortalTypeAdmin",
)


class MountPlanFileInline(admin.TabularInline):
    model = MountPlanFile


@admin.register(MountPlan)
class MountPlanAdmin(
    SoftDeleteAdminMixin, UserStampedAdminMixin, admin.OSMGeoAdmin, AuditLogHistoryAdmin
):
    default_lon = 2776957.204335059  # Helsinki city coordinates
    default_lat = 8442622.403718097
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


@admin.register(MountReal)
class MountRealAdmin(
    SoftDeleteAdminMixin, UserStampedAdminMixin, admin.OSMGeoAdmin, AuditLogHistoryAdmin
):
    default_lon = 2776957.204335059  # Helsinki city coordinates
    default_lat = 8442622.403718097
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
    inlines = (OrderedTrafficSignRealInline,)


@admin.register(PortalType)
class PortalTypeAdmin(AuditLogHistoryAdmin):
    list_display = (
        "structure",
        "build_type",
        "model",
    )
    ordering = ("structure", "build_type", "model")
    actions = None

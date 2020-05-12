from django.contrib.gis import admin

from ..mixins import SoftDeleteAdminMixin, UserStampedAdminMixin
from ..models import BarrierPlan, BarrierPlanFile, BarrierReal
from .audit_log import AuditLogHistoryAdmin

__all__ = (
    "BarrierPlanAdmin",
    "BarrierPlanFileInline",
    "BarrierRealAdmin",
)


class BarrierPlanFileInline(admin.TabularInline):
    model = BarrierPlanFile


@admin.register(BarrierPlan)
class BarrierPlanAdmin(
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
        "decision_date",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    ordering = ("-created_at",)
    inlines = (BarrierPlanFileInline,)


@admin.register(BarrierReal)
class BarrierRealAdmin(
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
        "installation_date",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    ordering = ("-created_at",)

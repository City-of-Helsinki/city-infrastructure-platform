from django.contrib.gis import admin

from ..mixins import SoftDeleteAdminMixin, UserStampedAdminMixin
from ..models import RoadMarkingPlan, RoadMarkingPlanFile, RoadMarkingReal
from .audit_log import AuditLogHistoryAdmin

__all__ = (
    "RoadMarkingPlanAdmin",
    "RoadMarkingPlanFileInline",
    "RoadMarkingRealAdmin",
)


class RoadMarkingPlanFileInline(admin.TabularInline):
    model = RoadMarkingPlanFile


@admin.register(RoadMarkingPlan)
class RoadMarkingPlanAdmin(
    SoftDeleteAdminMixin, UserStampedAdminMixin, admin.OSMGeoAdmin, AuditLogHistoryAdmin
):
    default_lon = 2776957.204335059  # Helsinki city coordinates
    default_lat = 8442622.403718097
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


@admin.register(RoadMarkingReal)
class RoadMarkingRealAdmin(
    SoftDeleteAdminMixin, UserStampedAdminMixin, admin.OSMGeoAdmin, AuditLogHistoryAdmin
):
    default_lon = 2776957.204335059  # Helsinki city coordinates
    default_lat = 8442622.403718097
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

from django.contrib.gis import admin

from ..constants import HELSINKI_LATITUDE, HELSINKI_LONGITUDE
from ..mixins import SoftDeleteAdminMixin, UserStampedAdminMixin
from ..models import SignpostPlan, SignpostPlanFile, SignpostReal
from .audit_log import AuditLogHistoryAdmin

__all__ = (
    "SignpostPlanAdmin",
    "SignpostPlanFileInline",
    "SignpostRealAdmin",
)


class SignpostPlanFileInline(admin.TabularInline):
    model = SignpostPlanFile


@admin.register(SignpostPlan)
class SignpostPlanAdmin(
    SoftDeleteAdminMixin, UserStampedAdminMixin, admin.OSMGeoAdmin, AuditLogHistoryAdmin
):
    default_lon = HELSINKI_LONGITUDE
    default_lat = HELSINKI_LATITUDE
    default_zoom = 12
    list_display = (
        "id",
        "code",
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
    inlines = (SignpostPlanFileInline,)


@admin.register(SignpostReal)
class SignpostRealAdmin(
    SoftDeleteAdminMixin, UserStampedAdminMixin, admin.OSMGeoAdmin, AuditLogHistoryAdmin
):
    default_lon = HELSINKI_LONGITUDE
    default_lat = HELSINKI_LATITUDE
    default_zoom = 12
    list_display = (
        "id",
        "code",
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

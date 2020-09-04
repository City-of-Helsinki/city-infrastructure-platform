from django.contrib.gis import admin
from django.utils.translation import gettext_lazy as _

from ..constants import HELSINKI_LATITUDE, HELSINKI_LONGITUDE
from ..mixins import (
    EnumChoiceValueDisplayAdminMixin,
    SoftDeleteAdminMixin,
    UserStampedAdminMixin,
)
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
    EnumChoiceValueDisplayAdminMixin,
    SoftDeleteAdminMixin,
    UserStampedAdminMixin,
    admin.OSMGeoAdmin,
    AuditLogHistoryAdmin,
):
    default_lon = HELSINKI_LONGITUDE
    default_lat = HELSINKI_LATITUDE
    default_zoom = 12
    fieldsets = (
        (
            _("Location information"),
            {
                "fields": (
                    "location",
                    "direction",
                    "road_name",
                    "lane_number",
                    "lane_type",
                    "location_specifier",
                )
            },
        ),
        (_("Physical properties"), {"fields": ("height", "mount_type")}),
        (
            _("General information"),
            {
                "fields": (
                    "owner",
                    "device_type",
                    "type",
                    "vehicle_recognition",
                    "push_button",
                    "sound_beacon",
                    "txt",
                )
            },
        ),
        (_("Related models"), {"fields": ("plan", "mount_plan")}),
        (_("Decision information"), {"fields": ("decision_date", "decision_id")}),
        (
            _("Validity"),
            {
                "fields": (
                    ("validity_period_start", "validity_period_end"),
                    "lifecycle",
                )
            },
        ),
        (
            _("Metadata"),
            {"fields": ("created_at", "updated_at", "created_by", "updated_by")},
        ),
    )
    list_display = (
        "id",
        "device_type",
        "txt",
        "lifecycle",
        "location",
        "decision_date",
    )
    list_filter = SoftDeleteAdminMixin.list_filter + ["owner"]
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
    EnumChoiceValueDisplayAdminMixin,
    SoftDeleteAdminMixin,
    UserStampedAdminMixin,
    admin.OSMGeoAdmin,
    AuditLogHistoryAdmin,
):
    default_lon = HELSINKI_LONGITUDE
    default_lat = HELSINKI_LATITUDE
    default_zoom = 12
    fieldsets = (
        (
            _("Location information"),
            {
                "fields": (
                    "location",
                    "direction",
                    "road_name",
                    "lane_number",
                    "lane_type",
                    "location_specifier",
                )
            },
        ),
        (_("Physical properties"), {"fields": ("height", "mount_type", "condition")}),
        (
            _("General information"),
            {
                "fields": (
                    "owner",
                    "device_type",
                    "type",
                    "vehicle_recognition",
                    "push_button",
                    "sound_beacon",
                    "txt",
                )
            },
        ),
        (_("Related models"), {"fields": ("traffic_light_plan", "mount_real")}),
        (
            _("Installation information"),
            {"fields": ("installation_date", "installation_status")},
        ),
        (
            _("Validity"),
            {
                "fields": (
                    ("validity_period_start", "validity_period_end"),
                    "lifecycle",
                )
            },
        ),
        (
            _("Metadata"),
            {"fields": ("created_at", "updated_at", "created_by", "updated_by")},
        ),
    )
    list_display = (
        "id",
        "device_type",
        "txt",
        "lifecycle",
        "location",
        "installation_date",
    )
    list_filter = SoftDeleteAdminMixin.list_filter + ["owner"]
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    ordering = ("-created_at",)
    inlines = (TrafficLightRealFileInline,)

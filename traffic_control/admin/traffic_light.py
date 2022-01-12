from django.contrib.gis import admin
from django.db import models
from django.utils.translation import gettext_lazy as _

from ..constants import HELSINKI_LATITUDE, HELSINKI_LONGITUDE
from ..forms import AdminFileWidget
from ..mixins import (
    EnumChoiceValueDisplayAdminMixin,
    SoftDeleteAdminMixin,
    UserStampedAdminMixin,
    UserStampedInlineAdminMixin,
)
from ..models import TrafficLightPlan, TrafficLightPlanFile, TrafficLightReal, TrafficLightRealFile
from .audit_log import AuditLogHistoryAdmin
from .common import TrafficControlOperationInlineBase

__all__ = (
    "TrafficLightPlanAdmin",
    "TrafficLightPlanFileInline",
    "TrafficLightRealAdmin",
    "TrafficLightRealFileInline",
)

from ..models.traffic_light import TrafficLightRealOperation


class TrafficLightPlanFileInline(admin.TabularInline):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidget},
    }
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
        (_("Related models"), {"fields": ("plan", "mount_plan")}),
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
    )
    list_filter = SoftDeleteAdminMixin.list_filter + ["owner"]
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "source_name",
        "source_id",
    )
    raw_id_fields = ("plan", "mount_plan")
    ordering = ("-created_at",)
    inlines = (TrafficLightPlanFileInline,)


class TrafficLightRealFileInline(admin.TabularInline):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidget},
    }
    model = TrafficLightRealFile


class TrafficLightRealOperationInline(TrafficControlOperationInlineBase):
    model = TrafficLightRealOperation


@admin.register(TrafficLightReal)
class TrafficLightRealAdmin(
    EnumChoiceValueDisplayAdminMixin,
    SoftDeleteAdminMixin,
    UserStampedAdminMixin,
    UserStampedInlineAdminMixin,
    admin.OSMGeoAdmin,
    AuditLogHistoryAdmin,
):
    default_lon = HELSINKI_LONGITUDE
    default_lat = HELSINKI_LATITUDE
    default_zoom = 12
    fieldsets = (
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
        "source_name",
        "source_id",
    )
    raw_id_fields = ("traffic_light_plan", "mount_real")
    ordering = ("-created_at",)
    inlines = (TrafficLightRealFileInline, TrafficLightRealOperationInline)

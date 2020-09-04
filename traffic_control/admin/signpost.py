from django.contrib.gis import admin
from django.utils.translation import gettext_lazy as _

from ..constants import HELSINKI_LATITUDE, HELSINKI_LONGITUDE
from ..mixins import (
    EnumChoiceValueDisplayAdminMixin,
    SoftDeleteAdminMixin,
    UserStampedAdminMixin,
)
from ..models import SignpostPlan, SignpostPlanFile, SignpostReal, SignpostRealFile
from .audit_log import AuditLogHistoryAdmin

__all__ = (
    "SignpostPlanAdmin",
    "SignpostPlanFileInline",
    "SignpostRealAdmin",
    "SignpostRealFileInline",
)


class SignpostPlanFileInline(admin.TabularInline):
    model = SignpostPlanFile


@admin.register(SignpostPlan)
class SignpostPlanAdmin(
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
        (_("Physical properties"), {"fields": ("height", "size", "reflection_class")}),
        (
            _("General information"),
            {
                "fields": (
                    "owner",
                    "responsible_entity",
                    "electric_maintainer",
                    "device_type",
                    "mount_type",
                    "attachment_class",
                    "value",
                    "txt",
                    "target_id",
                    "target_txt",
                )
            },
        ),
        (_("Related models"), {"fields": ("parent", "plan", "mount_plan")}),
        (_("Decision information"), {"fields": ("decision_date", "decision_id")}),
        (
            _("Validity"),
            {
                "fields": (
                    ("validity_period_start", "validity_period_end"),
                    ("seasonal_validity_period_start", "seasonal_validity_period_end"),
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
    inlines = (SignpostPlanFileInline,)


class SignpostRealFileInline(admin.TabularInline):
    model = SignpostRealFile


@admin.register(SignpostReal)
class SignpostRealAdmin(
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
        (
            _("Physical properties"),
            {
                "fields": (
                    "height",
                    "size",
                    "reflection_class",
                    "material",
                    "condition",
                )
            },
        ),
        (
            _("General information"),
            {
                "fields": (
                    "owner",
                    "responsible_entity",
                    "electric_maintainer",
                    "device_type",
                    "mount_type",
                    "attachment_class",
                    "value",
                    "txt",
                    "target_id",
                    "target_txt",
                    "organization",
                    "manufacturer",
                )
            },
        ),
        (_("Related models"), {"fields": ("parent", "signpost_plan", "mount_real")}),
        (
            _("Installation information"),
            {"fields": ("installation_date", "installation_status")},
        ),
        (
            _("Validity"),
            {
                "fields": (
                    ("validity_period_start", "validity_period_end"),
                    ("seasonal_validity_period_start", "seasonal_validity_period_end"),
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
    inline = (SignpostRealFileInline,)

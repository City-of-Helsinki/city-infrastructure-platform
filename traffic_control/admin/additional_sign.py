from django.contrib.gis import admin
from django.utils.translation import gettext_lazy as _
from enumfields.admin import EnumFieldListFilter

from traffic_control.admin.audit_log import AuditLogHistoryAdmin
from traffic_control.admin.common import OperationalAreaListFilter, TrafficControlOperationInlineBase
from traffic_control.admin.utils import (
    DeviceComparisonAdminMixin,
    ResponsibleEntityPermissionAdminMixin,
    ResponsibleEntityPermissionFilter,
    TreeModelFieldListFilter,
)
from traffic_control.constants import HELSINKI_LATITUDE, HELSINKI_LONGITUDE
from traffic_control.forms import AdditionalSignPlanModelForm, AdditionalSignRealModelForm
from traffic_control.mixins import (
    EnumChoiceValueDisplayAdminMixin,
    Point3DFieldAdminMixin,
    SoftDeleteAdminMixin,
    UserStampedAdminMixin,
    UserStampedInlineAdminMixin,
)
from traffic_control.models import AdditionalSignPlan, AdditionalSignReal
from traffic_control.models.additional_sign import AdditionalSignRealOperation
from traffic_control.resources.additional_sign import AdditionalSignPlanResource, AdditionalSignRealResource
from traffic_control.resources.common import CustomImportExportActionModelAdmin


class AdditionalSignRealOperationInline(TrafficControlOperationInlineBase):
    model = AdditionalSignRealOperation


@admin.register(AdditionalSignPlan)
class AdditionalSignPlanAdmin(
    ResponsibleEntityPermissionAdminMixin,
    EnumChoiceValueDisplayAdminMixin,
    SoftDeleteAdminMixin,
    UserStampedAdminMixin,
    UserStampedInlineAdminMixin,
    Point3DFieldAdminMixin,
    admin.OSMGeoAdmin,
    AuditLogHistoryAdmin,
    CustomImportExportActionModelAdmin,
):
    resource_class = AdditionalSignPlanResource
    form = AdditionalSignPlanModelForm
    fieldsets = (
        (
            _("General information"),
            {
                "fields": (
                    "owner",
                    "responsible_entity",
                    "device_type",
                    "content_s",
                    "mount_type",
                    "source_id",
                    "source_name",
                )
            },
        ),
        (
            _("Location information"),
            {
                "fields": (
                    ("location", "z_coord"),
                    "direction",
                    "order",
                    "road_name",
                    "lane_number",
                    "lane_type",
                    "location_specifier",
                )
            },
        ),
        (
            _("Physical properties"),
            {"fields": ("height", "color", "reflection_class", "surface_class")},
        ),
        (_("Related models"), {"fields": ("parent", "plan", "mount_plan")}),
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

    default_lon = HELSINKI_LONGITUDE
    default_lat = HELSINKI_LATITUDE
    default_zoom = 12
    list_display = (
        "id",
        "device_type",
        "lifecycle",
        "location",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "source_name",
        "source_id",
    )
    raw_id_fields = ("parent", "plan", "mount_plan")
    list_filter = SoftDeleteAdminMixin.list_filter + [
        ResponsibleEntityPermissionFilter,
        ("responsible_entity", TreeModelFieldListFilter),
        ("lifecycle", EnumFieldListFilter),
        "owner",
    ]
    ordering = ("-created_at",)


@admin.register(AdditionalSignReal)
class AdditionalSignRealAdmin(
    DeviceComparisonAdminMixin,
    EnumChoiceValueDisplayAdminMixin,
    SoftDeleteAdminMixin,
    UserStampedAdminMixin,
    UserStampedInlineAdminMixin,
    Point3DFieldAdminMixin,
    admin.OSMGeoAdmin,
    AuditLogHistoryAdmin,
    CustomImportExportActionModelAdmin,
):
    plan_model_field_name = "additional_sign_plan"
    resource_class = AdditionalSignRealResource
    form = AdditionalSignRealModelForm
    fieldsets = (
        (
            _("General information"),
            {
                "fields": (
                    "owner",
                    "responsible_entity",
                    "device_type",
                    "content_s",
                    "mount_type",
                    "permit_decision_id",
                    "attachment_url",
                    "scanned_at",
                    "operation",
                    "manufacturer",
                    "rfid",
                    "legacy_code",
                    "source_id",
                    "source_name",
                )
            },
        ),
        (
            _("Location information"),
            {
                "fields": (
                    ("location", "z_coord"),
                    "direction",
                    "order",
                    "road_name",
                    "lane_number",
                    "lane_type",
                    "location_specifier",
                    "coverage_area",
                )
            },
        ),
        (
            _("Physical properties"),
            {
                "fields": (
                    "size",
                    "height",
                    "color",
                    "reflection_class",
                    "surface_class",
                    "condition",
                )
            },
        ),
        (
            _("Related models"),
            {"fields": ("parent", "additional_sign_plan", "mount_real")},
        ),
        (
            _("Installation information"),
            {
                "fields": (
                    "installation_id",
                    "installation_details",
                    "installation_date",
                    "installation_status",
                    "installed_by",
                )
            },
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
    default_lon = HELSINKI_LONGITUDE
    default_lat = HELSINKI_LATITUDE
    default_zoom = 12
    list_display = (
        "id",
        "device_type",
        "additional_sign_plan",
        "legacy_code",
        "installation_id",
        "installation_details",
        "installation_date",
        "size",
        "mount_real",
        "mount_type",
        "height",
        "installation_status",
        "validity_period_start",
        "validity_period_end",
        "condition",
        "reflection_class",
        "surface_class",
        "seasonal_validity_period_start",
        "seasonal_validity_period_end",
        "owner",
        "lifecycle",
        "road_name",
        "lane_number",
        "lane_type",
        "location_specifier",
        "rfid",
        "direction",
        "operation",
        "manufacturer",
        "permit_decision_id",
        "color",
        "attachment_url",
        "scanned_at",
        "created_at",
        "created_by",
        "updated_at",
        "updated_by",
        "source_id",
        "source_name",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "source_name",
        "source_id",
    )
    raw_id_fields = ("parent", "additional_sign_plan", "mount_real")
    ordering = ("-created_at",)
    list_filter = SoftDeleteAdminMixin.list_filter + [
        ResponsibleEntityPermissionFilter,
        ("responsible_entity", TreeModelFieldListFilter),
        ("lifecycle", EnumFieldListFilter),
        ("installation_status", EnumFieldListFilter),
        ("condition", EnumFieldListFilter),
        ("reflection_class", EnumFieldListFilter),
        ("surface_class", EnumFieldListFilter),
        ("location_specifier", EnumFieldListFilter),
        ("color", EnumFieldListFilter),
        "owner",
        OperationalAreaListFilter,
    ]
    search_fields = (
        "size",
        "height",
        "reflection_class",
        "surface_class",
        "road_name",
        "lane_number",
        "lane_type",
        "source_id",
        "source_name",
    )

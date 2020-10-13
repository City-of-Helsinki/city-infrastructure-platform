from django.contrib.admin import SimpleListFilter
from django.contrib.gis import admin
from django.db import models
from django.utils.translation import gettext_lazy as _
from enumfields.admin import EnumFieldListFilter

from ..constants import HELSINKI_LATITUDE, HELSINKI_LONGITUDE
from ..forms import AdminFileWidget, TrafficSignPlanModelForm, TrafficSignRealModelForm
from ..mixins import (
    EnumChoiceValueDisplayAdminMixin,
    Point3DFieldAdminMixin,
    SoftDeleteAdminMixin,
    UserStampedAdminMixin,
)
from ..models import (
    TrafficControlDeviceType,
    TrafficSignPlan,
    TrafficSignPlanFile,
    TrafficSignReal,
    TrafficSignRealFile,
)
from ..models.common import TRAFFIC_SIGN_TYPE_CHOICES
from ..models.utils import order_queryset_by_z_coord_desc
from .audit_log import AuditLogHistoryAdmin

__all__ = (
    "OrderedTrafficSignRealInline",
    "TrafficControlDeviceTypeAdmin",
    "TrafficSignPlanAdmin",
    "TrafficSignPlanFileInline",
    "TrafficSignRealAdmin",
    "TrafficSignRealFileInline",
)


class TrafficSignTypeListFilter(SimpleListFilter):
    title = _("Traffic sign type")
    parameter_name = "traffic_sign_type"

    def lookups(self, request, model_admin):
        return TRAFFIC_SIGN_TYPE_CHOICES

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(code__startswith=value)
        return queryset


@admin.register(TrafficControlDeviceType)
class TrafficControlDeviceTypeAdmin(
    EnumChoiceValueDisplayAdminMixin, AuditLogHistoryAdmin
):
    list_display = (
        "code",
        "description",
        "legacy_code",
        "legacy_description",
        "target_model",
    )
    list_filter = (TrafficSignTypeListFilter,)
    ordering = ("code",)
    actions = None


class TrafficSignPlanFileInline(admin.TabularInline):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidget},
    }
    model = TrafficSignPlanFile


@admin.register(TrafficSignPlan)
class TrafficSignPlanAdmin(
    EnumChoiceValueDisplayAdminMixin,
    SoftDeleteAdminMixin,
    UserStampedAdminMixin,
    Point3DFieldAdminMixin,
    admin.OSMGeoAdmin,
    AuditLogHistoryAdmin,
):
    form = TrafficSignPlanModelForm
    fieldsets = (
        (
            _("General information"),
            {
                "fields": (
                    "owner",
                    "device_type",
                    "mount_type",
                    "value",
                    "txt",
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
                    "size",
                    "height",
                    "reflection_class",
                    "surface_class",
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
        "value",
        "lifecycle",
        "location",
        "decision_date",
        "has_additional_signs",
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
    inlines = (TrafficSignPlanFileInline,)

    def has_additional_signs(self, obj):
        return (_("No"), _("Yes"))[obj.has_additional_signs()]

    has_additional_signs.short_description = _("has additional signs")


class TrafficSignRealFileInline(admin.TabularInline):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidget},
    }
    model = TrafficSignRealFile


@admin.register(TrafficSignReal)
class TrafficSignRealAdmin(
    EnumChoiceValueDisplayAdminMixin,
    SoftDeleteAdminMixin,
    UserStampedAdminMixin,
    Point3DFieldAdminMixin,
    admin.OSMGeoAdmin,
    AuditLogHistoryAdmin,
):
    form = TrafficSignRealModelForm
    fieldsets = (
        (
            _("General information"),
            {
                "fields": (
                    "owner",
                    "device_type",
                    "mount_type",
                    "permit_decision_id",
                    "attachment_url",
                    "scanned_at",
                    "operation",
                    "manufacturer",
                    "rfid",
                    "value",
                    "txt",
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
                    "road_name",
                    "lane_number",
                    "lane_type",
                    "location_specifier",
                    "parking_area",
                )
            },
        ),
        (
            _("Physical properties"),
            {
                "fields": (
                    "size",
                    "height",
                    "reflection_class",
                    "surface_class",
                    "condition",
                )
            },
        ),
        (_("Related models"), {"fields": ("traffic_sign_plan", "mount_real")}),
        (
            _("Installation information"),
            {
                "fields": (
                    "installation_date",
                    "installation_status",
                    "installation_id",
                    "installation_details",
                ),
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
        "traffic_sign_plan",
        "device_type",
        "legacy_code",
        "value",
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
        "txt",
        "has_additional_signs",
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
        "has_additional_signs",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "source_name",
        "source_id",
    )
    raw_id_fields = ("traffic_sign_plan", "mount_real")
    ordering = ("-created_at",)
    list_filter = SoftDeleteAdminMixin.list_filter + [
        ("lifecycle", EnumFieldListFilter),
        ("installation_status", EnumFieldListFilter),
        ("condition", EnumFieldListFilter),
        ("reflection_class", EnumFieldListFilter),
        ("surface_class", EnumFieldListFilter),
        ("location_specifier", EnumFieldListFilter),
        "owner",
    ]
    search_fields = (
        "traffic_sign_plan__id",
        "device_type__code",
        "device_type__description",
        "value",
        "size",
        "mount_real__id",
        "height",
        "reflection_class",
        "surface_class",
        "owner",
        "road_name",
        "lane_number",
        "lane_type",
        "source_id",
        "source_name",
    )
    inlines = (TrafficSignRealFileInline,)

    def has_additional_signs(self, obj):
        return (_("No"), _("Yes"))[obj.has_additional_signs()]

    has_additional_signs.short_description = _("has additional signs")


class OrderedTrafficSignRealInline(admin.TabularInline):
    model = TrafficSignReal
    fields = ("id", "z_coord")
    readonly_fields = ("id", "z_coord")
    show_change_link = True
    can_delete = False
    verbose_name = _("Ordered traffic sign")
    verbose_name_plural = _("Ordered traffic signs")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return order_queryset_by_z_coord_desc(qs)

    def z_coord(self, obj):
        return obj.location.z

    z_coord.short_description = _("Location (z)")

    def has_add_permission(self, request, obj=None):
        return False

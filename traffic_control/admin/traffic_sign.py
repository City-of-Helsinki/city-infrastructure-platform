from django.contrib.gis import admin
from django.utils.translation import gettext_lazy as _
from enumfields.admin import EnumFieldListFilter

from ..constants import HELSINKI_LATITUDE, HELSINKI_LONGITUDE
from ..forms import TrafficSignPlanModelForm, TrafficSignRealModelForm
from ..mixins import Point3DFieldAdminMixin, SoftDeleteAdminMixin, UserStampedAdminMixin
from ..models import (
    TrafficSignCode,
    TrafficSignPlan,
    TrafficSignPlanFile,
    TrafficSignReal,
    TrafficSignRealFile,
)
from ..models.utils import order_queryset_by_z_coord_desc
from .audit_log import AuditLogHistoryAdmin

__all__ = (
    "OrderedTrafficSignRealInline",
    "TrafficSignCodeAdmin",
    "TrafficSignPlanAdmin",
    "TrafficSignPlanFileInline",
    "TrafficSignRealAdmin",
    "TrafficSignRealFileInline",
)


@admin.register(TrafficSignCode)
class TrafficSignCodeAdmin(AuditLogHistoryAdmin):
    list_display = ("code", "description", "legacy_code", "legacy_description")
    ordering = ("code",)
    actions = None


class TrafficSignPlanFileInline(admin.TabularInline):
    model = TrafficSignPlanFile


@admin.register(TrafficSignPlan)
class TrafficSignPlanAdmin(
    SoftDeleteAdminMixin,
    UserStampedAdminMixin,
    Point3DFieldAdminMixin,
    admin.OSMGeoAdmin,
    AuditLogHistoryAdmin,
):
    form = TrafficSignPlanModelForm
    fields = (
        ("location", "z_coord"),
        "height",
        "direction",
        "code",
        "value",
        "parent",
        "txt",
        "mount_plan",
        "decision_date",
        "decision_id",
        "validity_period_start",
        "validity_period_end",
        "affect_area",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "size",
        "reflection_class",
        "surface_class",
        "seasonal_validity_period_start",
        "seasonal_validity_period_end",
        "owner",
        "color",
        "lifecycle",
        "road_name",
        "lane_number",
        "lane_type",
        "location_specifier",
        "source_id",
        "source_name",
    )
    default_lon = HELSINKI_LONGITUDE
    default_lat = HELSINKI_LATITUDE
    default_zoom = 12
    list_display = (
        "id",
        "code",
        "value",
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
    inlines = (TrafficSignPlanFileInline,)


class TrafficSignRealFileInline(admin.TabularInline):
    model = TrafficSignRealFile


@admin.register(TrafficSignReal)
class TrafficSignRealAdmin(
    SoftDeleteAdminMixin,
    UserStampedAdminMixin,
    Point3DFieldAdminMixin,
    admin.OSMGeoAdmin,
    AuditLogHistoryAdmin,
):
    form = TrafficSignRealModelForm
    fields = (
        "traffic_sign_plan",
        ("location", "z_coord"),
        "height",
        "direction",
        "code",
        "value",
        "legacy_code",
        "has_additional_signs",
        "parent",
        "txt",
        "mount_real",
        "installation_date",
        "installation_status",
        "installation_id",
        "installation_details",
        "allu_decision_id",
        "validity_period_start",
        "validity_period_end",
        "condition",
        "affect_area",
        "created_at",
        "updated_at",
        "scanned_at",
        "created_by",
        "updated_by",
        "size",
        "reflection_class",
        "surface_class",
        "seasonal_validity_period_start",
        "seasonal_validity_period_end",
        "owner",
        "manufacturer",
        "rfid",
        "color",
        "lifecycle",
        "road_name",
        "lane_number",
        "lane_type",
        "location_specifier",
        "operation",
        "attachment_url",
        "source_id",
        "source_name",
    )
    default_lon = HELSINKI_LONGITUDE
    default_lat = HELSINKI_LATITUDE
    default_zoom = 12
    list_display = (
        "id",
        "traffic_sign_plan",
        "code",
        "legacy_code",
        "value",
        "installation_id",
        "installation_details",
        "installation_date",
        "size",
        "mount_real",
        "height",
        "parent",
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
        "allu_decision_id",
        "txt",
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
        "has_additional_signs",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    ordering = ("-created_at",)
    list_filter = [
        ("lifecycle", EnumFieldListFilter),
        ("installation_status", EnumFieldListFilter),
        ("condition", EnumFieldListFilter),
        ("reflection_class", EnumFieldListFilter),
        ("surface_class", EnumFieldListFilter),
        ("location_specifier", EnumFieldListFilter),
        ("color", EnumFieldListFilter),
    ]
    search_fields = (
        "traffic_sign_plan__id",
        "code__code",
        "code__description",
        "value",
        "installation_date",
        "size",
        "mount_real__id",
        "mount_type",
        "height",
        "parent__id",
        "validity_period_start",
        "validity_period_end",
        "reflection_class",
        "surface_class",
        "seasonal_validity_period_start",
        "seasonal_validity_period_end",
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
    fields = ("id", "parent", "z_coord")
    readonly_fields = ("id", "parent", "z_coord")
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

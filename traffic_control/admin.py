from django.contrib.admin.utils import unquote
from django.contrib.gis import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from enumfields.admin import EnumFieldListFilter

from .forms import TrafficSignPlanModelForm, TrafficSignRealModelForm
from .mixins import Point3DFieldAdminMixin, SoftDeleteAdminMixin, UserStampedAdminMixin
from .models import (
    BarrierPlan,
    BarrierPlanFile,
    BarrierReal,
    MountPlan,
    MountPlanFile,
    MountReal,
    PortalType,
    RoadMarkingPlan,
    RoadMarkingPlanFile,
    RoadMarkingReal,
    SignpostPlan,
    SignpostPlanFile,
    SignpostReal,
    TrafficLightPlan,
    TrafficLightPlanFile,
    TrafficLightReal,
    TrafficSignCode,
    TrafficSignPlan,
    TrafficSignPlanFile,
    TrafficSignReal,
)

admin.site.site_header = _("City Infrastructure Platform Administration")


class AuditLogHistoryAdmin(admin.ModelAdmin):
    def history_view(self, request, object_id, extra_context=None):
        return HttpResponseRedirect(
            "{url}?object_repr={object_repr}".format(
                url=reverse("admin:auditlog_logentry_changelist", args=()),
                object_repr=self.get_object(request, unquote(object_id)),
            )
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


class TrafficLightPlanFileInline(admin.TabularInline):
    model = TrafficLightPlanFile


@admin.register(TrafficLightPlan)
class TrafficLightPlanAdmin(
    SoftDeleteAdminMixin, UserStampedAdminMixin, admin.OSMGeoAdmin, AuditLogHistoryAdmin
):
    default_lon = 2776957.204335059  # Helsinki city coordinates
    default_lat = 8442622.403718097
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
    inlines = (TrafficLightPlanFileInline,)


@admin.register(TrafficLightReal)
class TrafficLightRealAdmin(
    SoftDeleteAdminMixin, UserStampedAdminMixin, admin.OSMGeoAdmin, AuditLogHistoryAdmin
):
    default_lon = 2776957.204335059  # Helsinki city coordinates
    default_lat = 8442622.403718097
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
        "order",
        "txt",
        "mount_plan",
        "mount_type",
        "mount_type_fi",
        "decision_date",
        "decision_id",
        "validity_period_start",
        "validity_period_end",
        "affect_area",
        "created_at",
        "updated_at",
        "deleted_at",
        "created_by",
        "updated_by",
        "deleted_by",
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
    default_lon = 2776957.204335059  # Helsinki city coordinates
    default_lat = 8442622.403718097
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
        "order",
        "txt",
        "mount_real",
        "mount_type",
        "mount_type_fi",
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
        "deleted_at",
        "scanned_at",
        "created_by",
        "updated_by",
        "deleted_by",
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
    default_lon = 2776957.204335059  # Helsinki city coordinates
    default_lat = 8442622.403718097
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
        "mount_type",
        "mount_type_fi",
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
        "source_id",
        "source_name",
        "order",
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
        "deleted_at",
        "reflection_class",
        "surface_class",
        "seasonal_validity_period_start",
        "seasonal_validity_period_end",
        "owner",
        "road_name",
        "lane_number",
        "lane_type",
    )

    def has_additional_signs(self, obj):
        return (_("No"), _("Yes"))[obj.has_additional_signs()]

    has_additional_signs.short_description = _("has additional signs")


class SignpostPlanFileInline(admin.TabularInline):
    model = SignpostPlanFile


@admin.register(SignpostPlan)
class SignpostPlanAdmin(
    SoftDeleteAdminMixin, UserStampedAdminMixin, admin.OSMGeoAdmin, AuditLogHistoryAdmin
):
    default_lon = 2776957.204335059  # Helsinki city coordinates
    default_lat = 8442622.403718097
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
    default_lon = 2776957.204335059  # Helsinki city coordinates
    default_lat = 8442622.403718097
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


@admin.register(TrafficSignCode)
class TrafficSignCodeAdmin(AuditLogHistoryAdmin):
    list_display = ("code", "description", "legacy_code", "legacy_description")
    ordering = ("code",)
    actions = None


@admin.register(PortalType)
class PortalTypeAdmin(AuditLogHistoryAdmin):
    list_display = (
        "structure",
        "build_type",
        "model",
    )
    ordering = ("structure", "build_type", "model")
    actions = None

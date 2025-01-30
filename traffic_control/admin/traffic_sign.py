from django.contrib.admin import SimpleListFilter
from django.contrib.gis import admin
from django.db import models
from django.utils.translation import gettext_lazy as _
from enumfields.admin import EnumFieldListFilter

from traffic_control.admin.additional_sign import AdditionalSignPlanInline, AdditionalSignRealInline
from traffic_control.admin.audit_log import AuditLogHistoryAdmin
from traffic_control.admin.common import (
    OperationalAreaListFilter,
    PlanReplacementListFilterMixin,
    ReplacedByInline,
    ReplacesInline,
    TrafficControlOperationInlineBase,
)
from traffic_control.admin.utils import (
    AdminFieldInitialValuesMixin,
    DeviceComparisonAdminMixin,
    MultiResourceExportActionAdminMixin,
    ResponsibleEntityPermissionAdminMixin,
    ResponsibleEntityPermissionFilter,
    TreeModelFieldListFilter,
)
from traffic_control.enums import (
    Condition,
    InstallationStatus,
    LaneNumber,
    LaneType,
    Reflection,
    Size,
    Surface,
    TRAFFIC_SIGN_TYPE_CHOICES,
)
from traffic_control.forms import (
    AdminFileWidget,
    CityInfraFileUploadFormset,
    TrafficSignPlanModelForm,
    TrafficSignRealModelForm,
)
from traffic_control.mixins import (
    DeviceTypeSearchAdminMixin,
    EnumChoiceValueDisplayAdminMixin,
    Geometry3DFieldAdminMixin,
    SoftDeleteAdminMixin,
    UpdatePlanLocationAdminMixin,
    UserStampedAdminMixin,
    UserStampedInlineAdminMixin,
)
from traffic_control.models import (
    TrafficControlDeviceType,
    TrafficSignPlan,
    TrafficSignPlanFile,
    TrafficSignPlanReplacement,
    TrafficSignReal,
    TrafficSignRealFile,
)
from traffic_control.models.traffic_sign import LocationSpecifier, TrafficSignRealOperation
from traffic_control.models.utils import order_queryset_by_z_coord_desc
from traffic_control.resources.common import CustomImportExportActionModelAdmin
from traffic_control.resources.device_type import TrafficControlDeviceTypeResource
from traffic_control.resources.traffic_sign import (
    TrafficSignPlanResource,
    TrafficSignPlanToRealTemplateResource,
    TrafficSignRealResource,
)

__all__ = (
    "OrderedTrafficSignRealInline",
    "TrafficControlDeviceTypeAdmin",
    "TrafficSignPlanAdmin",
    "TrafficSignPlanFileInline",
    "TrafficSignRealAdmin",
    "TrafficSignRealFileInline",
)

shared_initial_values = {
    "lane_number": LaneNumber.MAIN_1,
    "lane_type": LaneType.MAIN,
    "size": Size.MEDIUM,
    "reflection_class": Reflection.R1,
    "surface_class": Surface.FLAT,
    "location_specifier": LocationSpecifier.RIGHT,
}


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
    EnumChoiceValueDisplayAdminMixin,
    AuditLogHistoryAdmin,
    CustomImportExportActionModelAdmin,
):
    resource_class = TrafficControlDeviceTypeResource
    list_display = (
        "code",
        "icon",
        "description",
        "value",
        "unit",
        "size",
        "legacy_code",
        "legacy_description",
        "target_model",
    )
    list_filter = (TrafficSignTypeListFilter,)
    search_fields = ("code", "legacy_code")
    search_help_text = "Searches from code and legacy_code fields"
    ordering = ("code",)
    actions = None


class TrafficSignPlanFileInline(admin.TabularInline):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidget},
    }
    model = TrafficSignPlanFile
    formset = CityInfraFileUploadFormset


class TrafficSignPlanReplacesInline(ReplacesInline):
    model = TrafficSignPlanReplacement


class TrafficSignPlanReplacedByInline(ReplacedByInline):
    model = TrafficSignPlanReplacement


class TrafficSignPlanReplacementListFilter(PlanReplacementListFilterMixin, SimpleListFilter):
    plan_model = TrafficSignPlan


@admin.register(TrafficSignPlan)
class TrafficSignPlanAdmin(
    DeviceTypeSearchAdminMixin,
    ResponsibleEntityPermissionAdminMixin,
    EnumChoiceValueDisplayAdminMixin,
    SoftDeleteAdminMixin,
    UserStampedAdminMixin,
    Geometry3DFieldAdminMixin,
    MultiResourceExportActionAdminMixin,
    AdminFieldInitialValuesMixin,
    UpdatePlanLocationAdminMixin,
    admin.GISModelAdmin,
    AuditLogHistoryAdmin,
    CustomImportExportActionModelAdmin,
):
    resource_class = TrafficSignPlanResource
    extra_export_resource_classes = [TrafficSignPlanToRealTemplateResource]
    form = TrafficSignPlanModelForm
    fieldsets = (
        (
            _("General information"),
            {
                "fields": (
                    "owner",
                    "responsible_entity",
                    "device_type",
                    "mount_type",
                    "value",
                    "txt",
                    "source_id",
                )
            },
        ),
        (
            _("Location information"),
            {
                "fields": (
                    "location",
                    "z_coord",
                    "location_ewkt",
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
        "value",
        "lifecycle",
        "location",
        "has_additional_signs",
        "is_replaced_as_str",
    )
    list_filter = SoftDeleteAdminMixin.list_filter + [
        ResponsibleEntityPermissionFilter,
        ("responsible_entity", TreeModelFieldListFilter),
        ("lifecycle", EnumFieldListFilter),
        "owner",
        TrafficSignPlanReplacementListFilter,
    ]
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    raw_id_fields = ("plan", "mount_plan")
    ordering = ("-created_at",)
    inlines = (
        TrafficSignPlanFileInline,
        AdditionalSignPlanInline,
        TrafficSignPlanReplacesInline,
        TrafficSignPlanReplacedByInline,
    )
    initial_values = shared_initial_values

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("device_type")

    def has_additional_signs(self, obj):
        return (_("No"), _("Yes"))[obj.has_additional_signs()]

    has_additional_signs.short_description = _("has additional signs")


class TrafficSignRealFileInline(admin.TabularInline):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidget},
    }
    model = TrafficSignRealFile
    formset = CityInfraFileUploadFormset


class TrafficSignRealOperationInline(TrafficControlOperationInlineBase):
    model = TrafficSignRealOperation


@admin.register(TrafficSignReal)
class TrafficSignRealAdmin(
    DeviceTypeSearchAdminMixin,
    DeviceComparisonAdminMixin,
    ResponsibleEntityPermissionAdminMixin,
    EnumChoiceValueDisplayAdminMixin,
    SoftDeleteAdminMixin,
    UserStampedAdminMixin,
    UserStampedInlineAdminMixin,
    Geometry3DFieldAdminMixin,
    AdminFieldInitialValuesMixin,
    admin.GISModelAdmin,
    AuditLogHistoryAdmin,
    CustomImportExportActionModelAdmin,
):
    plan_model_field_name = "traffic_sign_plan"
    resource_class = TrafficSignRealResource
    form = TrafficSignRealModelForm
    fieldsets = (
        (
            _("General information"),
            {
                "fields": (
                    "owner",
                    "responsible_entity",
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
                    "location",
                    "z_coord",
                    "location_ewkt",
                    "direction",
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
        ResponsibleEntityPermissionFilter,
        ("responsible_entity", TreeModelFieldListFilter),
        ("lifecycle", EnumFieldListFilter),
        ("installation_status", EnumFieldListFilter),
        ("condition", EnumFieldListFilter),
        ("reflection_class", EnumFieldListFilter),
        ("surface_class", EnumFieldListFilter),
        ("location_specifier", EnumFieldListFilter),
        "owner",
        OperationalAreaListFilter,
    ]
    search_fields = (
        "value",
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
    inlines = (
        TrafficSignRealFileInline,
        TrafficSignRealOperationInline,
        AdditionalSignRealInline,
    )
    initial_values = {
        **shared_initial_values,
        "condition": Condition.VERY_GOOD,
        "installation_status": InstallationStatus.IN_USE,
    }

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("device_type")

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

from django.contrib.admin import SimpleListFilter
from django.contrib.gis import admin
from django.db import models
from django.utils.translation import gettext_lazy as _
from enumfields.admin import EnumFieldListFilter
from guardian.admin import GuardedModelAdmin

from traffic_control.admin.audit_log import AuditLogHistoryAdmin
from traffic_control.admin.common import (
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
from traffic_control.enums import Condition, InstallationStatus, LaneNumber, LaneType
from traffic_control.forms import (
    AdminFileWidget,
    CityInfraFileUploadFormset,
    RoadMarkingPlanModelForm,
    RoadMarkingRealModelForm,
)
from traffic_control.mixins import (
    DeviceTypeSearchAdminMixin,
    EnumChoiceValueDisplayAdminMixin,
    Geometry3DFieldAdminMixin,
    PreviewDeviceTypeRelationMixin,
    SoftDeleteAdminMixin,
    UpdatePlanLocationAdminMixin,
    UserStampedAdminMixin,
    UserStampedInlineAdminMixin,
)
from traffic_control.models import RoadMarkingPlan, RoadMarkingPlanFile, RoadMarkingReal, RoadMarkingRealFile
from traffic_control.resources.common import CustomImportExportActionModelAdmin
from traffic_control.resources.road_marking import (
    RoadMarkingPlanResource,
    RoadMarkingPlanToRealTemplateResource,
    RoadMarkingRealResource,
)

__all__ = (
    "RoadMarkingPlanAdmin",
    "RoadMarkingPlanFileInline",
    "RoadMarkingRealAdmin",
    "RoadMarkingRealFileInline",
)

from traffic_control.models.road_marking import (
    LineDirection,
    LocationSpecifier,
    RoadMarkingColor,
    RoadMarkingPlanReplacement,
    RoadMarkingRealOperation,
)

shared_initial_values = {
    "lane_number": LaneNumber.MAIN_1,
    "lane_type": LaneType.MAIN,
    "location_specifier": LocationSpecifier.RIGHT_SIDE_OF_LANE,
    "line_direction": LineDirection.FORWARD,
    "color": RoadMarkingColor.WHITE,
}


@admin.register(RoadMarkingPlanFile)
class RoadMarkingPlanFileAdmin(GuardedModelAdmin):
    list_display = ("id", "file", "is_public")
    raw_id_fields = ("road_marking_plan",)


@admin.register(RoadMarkingRealFile)
class RoadMarkingRealFileAdmin(GuardedModelAdmin):
    list_display = ("id", "file", "is_public")
    raw_id_fields = ("road_marking_real",)


class RoadMarkingPlanFileInline(admin.TabularInline):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidget},
    }
    model = RoadMarkingPlanFile
    formset = CityInfraFileUploadFormset


class RoadMarkingPlanReplacesInline(ReplacesInline):
    model = RoadMarkingPlanReplacement


class RoadMarkingPlanReplacedByInline(ReplacedByInline):
    model = RoadMarkingPlanReplacement


class RoadMarkingPlanReplacementListFilter(PlanReplacementListFilterMixin, SimpleListFilter):
    plan_model = RoadMarkingPlan


@admin.register(RoadMarkingPlan)
class RoadMarkingPlanAdmin(
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
    PreviewDeviceTypeRelationMixin,
):
    resource_class = RoadMarkingPlanResource
    extra_export_resource_classes = [RoadMarkingPlanToRealTemplateResource]
    form = RoadMarkingPlanModelForm
    SHOW_Z_COORD = False
    fieldsets = (
        (
            _("General information"),
            {
                "fields": (
                    "owner",
                    "responsible_entity",
                    "device_type",
                    "type_specifier",
                    "value",
                    "symbol",
                    "amount",
                    "additional_info",
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
                    "arrow_direction",
                    "line_direction",
                    "size",
                    "length",
                    "width",
                    "is_raised",
                    "is_grinded",
                    "material",
                    "color",
                )
            },
        ),
        (_("Related models"), {"fields": ("plan", "traffic_sign_plan")}),
        (
            _("Validity"),
            {
                "fields": (
                    ("validity_period_start", "validity_period_end"),
                    "seasonal_validity_period_information",
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
        "device_type_preview",
        "lifecycle",
        "location",
        "is_replaced_as_str",
    )
    list_filter = SoftDeleteAdminMixin.list_filter + [
        ResponsibleEntityPermissionFilter,
        ("responsible_entity", TreeModelFieldListFilter),
        ("lifecycle", EnumFieldListFilter),
        "owner",
        RoadMarkingPlanReplacementListFilter,
    ]
    search_fields = ("id",)
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    raw_id_fields = ("plan", "traffic_sign_plan")
    ordering = ("-created_at",)
    inlines = (
        RoadMarkingPlanFileInline,
        RoadMarkingPlanReplacesInline,
        RoadMarkingPlanReplacedByInline,
    )
    initial_values = shared_initial_values

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("device_type")


class RoadMarkingRealFileInline(admin.TabularInline):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidget},
    }
    model = RoadMarkingRealFile
    formset = CityInfraFileUploadFormset


class RoadMarkingRealOperationInline(TrafficControlOperationInlineBase):
    model = RoadMarkingRealOperation


@admin.register(RoadMarkingReal)
class RoadMarkingRealAdmin(
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
    PreviewDeviceTypeRelationMixin,
):
    plan_model_field_name = "road_marking_plan"
    resource_class = RoadMarkingRealResource
    form = RoadMarkingRealModelForm
    SHOW_Z_COORD = False
    fieldsets = (
        (
            _("General information"),
            {
                "fields": (
                    "owner",
                    "responsible_entity",
                    "device_type",
                    "type_specifier",
                    "value",
                    "symbol",
                    "amount",
                    "additional_info",
                    "missing_traffic_sign_real_txt",
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
                    "arrow_direction",
                    "line_direction",
                    "size",
                    "length",
                    "width",
                    "is_raised",
                    "is_grinded",
                    "material",
                    "color",
                    "condition",
                )
            },
        ),
        (_("Related models"), {"fields": ("road_marking_plan", "traffic_sign_real")}),
        (
            _("Installation information"),
            {"fields": ("installation_date", "installation_status")},
        ),
        (
            _("Validity"),
            {
                "fields": (
                    ("validity_period_start", "validity_period_end"),
                    "seasonal_validity_period_information",
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
        "device_type_preview",
        "lifecycle",
        "location",
        "installation_date",
    )
    list_filter = SoftDeleteAdminMixin.list_filter + [
        ResponsibleEntityPermissionFilter,
        ("responsible_entity", TreeModelFieldListFilter),
        ("lifecycle", EnumFieldListFilter),
        "owner",
    ]
    search_fields = ("id",)
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    raw_id_fields = ("road_marking_plan", "traffic_sign_real")
    ordering = ("-created_at",)
    inlines = (RoadMarkingRealFileInline, RoadMarkingRealOperationInline)
    initial_values = {
        **shared_initial_values,
        "condition": Condition.VERY_GOOD,
        "installation_status": InstallationStatus.IN_USE,
    }

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("device_type")

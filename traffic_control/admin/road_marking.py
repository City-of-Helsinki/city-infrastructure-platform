from django.contrib.admin import ChoicesFieldListFilter, SimpleListFilter
from django.contrib.gis import admin
from django.db import models
from django.utils.translation import gettext_lazy as _
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
)
from traffic_control.enums import Condition, InstallationStatus, LaneNumber, LaneType
from traffic_control.forms import (
    AdminFileWidgetWithProxy,
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
    UploadsFileProxyMixin,
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
class RoadMarkingPlanFileAdmin(GuardedModelAdmin, UploadsFileProxyMixin):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidgetWithProxy},
    }
    list_display = ("id", "file_proxy", "is_public")
    raw_id_fields = ("road_marking_plan",)


@admin.register(RoadMarkingRealFile)
class RoadMarkingRealFileAdmin(GuardedModelAdmin, UploadsFileProxyMixin):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidgetWithProxy},
    }
    list_display = ("id", "file_proxy", "is_public")
    raw_id_fields = ("road_marking_real",)


class RoadMarkingPlanFileInline(admin.TabularInline):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidgetWithProxy},
    }
    model = RoadMarkingPlanFile
    formset = CityInfraFileUploadFormset


class RoadMarkinRealInline(admin.TabularInline, PreviewDeviceTypeRelationMixin):
    model = RoadMarkingReal
    verbose_name = _("Road Marking Real")
    verbose_name_plural = _("Road Marking Real")
    fields = ("id", "device_type_preview", "color")
    readonly_fields = ("id", "device_type_preview", "color")
    show_change_link = True
    can_delete = False
    extra = 0

    def has_add_permission(self, request, obj):
        return False


class RoadMarkingPlanReplacesInline(ReplacesInline):
    model = RoadMarkingPlanReplacement


class RoadMarkingPlanReplacedByInline(ReplacedByInline):
    model = RoadMarkingPlanReplacement


class RoadMarkingPlanReplacementListFilter(PlanReplacementListFilterMixin, SimpleListFilter):
    plan_model = RoadMarkingPlan


@admin.register(RoadMarkingPlan)
class RoadMarkingPlanAdmin(
    DeviceTypeSearchAdminMixin,
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
                    "device_type",
                    "device_type_preview",
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
        "plan",
        "device_type_preview",
        "additional_info",
        "lifecycle",
        "location",
        "is_replaced_as_str",
    )
    list_filter = SoftDeleteAdminMixin.list_filter + [
        ("lifecycle", ChoicesFieldListFilter),
        "owner",
        RoadMarkingPlanReplacementListFilter,
    ]
    search_fields = (
        "additional_info",
        "created_by__email",
        "created_by__first_name",
        "created_by__last_name",
        "created_by__username",
        "device_type__code",
        "id",
        "plan__id",
        "plan__name",
        "road_name",
        "source_name",
        "traffic_sign_plan__id",
        "updated_by__email",
        "updated_by__first_name",
        "updated_by__last_name",
        "updated_by__username",
    )
    readonly_fields = (
        "device_type_preview",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    raw_id_fields = ("plan", "traffic_sign_plan")
    ordering = ("-created_at",)
    inlines = (
        RoadMarkingPlanFileInline,
        RoadMarkinRealInline,
        RoadMarkingPlanReplacesInline,
        RoadMarkingPlanReplacedByInline,
    )
    initial_values = shared_initial_values

    # Generated for RoadMarkingPlanAdmin at 2026-02-19 14:19:41+00:00
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        resolver_match = getattr(request, "resolver_match", None)
        if not resolver_match or not resolver_match.url_name:
            return qs

        if resolver_match.url_name.endswith("_changelist"):
            return qs.select_related(
                "device_type",  # n:1 relation in list_display (via device_type_preview -> TrafficControlDeviceTypeIcon.__str__) # noqa: E501
                "device_type__icon_file",  # n:1 relation chain in list_display (via device_type_preview -> TrafficControlDeviceTypeIcon.__str__) # noqa: E501
                "plan",  # n:1 relation in list_display, list_display (via Plan.__str__) # noqa: E501
                "replacement_to_new",  # 1:1 relation in list_display (via is_replaced_as_str) # noqa: E501
            )
        elif resolver_match.url_name.endswith("_change"):
            return qs.select_related(
                "created_by",  # n:1 relation in fieldsets, readonly_fields, readonly_fields (via User.__str__) # noqa: E501
                "device_type",  # n:1 relation in fieldsets, readonly_fields (via device_type_preview -> TrafficControlDeviceTypeIcon.__str__) # noqa: E501
                "device_type__icon_file",  # n:1 relation chain in readonly_fields (via device_type_preview -> TrafficControlDeviceTypeIcon.__str__) # noqa: E501
                "owner",  # n:1 relation in fieldsets, fieldsets (via Owner.__str__) # noqa: E501
                "plan",  # n:1 relation in fieldsets, fieldsets (via Plan.__str__) # noqa: E501
                "traffic_sign_plan",  # n:1 relation in fieldsets, fieldsets (via TrafficSignPlan.__str__) # noqa: E501
                "traffic_sign_plan__device_type",  # n:1 relation chain in fieldsets (via TrafficSignPlan.__str__) # noqa: E501
                "updated_by",  # n:1 relation in fieldsets, readonly_fields # noqa: E501
            )

        return qs


class RoadMarkingRealFileInline(admin.TabularInline):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidgetWithProxy},
    }
    model = RoadMarkingRealFile
    formset = CityInfraFileUploadFormset


class RoadMarkingRealOperationInline(TrafficControlOperationInlineBase):
    model = RoadMarkingRealOperation


@admin.register(RoadMarkingReal)
class RoadMarkingRealAdmin(
    DeviceTypeSearchAdminMixin,
    DeviceComparisonAdminMixin,
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
                    "device_type",
                    "device_type_preview",
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
    list_select_related = ("device_type", "device_type__icon_file")
    list_filter = SoftDeleteAdminMixin.list_filter + [
        ("lifecycle", ChoicesFieldListFilter),
        "owner",
    ]
    search_fields = ("id",)
    readonly_fields = (
        "device_type_preview",
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

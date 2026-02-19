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
    TrafficLightPlanModelForm,
    TrafficLightRealModelForm,
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
from traffic_control.models import TrafficLightPlan, TrafficLightPlanFile, TrafficLightReal, TrafficLightRealFile
from traffic_control.models.signpost import LocationSpecifier
from traffic_control.resources.common import CustomImportExportActionModelAdmin
from traffic_control.resources.traffic_light import (
    TrafficLightPlanResource,
    TrafficLightPlanToRealTemplateResource,
    TrafficLightRealResource,
)

__all__ = (
    "TrafficLightPlanAdmin",
    "TrafficLightPlanFileInline",
    "TrafficLightRealAdmin",
    "TrafficLightRealFileInline",
)

from traffic_control.models.traffic_light import TrafficLightPlanReplacement, TrafficLightRealOperation

shared_initial_values = {
    "lane_number": LaneNumber.MAIN_1,
    "lane_type": LaneType.MAIN,
    "location_specifier": LocationSpecifier.RIGHT,
}


@admin.register(TrafficLightPlanFile)
class TrafficSignPlanFileAdmin(GuardedModelAdmin, UploadsFileProxyMixin):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidgetWithProxy},
    }
    list_display = ("id", "file", "is_public")
    raw_id_fields = ("traffic_light_plan",)


@admin.register(TrafficLightRealFile)
class TrafficSignRealFileAdmin(GuardedModelAdmin, UploadsFileProxyMixin):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidgetWithProxy},
    }
    list_display = ("id", "file", "is_public")
    raw_id_fields = ("traffic_light_real",)


class TrafficLightRealInline(admin.TabularInline, PreviewDeviceTypeRelationMixin):
    model = TrafficLightReal
    verbose_name = _("Traffic Light Real")
    verbose_name_plural = _("Traffic Light Reals")
    fields = ("id", "device_type", "device_type_preview", "type")
    readonly_fields = ("id", "device_type", "device_type_preview", "type")
    show_change_link = True
    can_delete = False
    extra = 0


class TrafficLightPlanFileInline(admin.TabularInline):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidgetWithProxy},
    }
    model = TrafficLightPlanFile
    formset = CityInfraFileUploadFormset


class TrafficLightPlanReplacesInline(ReplacesInline):
    model = TrafficLightPlanReplacement


class TrafficLightPlanReplacedByInline(ReplacedByInline):
    model = TrafficLightPlanReplacement


class TrafficLightPlanReplacementListFilter(PlanReplacementListFilterMixin, SimpleListFilter):
    plan_model = TrafficLightPlan


@admin.register(TrafficLightPlan)
class TrafficLightPlanAdmin(
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
    resource_class = TrafficLightPlanResource
    extra_export_resource_classes = [TrafficLightPlanToRealTemplateResource]
    form = TrafficLightPlanModelForm
    fieldsets = (
        (
            _("General information"),
            {
                "fields": (
                    "owner",
                    "device_type",
                    "device_type_preview",
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
        "plan",
        "device_type_preview",
        "txt",
        "lifecycle",
        "location",
        "height",
        "is_replaced_as_str",
    )
    list_filter = SoftDeleteAdminMixin.list_filter + [
        ("lifecycle", ChoicesFieldListFilter),
        "owner",
        TrafficLightPlanReplacementListFilter,
    ]
    search_fields = (
        "created_by__email",
        "created_by__first_name",
        "created_by__last_name",
        "created_by__username",
        "device_type__code",
        "id",
        "mount_plan__id",
        "mount_type__code",
        "plan__id",
        "plan__name",
        "source_name",
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
    raw_id_fields = ("plan", "mount_plan")
    ordering = ("-created_at",)
    inlines = (
        TrafficLightPlanFileInline,
        TrafficLightRealInline,
        TrafficLightPlanReplacesInline,
        TrafficLightPlanReplacedByInline,
    )
    initial_values = shared_initial_values

    # Generated for TrafficLightPlanAdmin at 2026-02-19 12:27:24+00:00
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
                "mount_plan",  # n:1 relation in fieldsets, fieldsets (via MountPlan.__str__) # noqa: E501
                "mount_plan__mount_type",  # n:1 relation chain in fieldsets (via MountPlan.__str__) # noqa: E501
                "mount_type",  # n:1 relation in fieldsets, fieldsets (via MountType.__str__) # noqa: E501
                "owner",  # n:1 relation in fieldsets, fieldsets (via Owner.__str__) # noqa: E501
                "plan",  # n:1 relation in fieldsets, fieldsets (via Plan.__str__) # noqa: E501
                "updated_by",  # n:1 relation in fieldsets, readonly_fields # noqa: E501
            )

        return qs


class TrafficLightRealFileInline(admin.TabularInline):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidgetWithProxy},
    }
    model = TrafficLightRealFile
    formset = CityInfraFileUploadFormset


class TrafficLightRealOperationInline(TrafficControlOperationInlineBase):
    model = TrafficLightRealOperation


@admin.register(TrafficLightReal)
class TrafficLightRealAdmin(
    DeviceTypeSearchAdminMixin,
    DeviceComparisonAdminMixin,
    EnumChoiceValueDisplayAdminMixin,
    SoftDeleteAdminMixin,
    Geometry3DFieldAdminMixin,
    UserStampedAdminMixin,
    UserStampedInlineAdminMixin,
    AdminFieldInitialValuesMixin,
    admin.GISModelAdmin,
    AuditLogHistoryAdmin,
    CustomImportExportActionModelAdmin,
    PreviewDeviceTypeRelationMixin,
):
    plan_model_field_name = "traffic_light_plan"
    resource_class = TrafficLightRealResource
    form = TrafficLightRealModelForm
    fieldsets = (
        (
            _("General information"),
            {
                "fields": (
                    "owner",
                    "device_type",
                    "device_type_preview",
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
        "device_type_preview",
        "txt",
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
    raw_id_fields = ("traffic_light_plan", "mount_real")
    ordering = ("-created_at",)
    inlines = (TrafficLightRealFileInline, TrafficLightRealOperationInline)
    initial_values = {
        **shared_initial_values,
        "installation_status": InstallationStatus.IN_USE,
        "condition": Condition.VERY_GOOD,
    }

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
)
from traffic_control.enums import Condition, InstallationStatus, LaneNumber, LaneType
from traffic_control.forms import (
    AdminFileWidgetWithProxy,
    BarrierPlanModelForm,
    BarrierRealModelForm,
    CityInfraFileUploadFormset,
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
from traffic_control.models import BarrierPlan, BarrierPlanFile, BarrierReal, BarrierRealFile
from traffic_control.resources.barrier import (
    BarrierPlanResource,
    BarrierPlanToRealTemplateResource,
    BarrierRealResource,
)
from traffic_control.resources.common import CustomImportExportActionModelAdmin

__all__ = (
    "BarrierPlanAdmin",
    "BarrierPlanFileInline",
    "BarrierRealAdmin",
    "BarrierRealFileInline",
)

from traffic_control.models.barrier import BarrierPlanReplacement, BarrierRealOperation, LocationSpecifier

shared_initial_values = {
    "lane_number": LaneNumber.MAIN_1,
    "lane_type": LaneType.MAIN,
    "location_specifier": LocationSpecifier.RIGHT,
}


@admin.register(BarrierPlanFile)
class BarrierPlanFileAdmin(GuardedModelAdmin, UploadsFileProxyMixin):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidgetWithProxy},
    }
    list_display = ("id", "file_proxy", "is_public")
    raw_id_fields = ("barrier_plan",)


@admin.register(BarrierRealFile)
class BarrierRealFileAdmin(GuardedModelAdmin, UploadsFileProxyMixin):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidgetWithProxy},
    }
    list_display = ("id", "file_proxy", "is_public")
    raw_id_fields = ("barrier_real",)


class BarrierPlanFileInline(admin.TabularInline):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidgetWithProxy},
    }
    model = BarrierPlanFile
    formset = CityInfraFileUploadFormset


class BarrierRealInline(admin.TabularInline):
    model = BarrierReal
    verbose_name = _("Barrier real")
    verbose_name_plural = _("Barrier reals")
    fields = ("id", "connection_type", "device_type")
    readonly_fields = ("id", "connection_type", "device_type")
    show_change_link = True
    can_delete = False
    extra = 0

    def has_add_permission(self, request, obj):
        return False


class BarrierPlanReplacesInline(ReplacesInline):
    model = BarrierPlanReplacement


class BarrierPlanReplacedByInline(ReplacedByInline):
    model = BarrierPlanReplacement


class BarrierPlanReplacementListFilter(PlanReplacementListFilterMixin, SimpleListFilter):
    plan_model = BarrierPlan


@admin.register(BarrierPlan)
class BarrierPlanAdmin(
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
    resource_class = BarrierPlanResource
    extra_export_resource_classes = [BarrierPlanToRealTemplateResource]
    form = BarrierPlanModelForm
    fieldsets = (
        (
            _("General information"),
            {
                "fields": (
                    "owner",
                    "device_type",
                    "device_type_preview",
                    "is_electric",
                    "connection_type",
                    "count",
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
        (_("Physical properties"), {"fields": ("material", "reflective", "length")}),
        (_("Related models"), {"fields": ("plan",)}),
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
        "lifecycle",
        "location",
        "is_replaced_as_str",
    )
    list_filter = SoftDeleteAdminMixin.list_filter + [
        ("lifecycle", EnumFieldListFilter),
        "owner",
        BarrierPlanReplacementListFilter,
    ]
    search_fields = ("id",)
    readonly_fields = (
        "device_type_preview",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    raw_id_fields = ("plan",)
    ordering = ("-created_at",)
    inlines = (
        BarrierPlanFileInline,
        BarrierRealInline,
        BarrierPlanReplacesInline,
        BarrierPlanReplacedByInline,
    )
    initial_values = shared_initial_values

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("device_type")


class BarrierRealFileInline(admin.TabularInline):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidgetWithProxy},
    }
    model = BarrierRealFile
    formset = CityInfraFileUploadFormset


class BarrierRealOperationInline(TrafficControlOperationInlineBase):
    model = BarrierRealOperation


@admin.register(BarrierReal)
class BarrierRealAdmin(
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
    plan_model_field_name = "barrier_plan"
    resource_class = BarrierRealResource
    form = BarrierRealModelForm
    fieldsets = (
        (
            _("General information"),
            {
                "fields": (
                    "owner",
                    "device_type",
                    "device_type_preview",
                    "is_electric",
                    "connection_type",
                    "count",
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
            {"fields": ("material", "reflective", "length", "condition")},
        ),
        (_("Related models"), {"fields": ("barrier_plan",)}),
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
        "lifecycle",
        "location",
        "installation_date",
    )
    list_filter = SoftDeleteAdminMixin.list_filter + [
        ("lifecycle", EnumFieldListFilter),
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
    raw_id_fields = ("barrier_plan",)
    ordering = ("-created_at",)
    inlines = (BarrierRealFileInline, BarrierRealOperationInline)
    initial_values = {
        **shared_initial_values,
        "installation_status": InstallationStatus.IN_USE,
        "condition": Condition.VERY_GOOD,
    }

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("device_type")

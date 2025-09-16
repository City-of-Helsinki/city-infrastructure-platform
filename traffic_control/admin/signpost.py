from django.contrib.admin import SimpleListFilter
from django.contrib.gis import admin
from django.db import models
from django.utils.translation import gettext_lazy as _
from enumfields.admin import EnumFieldListFilter

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
from traffic_control.enums import Condition, InstallationStatus, LaneNumber, LaneType, Reflection, Size
from traffic_control.forms import (
    AdminFileWidget,
    CityInfraFileUploadFormset,
    SignpostPlanModelForm,
    SignpostRealModelForm,
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
from traffic_control.models import SignpostPlan, SignpostPlanFile, SignpostReal, SignpostRealFile
from traffic_control.resources.common import CustomImportExportActionModelAdmin
from traffic_control.resources.signpost import (
    SignpostPlanResource,
    SignpostPlanToRealTemplateResource,
    SignpostRealResource,
)

__all__ = (
    "SignpostPlanAdmin",
    "SignpostPlanFileInline",
    "SignpostRealAdmin",
    "SignpostRealFileInline",
)

from traffic_control.models.signpost import LocationSpecifier, SignpostPlanReplacement, SignpostRealOperation

shared_initial_values = {
    "lane_number": LaneNumber.MAIN_1,
    "lane_type": LaneType.MAIN,
    "size": Size.MEDIUM,
    "reflection_class": Reflection.R1,
    "location_specifier": LocationSpecifier.RIGHT,
}


class SignpostPlanFileInline(admin.TabularInline):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidget},
    }
    model = SignpostPlanFile
    formset = CityInfraFileUploadFormset


class SignpostPlanReplacesInline(ReplacesInline):
    model = SignpostPlanReplacement


class SignpostPlanReplacedByInline(ReplacedByInline):
    model = SignpostPlanReplacement


class SignpostPlanReplacementListFilter(PlanReplacementListFilterMixin, SimpleListFilter):
    plan_model = SignpostPlan


@admin.register(SignpostPlan)
class SignpostPlanAdmin(
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
    resource_class = SignpostPlanResource
    extra_export_resource_classes = [SignpostPlanToRealTemplateResource]
    form = SignpostPlanModelForm
    fieldsets = (
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
        (_("Physical properties"), {"fields": ("height", "size", "reflection_class", "double_sided")}),
        (_("Related models"), {"fields": ("parent", "plan", "mount_plan")}),
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
        "device_type",
        "txt",
        "lifecycle",
        "location",
        "is_replaced_as_str",
    )
    list_filter = SoftDeleteAdminMixin.list_filter + [
        ResponsibleEntityPermissionFilter,
        ("responsible_entity", TreeModelFieldListFilter),
        ("lifecycle", EnumFieldListFilter),
        "owner",
        SignpostPlanReplacementListFilter,
    ]
    search_fields = ("id",)
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    raw_id_fields = ("parent", "plan", "mount_plan")
    ordering = ("-created_at",)
    inlines = (
        SignpostPlanFileInline,
        SignpostPlanReplacesInline,
        SignpostPlanReplacedByInline,
    )
    initial_values = shared_initial_values

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("device_type")


class SignpostRealFileInline(admin.TabularInline):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidget},
    }
    model = SignpostRealFile
    formset = CityInfraFileUploadFormset


class SignpostRealOperationInline(TrafficControlOperationInlineBase):
    model = SignpostRealOperation


@admin.register(SignpostReal)
class SignpostRealAdmin(
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
    plan_model_field_name = "signpost_plan"
    resource_class = SignpostRealResource
    form = SignpostRealModelForm
    fieldsets = (
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
                    "height",
                    "size",
                    "reflection_class",
                    "material",
                    "condition",
                    "double_sided",
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
        "device_type",
        "txt",
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
    raw_id_fields = ("parent", "signpost_plan", "mount_real")
    ordering = ("-created_at",)
    inline = (SignpostRealFileInline, SignpostRealOperationInline)
    initial_values = {
        **shared_initial_values,
        "installation_status": InstallationStatus.IN_USE,
        "condition": Condition.VERY_GOOD,
    }

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("device_type")

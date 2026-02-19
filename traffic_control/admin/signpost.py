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
from traffic_control.enums import Condition, InstallationStatus, LaneNumber, LaneType, Reflection, Size
from traffic_control.forms import (
    AdminFileWidgetWithProxy,
    CityInfraFileUploadFormset,
    SignpostPlanModelForm,
    SignpostRealModelForm,
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


@admin.register(SignpostPlanFile)
class SignpostPlanFileAdmin(GuardedModelAdmin, UploadsFileProxyMixin):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidgetWithProxy},
    }
    list_display = ("id", "file_proxy", "is_public")
    raw_id_fields = ("signpost_plan",)


@admin.register(SignpostRealFile)
class SignpostRealFileAdmin(GuardedModelAdmin, UploadsFileProxyMixin):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidgetWithProxy},
    }
    list_display = ("id", "file_proxy", "is_public")
    raw_id_fields = ("signpost_real",)


class SignpostPlanFileInline(admin.TabularInline):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidgetWithProxy},
    }
    model = SignpostPlanFile
    formset = CityInfraFileUploadFormset


class SignpostRealInline(admin.TabularInline, PreviewDeviceTypeRelationMixin):
    model = SignpostReal
    verbose_name = _("Signpost Real")
    verbose_name_plural = _("Signpost Reals")
    fields = ("id", "device_type", "device_type_preview", "mount_type")
    readonly_fields = ("id", "device_type", "device_type_preview", "mount_type")
    show_change_link = True
    can_delete = False
    extra = 0


class SignpostPlanReplacesInline(ReplacesInline):
    model = SignpostPlanReplacement


class SignpostPlanReplacedByInline(ReplacedByInline):
    model = SignpostPlanReplacement


class SignpostPlanReplacementListFilter(PlanReplacementListFilterMixin, SimpleListFilter):
    plan_model = SignpostPlan


@admin.register(SignpostPlan)
class SignpostPlanAdmin(
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
    resource_class = SignpostPlanResource
    extra_export_resource_classes = [SignpostPlanToRealTemplateResource]
    form = SignpostPlanModelForm
    fieldsets = (
        (
            _("General information"),
            {
                "fields": (
                    "owner",
                    "electric_maintainer",
                    "device_type",
                    "device_type_preview",
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
        SignpostPlanReplacementListFilter,
    ]
    search_fields = (
        "created_by__email",
        "created_by__first_name",
        "created_by__last_name",
        "created_by__username",
        "device_type__code",
        "mount_plan__id",
        "mount_type__code",
        "id",
        "parent__id",
        "plan__id",
        "plan__name",
        "road_name",
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
    raw_id_fields = ("parent", "plan", "mount_plan")
    ordering = ("-created_at",)
    inlines = (
        SignpostPlanFileInline,
        SignpostRealInline,
        SignpostPlanReplacesInline,
        SignpostPlanReplacedByInline,
    )
    initial_values = shared_initial_values

    # Generated for SignpostPlanAdmin at 2026-02-19 12:44:25+00:00
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
                "parent",  # n:1 relation in fieldsets, fieldsets (via SignpostPlan.__str__) # noqa: E501
                "parent__device_type",  # n:1 relation chain in fieldsets (via SignpostPlan.__str__) # noqa: E501
                "plan",  # n:1 relation in fieldsets, fieldsets (via Plan.__str__) # noqa: E501
                "updated_by",  # n:1 relation in fieldsets, readonly_fields # noqa: E501
            )

        return qs


class SignpostRealFileInline(admin.TabularInline):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidgetWithProxy},
    }
    model = SignpostRealFile
    formset = CityInfraFileUploadFormset


class SignpostRealOperationInline(TrafficControlOperationInlineBase):
    model = SignpostRealOperation


@admin.register(SignpostReal)
class SignpostRealAdmin(
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
    plan_model_field_name = "signpost_plan"
    resource_class = SignpostRealResource
    form = SignpostRealModelForm
    fieldsets = (
        (
            _("General information"),
            {
                "fields": (
                    "owner",
                    "electric_maintainer",
                    "device_type",
                    "device_type_preview",
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
        "device_type_preview",
        "txt",
        "lifecycle",
        "location",
        "installation_date",
    )
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

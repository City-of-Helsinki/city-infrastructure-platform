from django.contrib.admin import ChoicesFieldListFilter
from django.contrib.gis import admin
from django.db import models
from django.utils.translation import gettext_lazy as _
from guardian.admin import GuardedModelAdmin

from city_furniture.forms import FurnitureSignpostPlanModelForm, FurnitureSignpostRealModelForm
from city_furniture.models import (
    FurnitureSignpostPlan,
    FurnitureSignpostPlanFile,
    FurnitureSignpostReal,
    FurnitureSignpostRealFile,
    FurnitureSignpostRealOperation,
)
from city_furniture.resources.furniture_signpost import (
    FurnitureSignpostPlanResource,
    FurnitureSignpostPlanTemplateResource,
    FurnitureSignpostRealResource,
)
from traffic_control.admin.audit_log import AuditLogHistoryAdmin
from traffic_control.admin.common import OperationalAreaListFilter, TrafficControlOperationInlineBase
from traffic_control.admin.utils import (
    AdminFieldInitialValuesMixin,
    DeviceComparisonAdminMixin,
    MultiResourceExportActionAdminMixin,
    ResponsibleEntityPermissionAdminMixin,
    ResponsibleEntityPermissionFilter,
    SimplifiedRelatedFieldListFilter,
    TreeModelFieldListFilter,
)
from traffic_control.enums import Condition, InstallationStatus
from traffic_control.forms import AdminFileWidgetWithProxy, CityInfraFileUploadFormset
from traffic_control.mixins import (
    EnumChoiceValueDisplayAdminMixin,
    Geometry3DFieldAdminMixin,
    PreviewDeviceTypeRelationMixin,
    SoftDeleteAdminMixin,
    UpdatePlanLocationAdminMixin,
    UploadsFileProxyMixin,
    UserStampedAdminMixin,
    UserStampedInlineAdminMixin,
)
from traffic_control.resources.common import CustomImportExportActionModelAdmin

__all__ = (
    "FurnitureSignpostPlanAdmin",
    "FurnitureSignpostPlanFileInline",
    "FurnitureSignpostRealAdmin",
    "FurnitureSignpostRealFileInline",
)


@admin.register(FurnitureSignpostPlanFile)
class FurnitureSignpostPlanFileAdmin(GuardedModelAdmin, UploadsFileProxyMixin):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidgetWithProxy},
    }
    list_display = ("id", "file_proxy", "is_public")
    raw_id_fields = ("furniture_signpost_plan",)


@admin.register(FurnitureSignpostRealFile)
class FurnitureSignpostRealFileAdmin(GuardedModelAdmin, UploadsFileProxyMixin):
    formfield_overrides = {
        models.FileField: {"widget": AdminFileWidgetWithProxy},
    }
    list_display = ("id", "file_proxy", "is_public")
    raw_id_fields = ("furniture_signpost_real",)


class FurnitureSignpostPlanFileInline(admin.TabularInline):
    formfield_overrides = {models.FileField: {"widget": AdminFileWidgetWithProxy}}
    model = FurnitureSignpostPlanFile
    formset = CityInfraFileUploadFormset


class FurnitureSignpostRealFileInline(admin.TabularInline):
    formfield_overrides = {models.FileField: {"widget": AdminFileWidgetWithProxy}}
    model = FurnitureSignpostRealFile
    formset = CityInfraFileUploadFormset


class FurnitureSignpostRealOperationInline(TrafficControlOperationInlineBase):
    model = FurnitureSignpostRealOperation


class FurnitureSignpostRealInline(admin.TabularInline):
    model = FurnitureSignpostReal
    verbose_name = _("Furniture Signpost Real")
    verbose_name_plural = _("Furniture Signpost Real")
    fields = ("id", "device_type")
    readonly_fields = ("id", "device_type")
    show_change_link = True
    can_delete = False
    extra = 0

    def has_add_permission(self, request, obj):
        return False


class AbstractFurnitureSignpostAdmin(
    ResponsibleEntityPermissionAdminMixin,
    EnumChoiceValueDisplayAdminMixin,
    SoftDeleteAdminMixin,
    UserStampedAdminMixin,
    Geometry3DFieldAdminMixin,
    AdminFieldInitialValuesMixin,
    admin.GISModelAdmin,
    AuditLogHistoryAdmin,
    CustomImportExportActionModelAdmin,
    PreviewDeviceTypeRelationMixin,
):
    ordering = ("-created_at",)
    list_filter = SoftDeleteAdminMixin.list_filter + [
        ResponsibleEntityPermissionFilter,
        ("responsible_entity", TreeModelFieldListFilter),
        ("owner", SimplifiedRelatedFieldListFilter),
        ("target", SimplifiedRelatedFieldListFilter),
        ("device_type", SimplifiedRelatedFieldListFilter),
        ("lifecycle", ChoicesFieldListFilter),
        OperationalAreaListFilter,
        ("created_by", SimplifiedRelatedFieldListFilter),
        "validity_period_start",
    ]
    readonly_fields = (
        "device_type_preview",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    list_select_related = ("device_type", "device_type__icon_file")

    _fieldset_general_information = (
        _("General information"),
        {
            "fields": (
                "owner",
                "responsible_entity",
                "device_type",
                "device_type_preview",
                "target",
                "mount_type",
                "additional_material_url",
                "source_id",
                "source_name",
            )
        },
    )
    _fieldset_location_information = (
        _("Location information"),
        {
            "fields": (
                "location",
                "z_coord",
                "location_ewkt",
                "location_name_fi",
                "location_name_sw",
                "location_name_en",
                "location_additional_info",
                "direction",
                "height",
            )
        },
    )
    _fieldset_physical_properties = (
        _("Content and physical properties"),
        {
            "fields": (
                "arrow_direction",
                "color",
                "pictogram",
                "value",
                "text_content_fi",
                "text_content_sw",
                "text_content_en",
                "content_responsible_entity",
                "size",
            )
        },
    )
    _fieldset_validity = (
        _("Validity"),
        {
            "fields": (
                "validity_period_start",
                "validity_period_end",
                "lifecycle",
            )
        },
    )
    _fieldset_metadata = (
        _("Metadata"),
        {"fields": (("created_at", "updated_at", "created_by", "updated_by"),)},
    )


@admin.register(FurnitureSignpostPlan)
class FurnitureSignpostPlanAdmin(
    MultiResourceExportActionAdminMixin,
    UpdatePlanLocationAdminMixin,
    AbstractFurnitureSignpostAdmin,
):
    resource_class = FurnitureSignpostPlanResource
    extra_export_resource_classes = [
        FurnitureSignpostPlanTemplateResource,
    ]
    form = FurnitureSignpostPlanModelForm
    fieldsets = (
        AbstractFurnitureSignpostAdmin._fieldset_general_information,
        AbstractFurnitureSignpostAdmin._fieldset_location_information,
        AbstractFurnitureSignpostAdmin._fieldset_physical_properties,
        (_("Related models"), {"fields": ("plan", "mount_plan", "parent")}),
        AbstractFurnitureSignpostAdmin._fieldset_validity,
        AbstractFurnitureSignpostAdmin._fieldset_metadata,
    )
    raw_id_fields = ("plan", "mount_plan", "parent")
    list_display = (
        "id",
        "plan",
        "device_type_preview",
        "text_content_fi",
        "location_name_fi",
        "lifecycle",
        "height",
    )
    list_filter = AbstractFurnitureSignpostAdmin.list_filter
    inlines = (FurnitureSignpostPlanFileInline, FurnitureSignpostRealInline)
    search_fields = (
        "created_by__email",
        "created_by__first_name",
        "created_by__last_name",
        "created_by__username",
        "device_type__code",
        "id",
        "mount_plan__id",
        "mount_type__code",
        "parent__id",
        "plan__id",
        "plan__name",
        "source_name",
        "updated_by__email",
        "updated_by__first_name",
        "updated_by__last_name",
        "updated_by__username",
    )

    # Generated for FurnitureSignpostPlanAdmin at 2026-02-20 07:47:59+00:00
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        resolver_match = getattr(request, "resolver_match", None)
        if not resolver_match or not resolver_match.url_name:
            return qs

        if resolver_match.url_name.endswith("_changelist"):
            return qs.select_related(
                "device_type",  # n:1 relation in list_display (via device_type_preview -> CityFurnitureDeviceTypeIcon.__str__) # noqa: E501
                "device_type__icon_file",  # n:1 relation chain in list_display (via device_type_preview -> CityFurnitureDeviceTypeIcon.__str__) # noqa: E501
                "plan",  # n:1 relation in list_display, list_display (via Plan.__str__) # noqa: E501
            )
        elif resolver_match.url_name.endswith("_change"):
            return qs.select_related(
                "color",  # n:1 relation in fieldsets, fieldsets (via CityFurnitureColor.__str__) # noqa: E501
                "created_by",  # n:1 relation in fieldsets, readonly_fields, readonly_fields (via User.__str__) # noqa: E501
                "device_type",  # n:1 relation in fieldsets, readonly_fields (via device_type_preview -> CityFurnitureDeviceTypeIcon.__str__) # noqa: E501
                "device_type__icon_file",  # n:1 relation chain in readonly_fields (via device_type_preview -> CityFurnitureDeviceTypeIcon.__str__) # noqa: E501
                "mount_plan",  # n:1 relation in fieldsets, fieldsets (via MountPlan.__str__) # noqa: E501
                "mount_plan__mount_type",  # n:1 relation chain in fieldsets (via MountPlan.__str__) # noqa: E501
                "mount_type",  # n:1 relation in fieldsets, fieldsets (via MountType.__str__) # noqa: E501
                "owner",  # n:1 relation in fieldsets, fieldsets (via Owner.__str__) # noqa: E501
                "parent",  # n:1 relation in fieldsets, fieldsets (via FurnitureSignpostPlan.__str__) # noqa: E501
                "parent__device_type",  # n:1 relation chain in fieldsets (via FurnitureSignpostPlan.__str__) # noqa: E501
                "plan",  # n:1 relation in fieldsets, fieldsets (via Plan.__str__) # noqa: E501
                "responsible_entity",  # n:1 relation in fieldsets # noqa: E501
                "target",  # n:1 relation in fieldsets, fieldsets (via CityFurnitureTarget.__str__) # noqa: E501
                "updated_by",  # n:1 relation in fieldsets, readonly_fields # noqa: E501
            )

        return qs


@admin.register(FurnitureSignpostReal)
class FurnitureSignpostRealAdmin(
    DeviceComparisonAdminMixin,
    UserStampedInlineAdminMixin,
    AbstractFurnitureSignpostAdmin,
):
    plan_model_field_name = "furniture_signpost_plan"
    resource_class = FurnitureSignpostRealResource
    form = FurnitureSignpostRealModelForm
    fieldsets = (
        AbstractFurnitureSignpostAdmin._fieldset_general_information,
        AbstractFurnitureSignpostAdmin._fieldset_location_information,
        AbstractFurnitureSignpostAdmin._fieldset_physical_properties,
        (_("Related models"), {"fields": ("furniture_signpost_plan", "mount_real", "parent")}),
        (
            _("Installation information"),
            {
                "fields": (
                    "installation_date",
                    "installation_status",
                    "condition",
                ),
            },
        ),
        AbstractFurnitureSignpostAdmin._fieldset_validity,
        AbstractFurnitureSignpostAdmin._fieldset_metadata,
    )
    raw_id_fields = ("furniture_signpost_plan", "mount_real", "parent")
    list_display = (
        "id",
        "device_type_preview",
        "text_content_fi",
        "location_name_fi",
        "lifecycle",
        "height",
    )
    list_filter = AbstractFurnitureSignpostAdmin.list_filter + [
        ("condition", ChoicesFieldListFilter),
        "installation_date",
    ]
    search_fields = (
        "value",
        "size",
        "height",
        "source_id",
        "source_name",
        "text_content_fi",
        "text_content_sw",
        "text_content_en",
        "location_name_fi",
        "location_name_en",
        "location_name_sw",
        "device_type__code",
        "id",
    )
    inlines = (FurnitureSignpostRealFileInline, FurnitureSignpostRealOperationInline)
    initial_values = {
        "installation_status": InstallationStatus.IN_USE,
        "condition": Condition.VERY_GOOD,
    }

    # Generated for FurnitureSignpostRealAdmin at 2026-02-20 07:48:15+00:00
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        resolver_match = getattr(request, "resolver_match", None)
        if not resolver_match or not resolver_match.url_name:
            return qs

        if resolver_match.url_name.endswith("_changelist"):
            return qs.select_related(
                "device_type",  # n:1 relation in list_display (via device_type_preview -> CityFurnitureDeviceTypeIcon.__str__) # noqa: E501
                "device_type__icon_file",  # n:1 relation chain in list_display (via device_type_preview -> CityFurnitureDeviceTypeIcon.__str__) # noqa: E501
            )
        elif resolver_match.url_name.endswith("_change"):
            return qs.select_related(
                "color",  # n:1 relation in fieldsets, fieldsets (via CityFurnitureColor.__str__) # noqa: E501
                "created_by",  # n:1 relation in fieldsets, readonly_fields, readonly_fields (via User.__str__) # noqa: E501
                "device_type",  # n:1 relation in fieldsets, readonly_fields (via device_type_preview -> CityFurnitureDeviceTypeIcon.__str__) # noqa: E501
                "device_type__icon_file",  # n:1 relation chain in readonly_fields (via device_type_preview -> CityFurnitureDeviceTypeIcon.__str__) # noqa: E501
                "furniture_signpost_plan",  # n:1 relation in fieldsets, fieldsets (via FurnitureSignpostPlan.__str__) # noqa: E501
                "furniture_signpost_plan__device_type",  # n:1 relation chain in fieldsets (via FurnitureSignpostPlan.__str__) # noqa: E501
                "mount_real",  # n:1 relation in fieldsets, fieldsets (via MountReal.__str__) # noqa: E501
                "mount_real__mount_type",  # n:1 relation chain in fieldsets (via MountReal.__str__) # noqa: E501
                "mount_type",  # n:1 relation in fieldsets, fieldsets (via MountType.__str__) # noqa: E501
                "owner",  # n:1 relation in fieldsets, fieldsets (via Owner.__str__) # noqa: E501
                "parent",  # n:1 relation in fieldsets # noqa: E501
                "responsible_entity",  # n:1 relation in fieldsets # noqa: E501
                "target",  # n:1 relation in fieldsets, fieldsets (via CityFurnitureTarget.__str__) # noqa: E501
                "updated_by",  # n:1 relation in fieldsets, readonly_fields # noqa: E501
            )

        return qs

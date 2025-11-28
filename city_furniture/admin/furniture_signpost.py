from django.contrib.gis import admin
from django.db import models
from django.utils.translation import gettext_lazy as _
from enumfields.admin import EnumFieldListFilter
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
        ("lifecycle", EnumFieldListFilter),
        OperationalAreaListFilter,
        ("created_by", SimplifiedRelatedFieldListFilter),
        "validity_period_start",
    ]
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    list_display = (
        "id",
        "device_type_preview",
        "location_name_fi",
        "lifecycle",
    )
    _fieldset_general_information = (
        _("General information"),
        {
            "fields": (
                "owner",
                "responsible_entity",
                "device_type",
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
    list_filter = AbstractFurnitureSignpostAdmin.list_filter
    inlines = (FurnitureSignpostPlanFileInline,)
    search_fields = (
        "device_type__code",
        "id",
    )


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
    list_filter = AbstractFurnitureSignpostAdmin.list_filter + [
        ("condition", EnumFieldListFilter),
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

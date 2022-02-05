from django.contrib.gis import admin
from django.db import models
from django.utils.translation import gettext_lazy as _
from enumfields.admin import EnumFieldListFilter

from city_furniture.forms import FurnitureSignpostPlanModelForm, FurnitureSignpostRealModelForm
from city_furniture.models import (
    FurnitureSignpostPlan,
    FurnitureSignpostPlanFile,
    FurnitureSignpostReal,
    FurnitureSignpostRealFile,
    FurnitureSignpostRealOperation,
)
from traffic_control.admin.audit_log import AuditLogHistoryAdmin
from traffic_control.admin.common import TrafficControlOperationInlineBase
from traffic_control.constants import HELSINKI_LATITUDE, HELSINKI_LONGITUDE
from traffic_control.forms import AdminFileWidget
from traffic_control.mixins import (
    EnumChoiceValueDisplayAdminMixin,
    Point3DFieldAdminMixin,
    SoftDeleteAdminMixin,
    UserStampedAdminMixin,
    UserStampedInlineAdminMixin,
)

__all__ = (
    "FurnitureSignpostPlanAdmin",
    "FurnitureSignpostPlanFileInline",
    "FurnitureSignpostRealAdmin",
    "FurnitureSignpostRealFileInline",
)


class FurnitureSignpostPlanFileInline(admin.TabularInline):
    formfield_overrides = {models.FileField: {"widget": AdminFileWidget}}
    model = FurnitureSignpostPlanFile


class FurnitureSignpostRealFileInline(admin.TabularInline):
    formfield_overrides = {models.FileField: {"widget": AdminFileWidget}}
    model = FurnitureSignpostRealFile


class FurnitureSignpostRealOperationInline(TrafficControlOperationInlineBase):
    model = FurnitureSignpostRealOperation


class AbstractFurnitureSignpostAdmin(
    EnumChoiceValueDisplayAdminMixin,
    SoftDeleteAdminMixin,
    UserStampedAdminMixin,
    Point3DFieldAdminMixin,
    admin.OSMGeoAdmin,
    AuditLogHistoryAdmin,
):
    default_lon = HELSINKI_LONGITUDE
    default_lat = HELSINKI_LATITUDE
    default_zoom = 12

    ordering = ("-created_at",)
    list_filter = SoftDeleteAdminMixin.list_filter + [
        "owner",
        "project_id",
        ("lifecycle", EnumFieldListFilter),
    ]
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "source_name",
        "source_id",
    )
    list_display = (
        "id",
        "device_type",
        "lifecycle",
        "location",
    )
    _fieldset_general_information = (
        _("General information"),
        {
            "fields": (
                "owner",
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
                ("location", "z_coord"),
                "location_name",
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
class FurnitureSignpostPlanAdmin(AbstractFurnitureSignpostAdmin):
    form = FurnitureSignpostPlanModelForm
    fieldsets = (
        AbstractFurnitureSignpostAdmin._fieldset_general_information,
        AbstractFurnitureSignpostAdmin._fieldset_location_information,
        AbstractFurnitureSignpostAdmin._fieldset_physical_properties,
        (_("Related models"), {"fields": ("plan", "mount_plan", "parent")}),
        AbstractFurnitureSignpostAdmin._fieldset_validity,
        AbstractFurnitureSignpostAdmin._fieldset_metadata,
    )
    raw_id_fields = ("plan", "mount_plan")
    list_filter = AbstractFurnitureSignpostAdmin.list_filter
    inlines = (FurnitureSignpostPlanFileInline,)


@admin.register(FurnitureSignpostReal)
class FurnitureSignpostRealAdmin(UserStampedInlineAdminMixin, AbstractFurnitureSignpostAdmin):
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
    raw_id_fields = ("furniture_signpost_plan", "mount_real")
    list_filter = AbstractFurnitureSignpostAdmin.list_filter + [
        ("condition", EnumFieldListFilter),
        ("installation_status", EnumFieldListFilter),
    ]
    search_fields = (
        "furniture_signpost_plan__id",
        "device_type__code",
        "device_type__description",
        "value",
        "size",
        "mount_real__id",
        "height",
        "owner",
        "source_id",
        "source_name",
    )
    inlines = (FurnitureSignpostRealFileInline, FurnitureSignpostRealOperationInline)
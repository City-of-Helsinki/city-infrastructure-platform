from django.contrib.gis import admin

from city_furniture.forms import CityFurnitureDeviceTypeForm, CityFurnitureDeviceTypeIconForm
from city_furniture.models.common import (
    CityFurnitureColor,
    CityFurnitureDeviceType,
    CityFurnitureDeviceTypeIcon,
    CityFurnitureTarget,
)
from traffic_control.admin.audit_log import AuditLogHistoryAdmin
from traffic_control.mixins import (
    EnumChoiceValueDisplayAdminMixin,
    PreviewIconFileRelationMixin,
    PreviewImageFileFieldMixin,
)

__all__ = ("CityFurnitureDeviceTypeAdmin",)


@admin.register(CityFurnitureDeviceType)
class CityFurnitureDeviceTypeAdmin(
    EnumChoiceValueDisplayAdminMixin,
    AuditLogHistoryAdmin,
    PreviewIconFileRelationMixin,
):
    form = CityFurnitureDeviceTypeForm
    list_display = (
        "id",
        "code",
        "class_type",
        "function_type",
        "icon_preview",
        "description_fi",
        "size",
        "target_model",
    )
    list_select_related = ("icon_file",)
    search_fields = ("id", "description_fi", "description_sw", "description_en")
    ordering = ("code", "class_type", "function_type")
    actions = None


@admin.register(CityFurnitureColor)
class CityFurnitureColorAdmin(AuditLogHistoryAdmin):
    list_display = (
        "id",
        "name",
        "rgb",
    )
    ordering = ("name",)
    actions = None


@admin.register(CityFurnitureTarget)
class CityFurnitureTargetAdmin(AuditLogHistoryAdmin):
    list_display = (
        "id",
        "name_fi",
        "name_sw",
        "name_en",
        "description",
        "source_id",
        "source_name",
    )
    search_fields = ("id",)
    ordering = ("name_fi",)
    actions = None


@admin.register(CityFurnitureDeviceTypeIcon)
class CityFurnitureDeviceTypeIconAdmin(admin.ModelAdmin, PreviewImageFileFieldMixin):
    form = CityFurnitureDeviceTypeIconForm
    list_display = ("id", "image_file_preview", "file")
    readonly_fields = ("image_file_preview",)
    search_fields = ("id", "file")

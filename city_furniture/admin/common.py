from django.contrib.gis import admin

from city_furniture.models.common import CityFurnitureColor, CityFurnitureDeviceType, CityFurnitureTarget
from traffic_control.admin.audit_log import AuditLogHistoryAdmin
from traffic_control.mixins import EnumChoiceValueDisplayAdminMixin

__all__ = ("CityFurnitureDeviceTypeAdmin",)


@admin.register(CityFurnitureDeviceType)
class CityFurnitureDeviceTypeAdmin(EnumChoiceValueDisplayAdminMixin, AuditLogHistoryAdmin):
    list_display = (
        "id",
        "code",
        "class_type",
        "function_type",
        "icon",
        "description_fi",
        "size",
        "target_model",
    )
    search_fields = ("id",)
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

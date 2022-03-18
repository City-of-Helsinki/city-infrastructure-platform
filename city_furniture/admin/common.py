from django.contrib.admin import RelatedFieldListFilter
from django.contrib.gis import admin

from city_furniture.models.common import (
    CityFurnitureColor,
    CityFurnitureDeviceType,
    CityFurnitureTarget,
    ResponsibleEntity,
)
from traffic_control.admin.audit_log import AuditLogHistoryAdmin
from traffic_control.mixins import EnumChoiceValueDisplayAdminMixin

__all__ = ("CityFurnitureDeviceTypeAdmin",)


class SimplifiedRelatedFieldListFilter(RelatedFieldListFilter):
    def field_choices(self, field, request, model_admin):
        """Return only choices, which are actually used."""
        ordering = self.field_admin_ordering(field, request, model_admin)
        used_ids = model_admin.model.objects.values_list(field.attname, flat=True).distinct()
        return field.get_choices(include_blank=False, ordering=ordering, limit_choices_to={"id__in": used_ids})


@admin.register(CityFurnitureDeviceType)
class CityFurnitureDeviceTypeAdmin(EnumChoiceValueDisplayAdminMixin, AuditLogHistoryAdmin):
    list_display = (
        "id",
        "code",
        "class_type",
        "function_type",
        "icon",
        "description",
        "size",
        "target_model",
    )
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
    ordering = ("name_fi",)
    actions = None


@admin.register(ResponsibleEntity)
class ResponsibleEntityAdmin(AuditLogHistoryAdmin):
    list_display = (
        "id",
        "name",
        "organization_level",
        "parent",
    )
    ordering = ("organization_level",)
    actions = None

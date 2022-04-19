from django import forms
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


class ResponsibleEntityAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        parent_choices = ((re.id, re) for re in ResponsibleEntity.objects.exclude(id=self.instance.id))
        self.fields["parent"].choices = (("", "---"), *parent_choices)


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
    form = ResponsibleEntityAdminForm

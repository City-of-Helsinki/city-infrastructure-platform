from typing import Type

import tablib
from django import forms
from django.contrib.admin import RelatedFieldListFilter
from django.contrib.admin.helpers import ActionForm
from django.contrib.gis import admin
from django.utils.translation import gettext_lazy as _
from import_export.resources import ModelResource

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


class MultiResourceExportActionAdminMixin:
    """Mixin to allow user to select the ModelResource to be used for exporting objects"""

    # List of ModelResource classes that can be used for exporting. Used only if more than 1 is specified.
    export_resource_classes: list[Type[ModelResource]] = []

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # Add a dropdown to select the used export resource
        export_resource_choices = []
        if len(self.export_resource_classes) > 1:
            export_resource_choices.append(("", "Default"))
            for i, rc in enumerate(self.export_resource_classes):
                export_resource_choices.append((str(i), rc.__name__))

            # Extract file_format choices from already created action_form
            file_format_choices = self.action_form.base_fields["file_format"].choices

            self.action_form = self.get_export_action_form(
                file_format_choices=file_format_choices,
                export_resource_choices=export_resource_choices,
            )

    def get_export_resource_class(self, **kwargs) -> Type[ModelResource]:
        """Return export resource class to be used for exporting"""
        request = kwargs.pop("request", None)
        export_resource = request.POST.get("export_resource_class", None)

        # Use default export_resource if nothing is specified
        if export_resource is None or export_resource == "":
            return super().get_export_resource_class()

        return self.export_resource_classes[int(export_resource)]

    def get_data_for_export(self, request, queryset, *args, **kwargs) -> tablib.Dataset:
        """Override super's method to pass `request` to `self.get_export_resource_class` as a kwarg"""
        resource_class: ModelResource = self.get_export_resource_class(request=request)()
        return resource_class.export(queryset, *args, **kwargs)

    @property
    def media(self) -> forms.Media:
        """Override js file to allows for selecting the export type"""
        super_media = super().media
        return forms.Media(js=super_media._js + ["city_furniture/action_formats.js"], css=super_media._css)

    @staticmethod
    def get_export_action_form(
        file_format_choices: list[tuple[str, str]],
        export_resource_choices: list[tuple[str, str]],
    ) -> Type[ActionForm]:
        """Returns an ActionForm subclass containing ChoiceFields populated with the given choices."""

        class _ExportActionForm(ActionForm):
            file_format = forms.ChoiceField(label=_("Format"), choices=file_format_choices, required=False)
            export_resource_class = forms.ChoiceField(
                label=_("Export resource"), choices=export_resource_choices, required=False
            )

        _ExportActionForm.__name__ = str("ExportActionForm")
        return _ExportActionForm

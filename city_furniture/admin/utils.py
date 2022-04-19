from typing import List, Tuple, Type

import tablib
from django import forms
from django.contrib.admin import RelatedFieldListFilter
from django.contrib.admin.helpers import ActionForm
from django.utils.translation import gettext_lazy as _
from import_export.resources import ModelResource


class SimplifiedRelatedFieldListFilter(RelatedFieldListFilter):
    def field_choices(self, field, request, model_admin):
        """Return only choices, which are actually used."""
        ordering = self.field_admin_ordering(field, request, model_admin)
        used_ids = model_admin.model.objects.values_list(field.attname, flat=True).distinct()
        return field.get_choices(include_blank=False, ordering=ordering, limit_choices_to={"id__in": used_ids})


class TreeModelFieldListFilter(RelatedFieldListFilter):
    def field_choices(self, field, request, model_admin):
        """Return only choices, which are actually used. Include children of selected object in the results"""

        used_ids = model_admin.model.objects.values_list(field.attname, flat=True).distinct()
        qs = field.related_model.objects.filter(pk__in=used_ids)

        # Include ancestors as available choices
        choice_ids = (
            field.related_model.objects.get_queryset_ancestors(qs, include_self=True)
            .values_list("id", flat=True)
            .distinct()
        )

        ordering = self.field_admin_ordering(field, request, model_admin)
        return field.get_choices(include_blank=False, ordering=ordering, limit_choices_to={"id__in": choice_ids})

    def queryset(self, request, queryset):
        """
        Remove old filter and replace it with a filter that includes children of selected object.
        This way when a parent is selected, objects belonging to a descendant are also included.
        """

        filter_used = self.used_parameters.pop(f"{self.field_path}__id__exact", None)
        if filter_used is not None:
            selected_object = self.field.related_model.objects.get(id=self.lookup_val)
            descendant_ids = selected_object.get_descendants(include_self=True).values_list("id", flat=True).distinct()
            self.used_parameters.update({f"{self.field_path}__id__in": descendant_ids})
        return super().queryset(request, queryset)


class MultiResourceExportActionAdminMixin:
    """Mixin to allow user to select the ModelResource to be used for exporting objects"""

    # List of ModelResource classes that can be used for exporting. Used only if more than 1 is specified.
    # `resource_class` is added as a default option to the list
    extra_export_resource_classes: List[Type[ModelResource]] = []

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # Add a dropdown to select the used export resource
        export_resource_choices = []
        if len(self.extra_export_resource_classes):
            export_resource_choices.append(("", "Default"))
            for i, rc in enumerate(self.extra_export_resource_classes):
                export_resource_choices.append((str(i), rc))

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

        return self.extra_export_resource_classes[int(export_resource)]

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
        file_format_choices: List[Tuple[str, str]],
        export_resource_choices: List[Tuple[str, str]],
    ) -> Type[ActionForm]:
        """Returns an ActionForm subclass containing ChoiceFields populated with the given choices."""

        class _ExportActionForm(ActionForm):
            file_format = forms.ChoiceField(label=_("Format"), choices=file_format_choices, required=False)
            export_resource_class = forms.ChoiceField(
                label=_("Export resource"), choices=export_resource_choices, required=False
            )

        _ExportActionForm.__name__ = str("ExportActionForm")
        return _ExportActionForm

import datetime
from typing import List, Tuple, Type

import tablib
from dateutil.relativedelta import relativedelta
from django import forms
from django.contrib.admin import DateFieldListFilter, RelatedFieldListFilter, SimpleListFilter
from django.contrib.admin.helpers import ActionForm
from django.contrib.admin.utils import unquote
from django.db import models
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from import_export.resources import ModelResource

from traffic_control.models import ResponsibleEntity


class CustomDateFieldListFilter(DateFieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        """
        Replace `this` filters with `last`
        e.g. instead of filtering results to `this calendar year`, filter to `past 365 days`.
        """
        super().__init__(field, request, params, model, model_admin, field_path)

        now = timezone.now()
        if isinstance(field, models.DateTimeField):
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:  # field is a models.DateField
            today = now.date()
        tomorrow = today + datetime.timedelta(days=1)

        self.lookup_kwarg_since = "%s__gte" % field_path
        self.lookup_kwarg_until = "%s__lt" % field_path
        self.links = (
            (_("Any date"), {}),
            (
                _("Today"),
                {
                    self.lookup_kwarg_since: str(today),
                    self.lookup_kwarg_until: str(tomorrow),
                },
            ),
            (
                _("Last 7 days"),
                {
                    self.lookup_kwarg_since: str(today - datetime.timedelta(days=7)),
                    self.lookup_kwarg_until: str(tomorrow),
                },
            ),
            (
                _("Last month"),
                {
                    self.lookup_kwarg_since: str(today - relativedelta(months=1)),
                    self.lookup_kwarg_until: str(tomorrow),
                },
            ),
            (
                _("Last 6 months"),
                {
                    self.lookup_kwarg_since: str(today - relativedelta(months=6)),
                    self.lookup_kwarg_until: str(tomorrow),
                },
            ),
            (
                _("Last year"),
                {
                    self.lookup_kwarg_since: str(today - relativedelta(years=1)),
                    self.lookup_kwarg_until: str(tomorrow),
                },
            ),
        )
        if field.null:
            self.lookup_kwarg_isnull = "%s__isnull" % field_path
            self.links += (
                (_("No date"), {self.field_generic + "isnull": "True"}),
                (_("Has date"), {self.field_generic + "isnull": "False"}),
            )


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


class ResponsibleEntityPermissionFilter(SimpleListFilter):
    title = _("Responsible Entity Permission")
    parameter_name = "responsible_entity_permission"

    def lookups(self, request, model_admin):
        # Don't show filter if user has access to all devices
        if request.user.bypass_responsible_entity or request.user.is_superuser:
            return []

        return [
            (True, "Has permission"),
            (False, "No permission"),
        ]

    def queryset(self, request, queryset):
        if not self.value():
            return queryset

        responsible_entity_qs = ResponsibleEntity.objects.filter(
            Q(pk__in=request.user.responsible_entities.all()) | Q(groups__group__user=request.user)
        )
        choice_ids = (
            ResponsibleEntity.objects.get_queryset_descendants(
                responsible_entity_qs,
                include_self=True,
            )
            .values_list("id", flat=True)
            .distinct()
        )

        if self.value() == "True":
            return queryset.filter(responsible_entity__pk__in=choice_ids)
        elif self.value() == "False":
            return queryset.exclude(responsible_entity__pk__in=choice_ids)


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
        return forms.Media(js=super_media._js + ["traffic_control/js/action_formats.js"], css=super_media._css)

    @staticmethod
    def get_export_action_form(
        file_format_choices: List[Tuple[str, str]],
        export_resource_choices: List[Tuple[str, str]],
    ) -> Type[ActionForm]:
        """Returns an ActionForm subclass containing ChoiceFields populated with the given choices."""

        class _ExportActionForm(ActionForm):
            file_format = forms.ChoiceField(label=_("Format"), choices=file_format_choices, required=False)
            export_resource_class = forms.ChoiceField(
                label=_("Export type"), choices=export_resource_choices, required=False
            )

        _ExportActionForm.__name__ = str("ExportActionForm")
        return _ExportActionForm


class ResponsibleEntityPermissionAdminMixin:
    def changelist_view(self, request, extra_context=None):
        """Use responsible_entity_permission=yes filter by default if user doesn't have access to all devices"""
        if not (request.user.bypass_responsible_entity or request.user.is_superuser) and (
            not request.META["QUERY_STRING"]  # No filters selected
            # Don't apply this filter if user modified filters (referer is from the same URL)
            and not request.META.get("HTTP_REFERER", "").startswith(request.build_absolute_uri())
        ):
            return HttpResponseRedirect(request.path + "?responsible_entity_permission=True")
        return super().changelist_view(request, extra_context=extra_context)

    def get_form(self, request, *args, **kwargs):
        form = super().get_form(request, *args, **kwargs)
        form.user = request.user
        return form

    def has_change_permission(self, request, obj=None):
        """User should be able to change devices that they have permission to"""
        if obj is not None and not request.user.has_responsible_entity_permission(obj.responsible_entity):
            return False
        return super().has_change_permission(request, obj=obj)

    def has_delete_permission(self, request, obj=None):
        """User should be able to delete devices that they have permission to"""
        if obj is not None and not request.user.has_responsible_entity_permission(obj.responsible_entity):
            return False
        return super().has_delete_permission(request, obj=obj)

    def has_add_permission(self, request):
        """User can't add new devices if they don't have any valid ResponsibleEntity targets"""
        if (
            not request.user.has_bypass_responsible_entity_permission()
            and not request.user.responsible_entities.count()
        ):
            return False
        return super().has_add_permission(request)

    def has_import_permission(self, request):
        """User can't import new devices if they don't have any valid ResponsibleEntity targets"""
        if (
            not request.user.has_bypass_responsible_entity_permission()
            and not request.user.responsible_entities.count()
        ):
            return False
        return super().has_import_permission(request)


class ResponsibleEntityPermissionAdminFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if (
            self.user is None
            or self.user.has_bypass_responsible_entity_permission()
            or "responsible_entity" not in self.fields  # Form is in read-only mode, so the field doesn't exist
        ):
            # Don't modify available choices, all ResponsibleEntities should be available
            return

        # Restrict available choices to ResponsibleEntities that are valid for logged in user
        responsible_entity_choices = []
        for i, entity in enumerate(self.user.responsible_entities.all().get_descendants(include_self=True)):
            responsible_entity_choices.append((str(i), entity))
        self.fields["responsible_entity"].choices = responsible_entity_choices


class DeviceComparisonAdminMixin:
    change_form_template = "admin/comparison/change_form.html"
    plan_model_field_name = None  # FK-Field to the Plan model which the Real object is compared against

    def get_real_and_plan_field_differences(self, real_object, plan_object) -> dict:
        def _should_ignore_field(f):
            ignored_fields = ["id", "parent", "created_at", "updated_at", "created_by", "updated_by"]
            return f.one_to_many or f.name in ignored_fields

        # Get common fields between Real and Plan object
        common_fields = set(f.name for f in real_object._meta.get_fields() if not _should_ignore_field(f)) & set(
            f.name for f in plan_object._meta.get_fields()
        )

        # Find fields that have different values between the Real and Plan
        differences = {}
        for field_name in common_fields:
            if getattr(real_object, field_name) != getattr(plan_object, field_name):
                differences[field_name] = getattr(plan_object, field_name)
        return differences

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """Add a dict containing Reals and Plans differences to context"""

        real_object = self.get_object(request, unquote(object_id), "id")
        plan_object = getattr(real_object, self.plan_model_field_name)

        if plan_object is not None:
            extra_context = extra_context or {}
            extra_context.update(
                {"plan_differences": self.get_real_and_plan_field_differences(real_object, plan_object)}
            )
        return super().change_view(request, object_id, form_url, extra_context)


class AdminFieldInitialValuesMixin:
    initial_values = {}

    def get_changeform_initial_data(self, request):
        return self.initial_values

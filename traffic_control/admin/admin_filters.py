import datetime

from dateutil.relativedelta import relativedelta
from django.contrib.admin import DateFieldListFilter, RelatedFieldListFilter, SimpleListFilter
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

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
            if isinstance(filter_used, list):
                filter_used = filter_used[0]

            # Retrieve the selected node and its descendants
            selected_object = self.field.related_model.objects.get(id=filter_used)
            descendant_ids = selected_object.get_descendants(include_self=True).values_list("id", flat=True)

            # Apply the filter directly to the queryset
            queryset = queryset.filter(**{f"{self.field_path}__id__in": descendant_ids})

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


class HeightFilter(SimpleListFilter):
    title = _("Height")
    parameter_name = "height_filter"

    def lookups(self, request, model_admin):
        return (
            ("null", _("Height is null")),
            ("zero", _("Height = 0m")),
            ("under_1_5", _("Height < 1.5m")),
            ("over_1_5", _("Height >= 1.5m")),
        )

    def queryset(self, request, queryset):
        value = self.value()

        if value == "null":
            return queryset.filter(height__isnull=True)
        elif value == "zero":
            return queryset.filter(height=0)
        elif value == "under_1_5":
            return queryset.filter(height__lt=150)
        elif value == "over_1_5":
            return queryset.filter(height__gte=150)

        return queryset


def as_dropdown(filter_class):
    """
    Takes any Django ListFilter class and forces it to use
    the custom dropdown template.
    """

    class DropdownFilter(filter_class):
        template = "admin/dropdown_filter.html"

    # Optional: Rename the class for cleaner debugging output
    DropdownFilter.__name__ = f"Dropdown{filter_class.__name__}"

    return DropdownFilter

import datetime

from dateutil.relativedelta import relativedelta
from django.contrib.admin import DateFieldListFilter, ListFilter, RelatedFieldListFilter, SimpleListFilter
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from traffic_control.enums import TagMatchMode
from traffic_control.models import ResponsibleEntity
from traffic_control.models.common import TrafficControlDeviceTypeTag


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
        raise ValueError(f"Unexpected value '{self.value()}' in ResponsibleEntityPermissionFilter")


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


class DeviceTypeTagFilter(ListFilter):
    """Sidebar filter allowing several device type tags to be selected at once.

    Supports repeated query parameters (``?tags=<uuid>&tags=<uuid>``) and a match mode
    parameter (``?tags_match=any|all``) that switches between OR and AND semantics.
    """

    title = _("Tags")
    parameter_name = "tags"
    match_parameter_name = "tags_match"
    template = "admin/multiselect_filter.html"

    MATCH_ANY = TagMatchMode.ANY
    MATCH_ALL = TagMatchMode.ALL

    def __init__(self, request, params, model, model_admin):
        super().__init__(request, params, model, model_admin)
        # Django keeps only the last value of a repeated parameter, so read the full list here.
        if self.parameter_name in params:
            self.used_parameters[self.parameter_name] = params.pop(self.parameter_name)
        if self.match_parameter_name in params:
            self.used_parameters[self.match_parameter_name] = params.pop(self.match_parameter_name)[-1]
        self.lookup_choices = list(self.lookups(model_admin))

    def lookups(self, model_admin) -> list[tuple[str, str]]:
        """
        List the tags that are actually assigned to at least one device type.

        Args:
            model_admin: The admin instance the filter is rendered for.

        Returns:
            list[tuple[str, str]]: Tag id and name pairs, ordered by name.
        """
        tags = TrafficControlDeviceTypeTag.objects.filter(device_types__isnull=False).distinct().order_by("name")
        return [(str(tag.pk), tag.name) for tag in tags]

    def has_output(self) -> bool:
        return bool(self.lookup_choices)

    def expected_parameters(self) -> list[str]:
        return [self.parameter_name, self.match_parameter_name]

    def value(self) -> list[str]:
        """
        Return the selected tag ids.

        Returns:
            list[str]: Selected tag ids, empty when the filter is unused.
        """
        return self.used_parameters.get(self.parameter_name, [])

    def match_mode(self) -> str:
        """
        Return the active match mode, defaulting to matching any selected tag.

        Returns:
            str: Either ``any`` or ``all``.
        """
        mode = self.used_parameters.get(self.match_parameter_name)
        return mode if mode == self.MATCH_ALL else self.MATCH_ANY

    def choices(self, changelist):
        """
        Build the context consumed by the multiselect filter template.

        Args:
            changelist: The admin changelist currently being rendered.

        Yields:
            dict: A single context entry holding tag options and match mode options.
        """
        selected = self.value()
        yield {
            "reset_query_string": changelist.get_query_string(remove=[self.parameter_name, self.match_parameter_name]),
            "base_query_string": changelist.get_query_string(remove=[self.parameter_name, self.match_parameter_name]),
            "parameter_name": self.parameter_name,
            "match_parameter_name": self.match_parameter_name,
            "match_mode": self.match_mode(),
            "selected": selected,
            "options": [
                {"value": value, "display": display, "selected": value in selected}
                for value, display in self.lookup_choices
            ],
        }

    def queryset(self, request, queryset):
        """
        Narrow the changelist to device types carrying the selected tags.

        Args:
            request: The current admin request.
            queryset (QuerySet): The changelist queryset to filter.

        Returns:
            QuerySet: Filtered queryset, unchanged when no tag is selected.
        """
        values = self.value()
        if not values:
            return queryset

        if self.match_mode() == self.MATCH_ALL:
            for value in values:
                queryset = queryset.filter(tags__pk=value)
            return queryset

        return queryset.filter(tags__pk__in=values).distinct()


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

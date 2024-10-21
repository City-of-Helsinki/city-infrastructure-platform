from django.contrib.gis.db.models import GeometryField
from django.utils.translation import gettext_lazy as _
from django_filters import CharFilter, ChoiceFilter, Filter, UUIDFilter
from django_filters.rest_framework import FilterSet
from rest_framework.exceptions import NotFound
from rest_framework_gis.filters import GeometryFilter

from traffic_control.enums import DeviceTypeTargetModel, TRAFFIC_SIGN_TYPE_CHOICES
from traffic_control.models import (
    AdditionalSignPlan,
    AdditionalSignReal,
    AdditionalSignRealOperation,
    BarrierPlan,
    BarrierReal,
    BarrierRealOperation,
    MountPlan,
    MountReal,
    MountRealOperation,
    MountType,
    OperationalArea,
    Owner,
    Plan,
    PortalType,
    ResponsibleEntity,
    RoadMarkingPlan,
    RoadMarkingReal,
    RoadMarkingRealOperation,
    SignpostPlan,
    SignpostReal,
    SignpostRealOperation,
    TrafficControlDeviceType,
    TrafficLightPlan,
    TrafficLightReal,
    TrafficLightRealOperation,
    TrafficSignPlan,
    TrafficSignReal,
    TrafficSignRealOperation,
)
from traffic_control.models.common import OperationType
from traffic_control.services.common import get_all_not_replaced_plans, get_all_replaced_plans


class OperationalAreaFilter(UUIDFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        if value:
            operational_area = OperationalArea.objects.filter(id=value).first()
            if operational_area is None:
                raise NotFound({"operational_area": f"Operational area with ID `{value}` was not found."})
            qs = qs.filter(location__contained=operational_area.location)
        return qs


class GenericMeta:
    model = None
    fields = "__all__"
    filter_overrides = {
        GeometryField: {
            "filter_class": GeometryFilter,
            "extra": lambda f: {"lookup_expr": "intersects"},
        },
    }


class PlanReplacementFilterSet(FilterSet):
    is_replaced = ChoiceFilter(
        label=_("If set to true, returns only plans that have been superseded by a new plan."),
        choices=(("All", "ALL"), ("true", "true"), ("false", "false")),
        method="filter_by_replacement",
        field_name="is_replaced",
    )

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        new_data = data.copy()
        if not data.get("is_replaced"):
            new_data.update({"is_replaced": "false"})
        super().__init__(data=new_data, queryset=queryset, request=request, prefix=prefix)

    def filter_by_replacement(self, queryset, name, value):
        if value == "true":
            return queryset.filter(id__in=get_all_replaced_plans(self.Meta.model))
        elif value == "false":
            return queryset.filter(id__in=get_all_not_replaced_plans(self.Meta.model))
        else:
            return queryset


class AdditionalSignPlanFilterSet(PlanReplacementFilterSet):
    class Meta(GenericMeta):
        model = AdditionalSignPlan
        exclude = ["content_s"]


class AdditionalSignRealFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = AdditionalSignReal
        exclude = ["content_s"]


class BarrierPlanFilterSet(PlanReplacementFilterSet):
    class Meta(GenericMeta):
        model = BarrierPlan


class BarrierRealFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = BarrierReal


class MountPlanFilterSet(PlanReplacementFilterSet):
    class Meta(GenericMeta):
        model = MountPlan


class MountRealFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = MountReal


class MountTypeFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = MountType


class OwnerFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = Owner


class PlanFilterSet(FilterSet):
    # Plan is searchable by single drawing number
    drawing_number = CharFilter(
        method="filter_by_drawing_number",
        field_name="drawing_numbers",
    )

    def filter_by_drawing_number(self, queryset, name, value):
        lookup = "__".join([name, "contains"])
        return queryset.filter(**{lookup: [value]})

    class Meta(GenericMeta):
        model = Plan
        exclude = ["drawing_numbers"]


class PortalTypeFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = PortalType


class RoadMarkingPlanFilterSet(PlanReplacementFilterSet):
    class Meta(GenericMeta):
        model = RoadMarkingPlan


class RoadMarkingRealFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = RoadMarkingReal


class SignpostPlanFilterSet(PlanReplacementFilterSet):
    class Meta(GenericMeta):
        model = SignpostPlan


class SignpostRealFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = SignpostReal


class TrafficLightPlanFilterSet(PlanReplacementFilterSet):
    class Meta(GenericMeta):
        model = TrafficLightPlan


class TrafficLightRealFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = TrafficLightReal


class TrafficControlDeviceTypeFilterSet(FilterSet):
    traffic_sign_type = ChoiceFilter(
        label=_("Traffic sign type"),
        choices=TRAFFIC_SIGN_TYPE_CHOICES,
        method="filter_traffic_sign_type",
    )

    target_model = ChoiceFilter(
        label=_("Target data model"),
        choices=DeviceTypeTargetModel.choices,
    )

    class Meta(GenericMeta):
        model = TrafficControlDeviceType
        exclude = ["content_schema"]

    def filter_traffic_sign_type(self, queryset, name, value):
        if value:
            queryset = queryset.filter(code__startswith=value)
        return queryset


class TrafficSignPlanFilterSet(PlanReplacementFilterSet):
    operational_area = OperationalAreaFilter()

    class Meta(GenericMeta):
        model = TrafficSignPlan


class TrafficSignRealFilterSet(FilterSet):
    operational_area = OperationalAreaFilter()

    class Meta(GenericMeta):
        model = TrafficSignReal


class OperationalAreaFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = OperationalArea


class OperationTypeFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = OperationType


# Operations
class BarrierRealOperationFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = BarrierRealOperation


class TrafficLightRealOperationFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = TrafficLightRealOperation


class TrafficSignRealOperationFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = TrafficSignRealOperation


class AdditionalSignRealOperationFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = AdditionalSignRealOperation


class MountRealOperationFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = MountRealOperation


class SignpostRealOperationFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = SignpostRealOperation


class RoadMarkingRealOperationFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = RoadMarkingRealOperation


class ResponsibleEntityFilter(Filter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        if value:
            selected_object = ResponsibleEntity.objects.filter(id=value).first()
            if selected_object is None:
                raise NotFound({"responsible_entity": f"Responsible Entity with ID `{value}` was not found."})

            descendant_ids = selected_object.get_descendants(include_self=True).values_list("id", flat=True).distinct()
            qs = qs.filter(responsible_entity__id__in=descendant_ids)
        return qs


class ResponsibleEntityFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = ResponsibleEntity

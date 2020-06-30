from django.contrib.gis.db.models import GeometryField
from django_filters.rest_framework import FilterSet
from rest_framework_gis.filters import GeometryFilter

from traffic_control.models import (
    AdditionalSignContentPlan,
    AdditionalSignContentReal,
    AdditionalSignPlan,
    AdditionalSignReal,
    BarrierPlan,
    BarrierReal,
    MountPlan,
    MountReal,
    MountType,
    Plan,
    PortalType,
    RoadMarkingPlan,
    RoadMarkingReal,
    SignpostPlan,
    SignpostReal,
    TrafficControlDeviceType,
    TrafficLightPlan,
    TrafficLightReal,
    TrafficSignPlan,
    TrafficSignReal,
)


class GenericMeta:
    model = None
    fields = "__all__"
    filter_overrides = {
        GeometryField: {
            "filter_class": GeometryFilter,
            "extra": lambda f: {"lookup_expr": "intersects"},
        },
    }


class AdditionalSignContentPlanFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = AdditionalSignContentPlan


class AdditionalSignContentRealFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = AdditionalSignContentReal


class AdditionalSignPlanFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = AdditionalSignPlan


class AdditionalSignRealFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = AdditionalSignReal


class BarrierPlanFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = BarrierPlan


class BarrierRealFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = BarrierReal


class MountPlanFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = MountPlan


class MountRealFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = MountReal


class MountTypeFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = MountType


class PlanFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = Plan


class PortalTypeFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = PortalType


class RoadMarkingPlanFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = RoadMarkingPlan


class RoadMarkingRealFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = RoadMarkingReal


class SignpostPlanFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = SignpostPlan


class SignpostRealFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = SignpostReal


class TrafficLightPlanFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = TrafficLightPlan


class TrafficLightRealFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = TrafficLightReal


class TrafficControlDeviceTypeFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = TrafficControlDeviceType


class TrafficSignPlanFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = TrafficSignPlan


class TrafficSignRealFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = TrafficSignReal

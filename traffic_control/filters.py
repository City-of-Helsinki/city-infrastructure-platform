from django.contrib.gis.db.models import GeometryField
from django_filters.rest_framework import FilterSet
from rest_framework_gis.filters import GeometryFilter

from traffic_control.models import (
    BarrierPlan,
    BarrierReal,
    MountPlan,
    MountReal,
    PortalType,
    RoadMarkingPlan,
    RoadMarkingReal,
    SignpostPlan,
    SignpostReal,
    TrafficLightPlan,
    TrafficLightReal,
    TrafficSignCode,
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


class TrafficSignCodeFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = TrafficSignCode


class TrafficSignPlanFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = TrafficSignPlan


class TrafficSignRealFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = TrafficSignReal

from django.contrib.gis.db.models import GeometryField
from django_filters.filterset import FilterSet
from rest_framework_gis.filters import GeometryFilter

from traffic_control.models import (
    BarrierPlan,
    BarrierReal,
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


class TrafficSignPlanFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = TrafficSignPlan


class TrafficSignRealFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = TrafficSignReal

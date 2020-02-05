from django.contrib.gis.db.models import GeometryField
from django_filters.filterset import FilterSet
from rest_framework_gis.filters import GeometryFilter

from traffic_control.models import TrafficSignPlan


class GenericMeta:
    model = None
    fields = "__all__"
    filter_overrides = {
        GeometryField: {
            "filter_class": GeometryFilter,
            "extra": lambda f: {"lookup_expr": "intersects"},
        },
    }


class TrafficSignPlanFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = TrafficSignPlan

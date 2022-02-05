from django_filters.rest_framework import FilterSet

from city_furniture.models import FurnitureSignpostPlan, FurnitureSignpostReal
from traffic_control.filters import GenericMeta


class FurnitureSignpostPlanFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = FurnitureSignpostPlan


class FurnitureSignpostRealFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = FurnitureSignpostReal

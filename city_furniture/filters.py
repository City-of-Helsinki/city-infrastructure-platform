from django_filters.rest_framework import FilterSet

from city_furniture.models import FurnitureSignpostPlan, FurnitureSignpostReal, FurnitureSignpostRealOperation
from city_furniture.models.common import CityFurnitureColor, CityFurnitureDeviceType, CityFurnitureTarget
from traffic_control.filters import GenericMeta


class FurnitureSignpostPlanFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = FurnitureSignpostPlan


class FurnitureSignpostRealFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = FurnitureSignpostReal


class FurnitureSignpostRealOperationFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = FurnitureSignpostRealOperation


class CityFurnitureDeviceTypeFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = CityFurnitureDeviceType


class CityFurnitureTargetFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = CityFurnitureTarget


class CityFurnitureColorFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = CityFurnitureColor

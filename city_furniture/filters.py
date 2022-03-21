from django_filters.rest_framework import FilterSet

from city_furniture.models import FurnitureSignpostPlan, FurnitureSignpostReal, FurnitureSignpostRealOperation
from city_furniture.models.common import (
    CityFurnitureColor,
    CityFurnitureDeviceType,
    CityFurnitureTarget,
    ResponsibleEntity,
)
from traffic_control.filters import GenericMeta, OperationalAreaFilter


class FurnitureSignpostPlanFilterSet(FilterSet):
    operational_area = OperationalAreaFilter()

    class Meta(GenericMeta):
        model = FurnitureSignpostPlan


class FurnitureSignpostRealFilterSet(FilterSet):
    operational_area = OperationalAreaFilter()

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


class ResponsibleEntityFilterSet(FilterSet):
    class Meta(GenericMeta):
        model = ResponsibleEntity

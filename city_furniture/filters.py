from django_filters import Filter
from django_filters.rest_framework import FilterSet
from rest_framework.exceptions import NotFound

from city_furniture.models import (
    FurnitureSignpostPlan,
    FurnitureSignpostReal,
    FurnitureSignpostRealOperation,
    ResponsibleEntity,
)
from city_furniture.models.common import CityFurnitureColor, CityFurnitureDeviceType, CityFurnitureTarget
from traffic_control.filters import GenericMeta, OperationalAreaFilter


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


class FurnitureSignpostPlanFilterSet(FilterSet):
    operational_area = OperationalAreaFilter()
    responsible_entity = ResponsibleEntityFilter()

    class Meta(GenericMeta):
        model = FurnitureSignpostPlan


class FurnitureSignpostRealFilterSet(FilterSet):
    operational_area = OperationalAreaFilter()
    responsible_entity = ResponsibleEntityFilter()

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

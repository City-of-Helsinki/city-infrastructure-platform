from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import ModelViewSet

from city_furniture.filters import CityFurnitureDeviceTypeFilterSet
from city_furniture.models.common import CityFurnitureDeviceType
from city_furniture.serializers.city_furniture_device_type import CityFurnitureDeviceTypeSerializer
from traffic_control.permissions import IsAdminUserOrReadOnly

__all__ = ("CityFurnitureDeviceTypeViewSet",)


@method_decorator(
    name="create",
    decorator=extend_schema(description="Create new CityFurnitureDeviceType"),
)
@method_decorator(
    name="list",
    decorator=extend_schema(description="Retrieve all CityFurnitureDeviceTypes"),
)
@method_decorator(
    name="retrieve",
    decorator=extend_schema(description="Retrieve single CityFurnitureDeviceType"),
)
@method_decorator(
    name="update",
    decorator=extend_schema(description="Update single CityFurnitureDeviceType"),
)
@method_decorator(
    name="partial_update",
    decorator=extend_schema(description="Partially update single CityFurnitureDeviceType"),
)
@method_decorator(
    name="destroy",
    decorator=extend_schema(description="Delete single CityFurnitureDeviceType"),
)
class CityFurnitureDeviceTypeViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = "__all__"
    ordering = ["code"]
    permission_classes = [IsAdminUserOrReadOnly]
    serializer_class = CityFurnitureDeviceTypeSerializer
    queryset = CityFurnitureDeviceType.objects.all()
    filterset_class = CityFurnitureDeviceTypeFilterSet

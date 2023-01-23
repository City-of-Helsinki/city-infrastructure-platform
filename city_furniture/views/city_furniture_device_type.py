from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import ModelViewSet

from city_furniture.filters import CityFurnitureDeviceTypeFilterSet
from city_furniture.models.common import CityFurnitureDeviceType
from city_furniture.serializers.city_furniture_device_type import CityFurnitureDeviceTypeSerializer
from traffic_control.permissions import IsAdminUserOrReadOnly

__all__ = ("CityFurnitureDeviceTypeViewSet",)


@extend_schema_view(
    create=extend_schema(summary="Create new CityFurnitureDeviceType"),
    list=extend_schema(summary="Retrieve all CityFurnitureDeviceTypes"),
    retrieve=extend_schema(summary="Retrieve single CityFurnitureDeviceType"),
    update=extend_schema(summary="Update single CityFurnitureDeviceType"),
    partial_update=extend_schema(summary="Partially update single CityFurnitureDeviceType"),
    destroy=extend_schema(summary="Soft-delete single CityFurnitureDeviceType"),
)
class CityFurnitureDeviceTypeViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = "__all__"
    ordering = ["code"]
    permission_classes = [IsAdminUserOrReadOnly]
    serializer_class = CityFurnitureDeviceTypeSerializer
    queryset = CityFurnitureDeviceType.objects.all()
    filterset_class = CityFurnitureDeviceTypeFilterSet

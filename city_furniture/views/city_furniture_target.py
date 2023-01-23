from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import ModelViewSet

from city_furniture.filters import CityFurnitureTargetFilterSet
from city_furniture.models.common import CityFurnitureTarget
from city_furniture.serializers.city_furniture_target import CityFurnitureTargetSerializer
from traffic_control.permissions import IsAdminUserOrReadOnly

__all__ = ("CityFurnitureTargetViewSet",)


@extend_schema_view(
    create=extend_schema(summary="Create new CityFurnitureTarget"),
    list=extend_schema(summary="Retrieve all CityFurnitureTargets"),
    retrieve=extend_schema(summary="Retrieve single CityFurnitureTarget"),
    update=extend_schema(summary="Update single CityFurnitureTarget"),
    partial_update=extend_schema(summary="Partially update single CityFurnitureTarget"),
    destroy=extend_schema(summary="Soft-delete single CityFurnitureTarget"),
)
class CityFurnitureTargetViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = "__all__"
    ordering = ["name_fi"]
    permission_classes = [IsAdminUserOrReadOnly]
    serializer_class = CityFurnitureTargetSerializer
    queryset = CityFurnitureTarget.objects.all()
    filterset_class = CityFurnitureTargetFilterSet

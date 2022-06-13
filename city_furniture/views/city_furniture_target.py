from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import ModelViewSet

from city_furniture.filters import CityFurnitureTargetFilterSet
from city_furniture.models.common import CityFurnitureTarget
from city_furniture.serializers.city_furniture_target import CityFurnitureTargetSerializer
from traffic_control.permissions import IsAdminUserOrReadOnly

__all__ = ("CityFurnitureTargetViewSet",)


@method_decorator(
    name="create",
    decorator=extend_schema(description="Create new CityFurnitureTarget"),
)
@method_decorator(
    name="list",
    decorator=extend_schema(description="Retrieve all CityFurnitureTargets"),
)
@method_decorator(
    name="retrieve",
    decorator=extend_schema(description="Retrieve single CityFurnitureTarget"),
)
@method_decorator(
    name="update",
    decorator=extend_schema(description="Update single CityFurnitureTarget"),
)
@method_decorator(
    name="partial_update",
    decorator=extend_schema(description="Partially update single CityFurnitureTarget"),
)
@method_decorator(
    name="destroy",
    decorator=extend_schema(description="Delete single CityFurnitureTarget"),
)
class CityFurnitureTargetViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = "__all__"
    ordering = ["name_fi"]
    permission_classes = [IsAdminUserOrReadOnly]
    serializer_class = CityFurnitureTargetSerializer
    queryset = CityFurnitureTarget.objects.all()
    filterset_class = CityFurnitureTargetFilterSet

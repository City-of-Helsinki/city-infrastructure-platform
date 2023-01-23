from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import ModelViewSet

from city_furniture.filters import CityFurnitureColorFilterSet
from city_furniture.models.common import CityFurnitureColor
from city_furniture.serializers.city_furniture_color import CityFurnitureColorSerializer
from traffic_control.permissions import IsAdminUserOrReadOnly

__all__ = ("CityFurnitureColorViewSet",)


@extend_schema_view(
    create=extend_schema(summary="Create new CityFurnitureColor"),
    list=extend_schema(summary="Retrieve all CityFurnitureColors"),
    retrieve=extend_schema(summary="Retrieve single CityFurnitureColor"),
    update=extend_schema(summary="Update single CityFurnitureColor"),
    partial_update=extend_schema(summary="Partially update single CityFurnitureColor"),
    destroy=extend_schema(summary="Soft-delete single CityFurnitureColor"),
)
class CityFurnitureColorViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = "__all__"
    ordering = ["name"]
    permission_classes = [IsAdminUserOrReadOnly]
    serializer_class = CityFurnitureColorSerializer
    queryset = CityFurnitureColor.objects.all()
    filterset_class = CityFurnitureColorFilterSet

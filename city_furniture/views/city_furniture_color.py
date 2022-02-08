from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import ModelViewSet

from city_furniture.filters import CityFurnitureColorFilterSet
from city_furniture.models.common import CityFurnitureColor
from city_furniture.serializers.city_furniture_color import CityFurnitureColorSerializer
from traffic_control.permissions import IsAdminUserOrReadOnly

__all__ = ("CityFurnitureColorViewSet",)


@method_decorator(
    name="create",
    decorator=swagger_auto_schema(operation_description="Create new CityFurnitureColor"),
)
@method_decorator(
    name="list",
    decorator=swagger_auto_schema(operation_description="Retrieve all CityFurnitureColors"),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(operation_description="Retrieve single CityFurnitureColor"),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(operation_description="Update single CityFurnitureColor"),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(operation_description="Partially update single CityFurnitureColor"),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(operation_description="Delete single CityFurnitureColor"),
)
class CityFurnitureColorViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = "__all__"
    ordering = ["name"]
    permission_classes = [IsAdminUserOrReadOnly]
    serializer_class = CityFurnitureColorSerializer
    queryset = CityFurnitureColor.objects.all()
    filterset_class = CityFurnitureColorFilterSet

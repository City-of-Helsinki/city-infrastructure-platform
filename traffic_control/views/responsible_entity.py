from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import ModelViewSet

from traffic_control.filters import ResponsibleEntityFilterSet
from traffic_control.models import ResponsibleEntity
from traffic_control.permissions import IsAdminUserOrReadOnly
from traffic_control.serializers.responsible_entity import ResponsibleEntitySerializer

__all__ = ("ResponsibleEntityViewSet",)


@method_decorator(
    name="create",
    decorator=swagger_auto_schema(operation_description="Create new ResponsibleEntity"),
)
@method_decorator(
    name="list",
    decorator=swagger_auto_schema(operation_description="Retrieve all ResponsibleEntitys"),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(operation_description="Retrieve single ResponsibleEntity"),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(operation_description="Update single ResponsibleEntity"),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(operation_description="Partially update single ResponsibleEntity"),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(operation_description="Delete single ResponsibleEntity"),
)
class ResponsibleEntityViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = "__all__"
    ordering = ["name"]
    permission_classes = [IsAdminUserOrReadOnly]
    serializer_class = ResponsibleEntitySerializer
    queryset = ResponsibleEntity.objects.all()
    filterset_class = ResponsibleEntityFilterSet

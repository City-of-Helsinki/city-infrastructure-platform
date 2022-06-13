from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import ModelViewSet

from traffic_control.filters import ResponsibleEntityFilterSet
from traffic_control.models import ResponsibleEntity
from traffic_control.permissions import IsAdminUserOrReadOnly
from traffic_control.serializers.responsible_entity import ResponsibleEntitySerializer

__all__ = ("ResponsibleEntityViewSet",)


@method_decorator(
    name="create",
    decorator=extend_schema(description="Create new ResponsibleEntity"),
)
@method_decorator(
    name="list",
    decorator=extend_schema(description="Retrieve all ResponsibleEntitys"),
)
@method_decorator(
    name="retrieve",
    decorator=extend_schema(description="Retrieve single ResponsibleEntity"),
)
@method_decorator(
    name="update",
    decorator=extend_schema(description="Update single ResponsibleEntity"),
)
@method_decorator(
    name="partial_update",
    decorator=extend_schema(description="Partially update single ResponsibleEntity"),
)
@method_decorator(
    name="destroy",
    decorator=extend_schema(description="Delete single ResponsibleEntity"),
)
class ResponsibleEntityViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = "__all__"
    ordering = ["name"]
    permission_classes = [IsAdminUserOrReadOnly]
    serializer_class = ResponsibleEntitySerializer
    queryset = ResponsibleEntity.objects.all()
    filterset_class = ResponsibleEntityFilterSet

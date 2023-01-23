from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import ModelViewSet

from traffic_control.filters import ResponsibleEntityFilterSet
from traffic_control.models import ResponsibleEntity
from traffic_control.permissions import IsAdminUserOrReadOnly
from traffic_control.serializers.responsible_entity import ResponsibleEntitySerializer

__all__ = ("ResponsibleEntityViewSet",)


@extend_schema_view(
    create=extend_schema(summary="Create new ResponsibleEntity"),
    list=extend_schema(summary="Retrieve all ResponsibleEntities"),
    retrieve=extend_schema(summary="Retrieve single ResponsibleEntity"),
    update=extend_schema(summary="Update single ResponsibleEntity"),
    partial_update=extend_schema(summary="Partially update single ResponsibleEntity"),
    destroy=extend_schema(summary="Delete single ResponsibleEntity"),
)
class ResponsibleEntityViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = "__all__"
    ordering = ["name"]
    permission_classes = [IsAdminUserOrReadOnly]
    serializer_class = ResponsibleEntitySerializer
    queryset = ResponsibleEntity.objects.all()
    filterset_class = ResponsibleEntityFilterSet

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import ModelViewSet

from traffic_control.filters import OperationTypeFilterSet
from traffic_control.models import OperationType
from traffic_control.permissions import IsAdminUserOrReadOnly
from traffic_control.serializers.opration_type import OperationTypeSerializer


@extend_schema_view(
    create=extend_schema(summary="Create new Operation Type"),
    list=extend_schema(summary="Retrieve all Operation Type"),
    retrieve=extend_schema(summary="Retrieve single Operation Type"),
    update=extend_schema(summary="Update single Operation Type"),
    partial_update=extend_schema(summary="Partially update single Operation Type"),
    destroy=extend_schema(summary="Delete single Operation Type"),
)
class OperationTypeViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = "__all__"
    ordering = ["id"]
    filterset_class = OperationTypeFilterSet
    permission_classes = [IsAdminUserOrReadOnly]
    serializer_class = OperationTypeSerializer
    queryset = OperationType.objects.all()

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import ModelViewSet

from traffic_control.filters import OperationalAreaFilterSet
from traffic_control.models import OperationalArea
from traffic_control.serializers.common import OperationalAreaSerializer


@extend_schema_view(
    create=extend_schema(summary="Create new Operational Area"),
    list=extend_schema(summary="Retrieve all Operational Area"),
    retrieve=extend_schema(summary="Retrieve single Operational Area"),
    update=extend_schema(summary="Update single Operational Area"),
    partial_update=extend_schema(summary="Partially update single Operational Area"),
    destroy=extend_schema(summary="Delete single Operational Area"),
)
class OperationalAreaViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = "__all__"
    ordering = ["name"]
    filterset_class = OperationalAreaFilterSet
    permission_classes = [IsAdminUser]
    serializer_class = OperationalAreaSerializer
    queryset = OperationalArea.objects.all()

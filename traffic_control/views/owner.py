from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.viewsets import ModelViewSet

from traffic_control.filters import OwnerFilterSet
from traffic_control.models import Owner
from traffic_control.permissions import IsAdminUserOrReadOnly
from traffic_control.serializers.common import OwnerSerializer


@extend_schema_view(
    create=extend_schema(summary="Create new Owner"),
    list=extend_schema(summary="Retrieve all Owners"),
    retrieve=extend_schema(summary="Retrieve single Owner"),
    update=extend_schema(summary="Update single Owner"),
    partial_update=extend_schema(summary="Partially update single Owner"),
    destroy=extend_schema(summary="Delete single Owner"),
)
class OwnerViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend]
    permission_classes = [IsAdminUserOrReadOnly]
    serializer_class = OwnerSerializer
    queryset = Owner.objects.all()
    filterset_class = OwnerFilterSet

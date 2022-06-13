from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework.viewsets import ModelViewSet

from traffic_control.filters import OwnerFilterSet
from traffic_control.models import Owner
from traffic_control.permissions import IsAdminUserOrReadOnly
from traffic_control.serializers.common import OwnerSerializer


@method_decorator(
    name="create",
    decorator=extend_schema(description="Create new Owner"),
)
@method_decorator(
    name="list",
    decorator=extend_schema(description="Retrieve all Owners"),
)
@method_decorator(
    name="retrieve",
    decorator=extend_schema(description="Retrieve single Owner"),
)
@method_decorator(
    name="update",
    decorator=extend_schema(description="Update single Owner"),
)
@method_decorator(
    name="partial_update",
    decorator=extend_schema(description="Partially update single Owner"),
)
@method_decorator(
    name="destroy",
    decorator=extend_schema(description="Delete single Owner"),
)
class OwnerViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend]
    permission_classes = [IsAdminUserOrReadOnly]
    serializer_class = OwnerSerializer
    queryset = Owner.objects.all()
    filterset_class = OwnerFilterSet

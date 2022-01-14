from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework.viewsets import ModelViewSet

from traffic_control.filters import OwnerFilterSet
from traffic_control.models import Owner
from traffic_control.permissions import IsAdminUserOrReadOnly
from traffic_control.serializers.common import OwnerSerializer


@method_decorator(
    name="create",
    decorator=swagger_auto_schema(operation_description="Create new Owner"),
)
@method_decorator(
    name="list",
    decorator=swagger_auto_schema(operation_description="Retrieve all Owners"),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(operation_description="Retrieve single Owner"),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(operation_description="Update single Owner"),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(operation_description="Partially update single Owner"),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(operation_description="Delete single Owner"),
)
class OwnerViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend]
    permission_classes = [IsAdminUserOrReadOnly]
    serializer_class = OwnerSerializer
    queryset = Owner.objects.all()
    filterset_class = OwnerFilterSet

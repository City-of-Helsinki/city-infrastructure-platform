from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import ModelViewSet

from traffic_control.models import OperationType
from traffic_control.serializers.opration_type import OperationTypeSerializer


@method_decorator(
    name="create",
    decorator=extend_schema(description="Create new Operation Type"),
)
@method_decorator(
    name="list",
    decorator=extend_schema(description="Retrieve all Operation Type"),
)
@method_decorator(
    name="retrieve",
    decorator=extend_schema(description="Retrieve single Operation Type"),
)
@method_decorator(
    name="update",
    decorator=extend_schema(description="Update single Operation Type"),
)
@method_decorator(
    name="partial_update",
    decorator=extend_schema(description="Partially update single Operation Type"),
)
@method_decorator(
    name="destroy",
    decorator=extend_schema(description="Delete single Operation Type"),
)
class OperationTypeViewSet(ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = OperationTypeSerializer
    queryset = OperationType.objects.all()

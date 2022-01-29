from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import ModelViewSet

from traffic_control.models import OperationType
from traffic_control.serializers.opration_type import OperationTypeSerializer


@method_decorator(
    name="create",
    decorator=swagger_auto_schema(operation_description="Create new Operation Type"),
)
@method_decorator(
    name="list",
    decorator=swagger_auto_schema(operation_description="Retrieve all Operation Type"),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(operation_description="Retrieve single Operation Type"),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(operation_description="Update single Operation Type"),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(operation_description="Partially update single Operation Type"),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(operation_description="Delete single Operation Type"),
)
class OperationTypeViewSet(ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = OperationTypeSerializer
    queryset = OperationType.objects.all()

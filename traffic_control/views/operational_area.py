from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import ModelViewSet

from traffic_control.models import OperationalArea
from traffic_control.serializers import OperationalAreaSerializer


@method_decorator(
    name="create",
    decorator=swagger_auto_schema(operation_description="Create new Operational Area"),
)
@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_description="Retrieve all Operational Area"
    ),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(
        operation_description="Retrieve single Operational Area"
    ),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(
        operation_description="Update single Operational Area"
    ),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(
        operation_description="Partially update single Operational Area"
    ),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(
        operation_description="Delete single Operational Area"
    ),
)
class OperationalAreaViewSet(ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = OperationalAreaSerializer
    queryset = OperationalArea.objects.all()

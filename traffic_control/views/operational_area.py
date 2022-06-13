from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import ModelViewSet

from traffic_control.models import OperationalArea
from traffic_control.serializers.common import OperationalAreaSerializer


@method_decorator(
    name="create",
    decorator=extend_schema(description="Create new Operational Area"),
)
@method_decorator(
    name="list",
    decorator=extend_schema(description="Retrieve all Operational Area"),
)
@method_decorator(
    name="retrieve",
    decorator=extend_schema(description="Retrieve single Operational Area"),
)
@method_decorator(
    name="update",
    decorator=extend_schema(description="Update single Operational Area"),
)
@method_decorator(
    name="partial_update",
    decorator=extend_schema(description="Partially update single Operational Area"),
)
@method_decorator(
    name="destroy",
    decorator=extend_schema(description="Delete single Operational Area"),
)
class OperationalAreaViewSet(ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = OperationalAreaSerializer
    queryset = OperationalArea.objects.all()

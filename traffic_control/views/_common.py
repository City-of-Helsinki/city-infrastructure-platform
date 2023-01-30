from django.core import exceptions
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from traffic_control.mixins import SoftDeleteMixin, UserCreateMixin, UserUpdateMixin
from traffic_control.permissions import ObjectInsideOperationalAreaOrAnonReadOnly
from traffic_control.schema import geo_format_parameter

__all__ = ("FileUploadViews", "TrafficControlViewSet", "OperationViewSet")


@extend_schema(methods=("get",), parameters=[geo_format_parameter])
class TrafficControlViewSet(ModelViewSet, UserCreateMixin, UserUpdateMixin, SoftDeleteMixin):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = "__all__"
    ordering = ["-created_at"]
    permission_classes = [
        DjangoModelPermissionsOrAnonReadOnly,
        ObjectInsideOperationalAreaOrAnonReadOnly,
    ]
    serializer_classes = {}

    def get_serializer_class(self):
        geo_format = self.request.query_params.get("geo_format")
        if geo_format == "geojson":
            return self.serializer_classes.get("geojson")
        return self.serializer_classes.get("default")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Check that the location of the to-be-created object is within the
        # user's operational area.
        user = request.user
        location = serializer.validated_data.get("location")
        if location and not user.location_is_in_operational_area(location):
            raise PermissionDenied("Location outside allowed operational area.")

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class FileUploadViews(GenericViewSet):
    file_queryset = None
    file_serializer = None
    file_relation = None

    def get_file_relation(self):
        return self.file_relation

    def get_file_serializer(self):
        return self.file_serializer

    @action(
        methods=("POST",),
        detail=True,
        url_path="files",
        parser_classes=(MultiPartParser,),
    )
    def post_files(self, request, *args, **kwargs):
        serializer_class = self.get_file_serializer()
        obj = self.get_object()
        serializer_cache = []
        files = []

        # Validate request data
        for _filename, file in request.data.items():
            serializer = serializer_class(data={self.get_file_relation(): obj.id, "file": file})
            serializer.is_valid(raise_exception=True)
            serializer_cache.append(serializer)

        # Validation passed - Proceed with saving everything
        for serializer in serializer_cache:
            serializer.save()
            files.append(serializer.data)

        return Response({"files": files})

    @action(
        methods=(
            "PATCH",
            "DELETE",
        ),
        detail=True,
        url_path="files/(?P<file_pk>[^/.]+)",
        parser_classes=(MultiPartParser,),
    )
    def change_file(self, request, file_pk, *args, **kwargs):
        if request.method == "DELETE":
            try:
                instance = self.file_queryset.get(id=file_pk)
            except exceptions.ObjectDoesNotExist:
                return Response({"detail": _("File not found.")}, status=status.HTTP_404_NOT_FOUND)

            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if request.method == "PATCH":
            instance = self.file_queryset.get(id=file_pk)
            serializer_class = self.get_file_serializer()
            serializer = serializer_class(instance=instance, data=request.data, partial=True)

            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(serializer.data)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class OperationViewSet(ModelViewSet, UserCreateMixin, UserUpdateMixin):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = "__all__"
    ordering = ["-created_at"]
    permission_classes = [
        DjangoModelPermissionsOrAnonReadOnly,
    ]
    serializer_classes = {}


class ResponsibleEntityPermission(permissions.BasePermission):
    message = "You do not have permissions to this Responsible Entity set"

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_authenticated and (
            request.user.has_bypass_responsible_entity_permission()
            or request.user.can_create_responsible_entity_devices()
        ):
            return True

        return False

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user.has_responsible_entity_permission(obj.responsible_entity)

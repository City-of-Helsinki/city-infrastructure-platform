from django.core import exceptions
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from traffic_control.mixins import SoftDeleteMixin, UserCreateMixin, UserUpdateMixin
from traffic_control.permissions import ObjectInsideOperationalAreaOrAnonReadOnly
from traffic_control.schema import geo_format_parameter
from traffic_control.services.virus_scan import add_virus_scan_errors_to_auditlog, get_error_details_message
from traffic_control.utils import get_file_upload_obstacles

__all__ = ("prefetch_replacements", "FileUploadViews", "TrafficControlViewSet", "OperationViewSet")


def prefetch_replacements(queryset):
    return queryset.prefetch_related("replacement_to_new", "replacement_to_old")


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

    def get_queryset(self):
        if self.action == "list":
            return self.get_list_queryset()
        return self.get_default_queryset()

    def get_default_queryset(self):
        return self.queryset

    def get_list_queryset(self):
        return self.get_default_queryset()

    def get_serializer_class(self):
        geo_format = self.request.query_params.get("geo_format")
        serializer_class = None

        if self.request.method == "GET":
            if geo_format == "geojson":
                serializer_class = self.serializer_classes.get("geojson")
            else:
                serializer_class = self.serializer_classes.get("default")
        else:
            if geo_format == "geojson":
                serializer_class = self.serializer_classes.get("geojson_input") or self.serializer_classes.get(
                    "geojson"
                )
            else:
                serializer_class = self.serializer_classes.get("input") or self.serializer_classes.get("default")

        return serializer_class

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
        output_serializer = self.serializer_classes.get("default")
        output_data = output_serializer(serializer.instance, context=serializer.context).data
        return Response(output_data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        output_serializer = self.serializer_classes.get("default")
        output_data = output_serializer(serializer.instance, context=serializer.context).data
        return Response(output_data)


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
        illegal_file_types, virus_scan_errors = get_file_upload_obstacles(request.data)
        if illegal_file_types:
            raise ValidationError(f"Illegal file types: {illegal_file_types}")
        if virus_scan_errors:
            add_virus_scan_errors_to_auditlog(virus_scan_errors, request.user, type(obj), object_id=None)
            raise ValidationError(f"Virus scan failure: {get_error_details_message(virus_scan_errors)}")

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
                obj = self.get_object()
                params = {"id": file_pk, self.get_file_relation(): obj.id}
                instance = self.file_queryset.get(**params)
            except exceptions.ObjectDoesNotExist:
                return Response({"detail": _("File not found.")}, status=status.HTTP_404_NOT_FOUND)

            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if request.method == "PATCH":
            instance = self.file_queryset.get(id=file_pk)
            illegal_file_types, virus_scan_errors = get_file_upload_obstacles(request.data)
            if illegal_file_types:
                raise ValidationError(f"Illegal file types: {illegal_file_types}")
            if virus_scan_errors:
                add_virus_scan_errors_to_auditlog(virus_scan_errors, request.user, type(instance), object_id=None)
                raise ValidationError(f"Virus scan failure: {get_error_details_message(virus_scan_errors)}")

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

from django.core import exceptions
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from ..mixins import SoftDeleteMixin, UserCreateMixin, UserUpdateMixin

__all__ = ("FileUploadViews", "location_parameter", "TrafficControlViewSet")

location_parameter = openapi.Parameter(
    "location",
    openapi.IN_QUERY,
    type=openapi.TYPE_STRING,
    description="Location (2D or 3D) to search from in WKT-format (EPSG:3879)",
    format="WKT",
)


class TrafficControlViewSet(
    ModelViewSet, UserCreateMixin, UserUpdateMixin, SoftDeleteMixin
):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = "__all__"
    ordering = ["-created_at"]
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    serializer_classes = {}

    def get_serializer_class(self):
        geo_format = self.request.query_params.get("geo_format")
        if geo_format == "geojson":
            return self.serializer_classes.get("geojson")
        return self.serializer_classes.get("default")


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
    def post_file(self, request, *args, **kwargs):
        obj = self.get_object()

        data = request.data.dict()
        data[self.get_file_relation()] = obj.id

        serializer_class = self.get_file_serializer()
        serializer = serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    @action(
        methods=("PATCH", "DELETE",),
        detail=True,
        url_path="files/(?P<file_pk>[^/.]+)",
        parser_classes=(MultiPartParser,),
    )
    def change_file(self, request, file_pk, *args, **kwargs):
        if request.method == "DELETE":
            try:
                instance = self.file_queryset.get(id=file_pk)
            except exceptions.ObjectDoesNotExist:
                return Response(
                    {"detail": _("File not found.")}, status=status.HTTP_404_NOT_FOUND
                )

            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if request.method == "PATCH":
            instance = self.file_queryset.get(id=file_pk)
            serializer_class = self.get_file_serializer()
            serializer = serializer_class(
                instance=instance, data=request.data, partial=True
            )

            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(serializer.data)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

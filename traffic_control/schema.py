from drf_yasg import openapi
from rest_framework import serializers

file_uuid_parameter = openapi.Parameter(
    "file_pk",
    openapi.IN_PATH,
    type=openapi.TYPE_STRING,
    format=openapi.FORMAT_UUID,
    description="File object UUID",
)


class FileUploadSchema(serializers.Serializer):
    """
    Serializer that is used to generate OpenAPI documentation for single file
    upload endpoints.
    """

    file = serializers.FileField(required=True, help_text="File to be uploaded.")


class MultiFileUploadSchema(serializers.Serializer):
    """
    Serializer that is used to generate OpenAPI documentation for multi file
    upload endpoints.
    """

    file = serializers.FileField(
        required=False,
        help_text=(
            "File to be uploaded. Form field name does not matter. Multiple files "
            "can be uploaded as long as the form field names are unique."
        ),
    )

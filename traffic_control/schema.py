from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.plumbing import build_bearer_security_scheme_object
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from enumfields import Enum
from rest_framework import serializers

location_parameter = OpenApiParameter(
    "location",
    {"type": "string", "format": "WKT"},
    description="Location (2D or 3D) to search from in WKT-format (EPSG:3879)",
)

file_uuid_parameter = OpenApiParameter(
    "file_pk",
    OpenApiTypes.UUID,
    location=OpenApiParameter.PATH,
    description="File object UUID",
)


def process_enum_values(generator, request, public, result):
    """
    To fix OpenAPI spec rendering, change each path's all possible
    enum parameter choices to be `Enum.value` instead of `Enum`.
    """

    for path, methods in result.get("paths").items():
        for method_name, method in methods.items():
            for parameter in method.get("parameters", []):
                enum = parameter.get("schema", {}).get("enum", [])
                for i, enum_value in enumerate(enum):
                    if isinstance(enum_value, Enum):
                        enum[i] = enum_value.value

    return result


class ApiTokenAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "helusers.oidc.ApiTokenAuthentication"
    name = "jwtAuth"

    def get_security_definition(self, auto_schema):
        return build_bearer_security_scheme_object(
            header_name="AUTHORIZATION",
            token_prefix="Bearer",
            bearer_format="JWT",
        )


class TrafficSignType(serializers.Serializer):
    """
    Serializer that is used to generate OpenAPI documentation for
    TrafficControlDeviceType model's traffic_sign_type attribute.
    """

    code = serializers.CharField(read_only=True)
    text = serializers.CharField(read_only=True)


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

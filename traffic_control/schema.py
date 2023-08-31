from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.plumbing import build_bearer_security_scheme_object
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import inline_serializer, OpenApiExample, OpenApiParameter
from enumfields import Enum
from rest_framework import serializers

location_search_parameter = OpenApiParameter(
    name="location",
    type={"type": "string", "format": "EWKT"},
    description="Location (2D or 3D) to search devices",
    required=False,
    examples=[
        # An empty example to make "Try it out" to not fill `location` with a value by default.
        OpenApiExample(name="--", value=""),
        OpenApiExample(
            name="2D polygon area (Katajanokka)",
            value="POLYGON (("
            + ", ".join(
                [
                    "25497733 6672927",
                    "25497946 6673032",
                    "25498653 6673034",
                    "25498987 6672708",
                    "25498314 6672170",
                    "25497651 6672629",
                    "25497646 6672775",
                    "25497733 6672927",
                ]
            )
            + "))",
        ),
    ],
)

geo_format_parameter = OpenApiParameter(
    name="geo_format",
    enum=("default", "geojson"),
    required=False,
    description="Determine whether the location should be in EWKT (default) or GeoJSON format.",
)


file_uuid_parameter = OpenApiParameter(
    name="file_pk",
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.PATH,
    description="File object UUID",
)


def file_create_serializer(file_serializer: serializers.ModelSerializer):
    """
    Return the schema (inline serializer) for file post successful response.
    """
    name = file_serializer.Meta.model.__name__ + "CreateResponse"
    return inline_serializer(
        name=name,
        fields={
            "files": file_serializer(many=True),
        },
    )


def process_enum_values(generator, request, public, result):
    """
    To fix OpenAPI spec rendering, change each path's all possible
    enum parameter choices to be `Enum.value` instead of `Enum`.
    """

    def enum_choice_index(enum_choice, enum_class) -> int:
        return list(map(lambda x: x[0], enum_class.choices())).index(enum_choice.value)

    for methods in result.get("paths", {}).values():
        for method in methods.values():
            for parameter in method.get("parameters", []):
                enum_values = parameter.get("schema", {}).get("enum", [])
                # Expect that if the first enum value is an Enum, then all of them are.
                if enum_values and isinstance(enum_values[0], Enum):
                    # List values in the same order as they are in the enum class.
                    enum_values.sort(key=lambda x: enum_choice_index(x, type(x)))
                    enum_values[:] = [enum_value.value for enum_value in enum_values]

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

from rest_framework import serializers


def get_single_object_serializer(
    serializer_class: serializers.ModelSerializer | serializers.ListSerializer,
) -> serializers.ModelSerializer:
    """Resolve the child serializer of a list field, or the main serializer for single object field."""
    if isinstance(serializer_class, serializers.ListSerializer):
        return serializer_class.child
    return serializer_class

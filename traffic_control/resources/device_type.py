from import_export.resources import ModelResource

from traffic_control.models import TrafficControlDeviceType
from traffic_control.resources.common import EnumFieldResourceMixin, ResourceUUIDField, UUIDWidget


class TrafficControlDeviceTypeResource(EnumFieldResourceMixin, ModelResource):
    """Traffic control device type resource for import/export."""

    id = ResourceUUIDField(attribute="id", column_name="id", default=None, widget=UUIDWidget())

    class Meta:
        model = TrafficControlDeviceType
        fields = (
            "id",
            "code",
            "icon",
            "description",
            "value",
            "unit",
            "size",
            "legacy_code",
            "legacy_description",
            "target_model",
            "type",
            "content_schema",
        )
        export_order = fields
        clean_model_instances = True
        # Force None and empty strings to be always "" in imports.
        widgets = {
            "icon": {"allow_blank": True, "coerce_to_string": True},
            "description": {"allow_blank": True, "coerce_to_string": True},
            "size": {"allow_blank": True, "coerce_to_string": True},
            "unit": {"allow_blank": True, "coerce_to_string": True},
            "value": {"allow_blank": True, "coerce_to_string": True},
            "legacy_code": {"allow_blank": True, "coerce_to_string": True},
            "legacy_description": {"allow_blank": True, "coerce_to_string": True},
        }

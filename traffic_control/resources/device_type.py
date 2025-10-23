from import_export.fields import Field
from import_export.resources import Diff, ModelResource
from import_export.widgets import ForeignKeyWidget

from traffic_control.models import (
    TrafficControlDeviceType,
    TrafficControlDeviceTypeIcon,
)
from traffic_control.resources.common import EnumFieldResourceMixin


class TrafficControlDeviceTypeDiff(Diff):
    """Diff wrapper not to show ID field in preview
    This is abit of an hack as it overrides private function from Diff class.
    Will be broken if import_export.resources.fields.Field implementation is changed so that column_name member
    is renamed to something else
    """

    def _export_resource_fields(self, resource, instance):
        return [
            resource.export_field(f, instance) if instance else ""
            for f in filter(lambda x: x.column_name != "id", resource.get_user_visible_fields())
        ]


class TrafficControlDeviceTypeResource(EnumFieldResourceMixin, ModelResource):
    """Traffic control device type resource for import/export."""

    icon_file = Field(
        attribute="icon_file",
        column_name="icon_file",
        widget=ForeignKeyWidget(TrafficControlDeviceTypeIcon, "file"),
    )

    class Meta:
        model = TrafficControlDeviceType
        fields = (
            "code",
            "icon_file",
            "description",
            "value",
            "unit",
            "size",
            "legacy_code",
            "legacy_description",
            "target_model",
            "type",
            "content_schema",
            "id",
        )
        export_order = fields
        clean_model_instances = True
        # Force None and empty strings to be always "" in imports.
        widgets = {
            "description": {"allow_blank": True, "coerce_to_string": True},
            "size": {"allow_blank": True, "coerce_to_string": True},
            "unit": {"allow_blank": True, "coerce_to_string": True},
            "value": {"allow_blank": True, "coerce_to_string": True},
            "legacy_code": {"allow_blank": True, "coerce_to_string": True},
            "legacy_description": {"allow_blank": True, "coerce_to_string": True},
        }
        import_id_fields = ["code"]

    def dehydrate_icon_file(self, obj: TrafficControlDeviceType):
        return obj.icon_file.file.name if obj.icon_file and obj.icon_file.file else ""

    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        """ID field is just informative when creating export file"""
        if "id" in dataset.headers:
            del dataset["id"]

    def get_diff_class(self):
        return TrafficControlDeviceTypeDiff

    def get_diff_headers(self):
        """Just to remove id column from import preview"""
        return list(filter(lambda x: x != "id", super().get_diff_headers()))

from import_export.fields import Field
from import_export.resources import Diff, ModelResource
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget

from traffic_control.models import (
    TrafficControlDeviceType,
    TrafficControlDeviceTypeIcon,
)
from traffic_control.models.common import TrafficControlDeviceTypeTag
from traffic_control.resources.common import EnumFieldResourceMixin

TAG_SEPARATOR = ","


class TrafficControlDeviceTypeTagWidget(ManyToManyWidget):
    """Widget that resolves device type tags by name, creating missing tags on import."""

    def clean(self, value, row=None, **kwargs) -> list:
        """
        Convert a separated string of tag names into tag instances.

        Args:
            value: Raw cell value containing separated tag names.
            row: The row being imported.

        Returns:
            list: Tag instances matching the given names, created when missing.
        """
        if not value:
            return []

        names = [name.strip() for name in str(value).split(self.separator)]
        return [TrafficControlDeviceTypeTag.objects.get_or_create(name=name)[0] for name in names if name]


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

    tags = Field(
        attribute="tags",
        column_name="tags",
        widget=TrafficControlDeviceTypeTagWidget(
            TrafficControlDeviceTypeTag,
            separator=TAG_SEPARATOR,
            field="name",
        ),
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
            "tags",
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

    def dehydrate_tags(self, obj: TrafficControlDeviceType) -> str:
        """
        Export tags as a separated list of tag names.

        Args:
            obj (TrafficControlDeviceType): The device type being exported.

        Returns:
            str: Sorted tag names joined by the tag separator.
        """
        if not obj.pk:
            return ""
        return f"{TAG_SEPARATOR}".join(sorted(obj.tags.values_list("name", flat=True)))

    def before_import(self, dataset, **kwargs):
        """ID field is just informative when creating export file"""
        super().before_import(dataset, **kwargs)
        if "id" in dataset.headers:
            del dataset["id"]

    def get_diff_class(self):
        return TrafficControlDeviceTypeDiff

    def get_diff_headers(self):
        """Just to remove id column from import preview"""
        return list(filter(lambda x: x != "id", super().get_diff_headers()))

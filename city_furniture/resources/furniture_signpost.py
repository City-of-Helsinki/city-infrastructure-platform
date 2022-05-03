from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget

from city_furniture.models import FurnitureSignpostPlan, FurnitureSignpostReal
from city_furniture.models.common import CityFurnitureColor, CityFurnitureDeviceType, CityFurnitureTarget
from traffic_control.enums import Condition, Lifecycle
from traffic_control.models import MountPlan, MountReal, MountType, Owner, Plan, ResponsibleEntity
from traffic_control.resources.common import (
    GenericDeviceBaseResource,
    ResourceEnumIntegerField,
    ResponsibleEntityPermissionImportMixin,
)


class AbstractFurnitureSignpostResource(ResponsibleEntityPermissionImportMixin, GenericDeviceBaseResource):
    lifecycle = ResourceEnumIntegerField(
        attribute="lifecycle", column_name="lifecycle", enum=Lifecycle, default=Lifecycle.ACTIVE
    )
    owner__name_fi = Field(attribute="owner", column_name="owner__name_fi", widget=ForeignKeyWidget(Owner, "name_fi"))
    responsible_entity__name = Field(
        attribute="responsible_entity",
        column_name="responsible_entity__name",
        widget=ForeignKeyWidget(ResponsibleEntity, "name"),
    )
    device_type__code = Field(
        attribute="device_type",
        column_name="device_type__code",
        widget=ForeignKeyWidget(CityFurnitureDeviceType, "code"),
    )
    mount_type__code = Field(
        attribute="mount_type", column_name="mount_type__code", widget=ForeignKeyWidget(MountType, "code")
    )
    target__name_fi = Field(
        attribute="target", column_name="target__name_fi", widget=ForeignKeyWidget(CityFurnitureTarget, "name_fi")
    )
    color__name = Field(
        attribute="color", column_name="color__name", widget=ForeignKeyWidget(CityFurnitureColor, "name")
    )

    class Meta(GenericDeviceBaseResource.Meta):
        exclude = (
            "is_active",
            "deleted_at",
            "deleted_by",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        )
        common_fields = (
            "id",
            "owner__name_fi",
            "responsible_entity__name",
            "location",
            "location_name_fi",
            "location_name_sw",
            "location_name_en",
            "location_additional_info",
            "direction",
            "device_type__code",
            "color__name",
            "height",
            "mount_type__code",
            "parent__id",
            "order",
            "pictogram",
            "value",
            "size",
            "arrow_direction",
            "target__name_fi",
            "content_responsible_entity",
            "text_content_fi",
            "text_content_sw",
            "text_content_en",
            "validity_period_start",
            "validity_period_end",
            "additional_material_url",
            "lifecycle",
        )


class FurnitureSignpostPlanResource(AbstractFurnitureSignpostResource):
    parent__id = Field(
        attribute="parent", column_name="parent__id", widget=ForeignKeyWidget(FurnitureSignpostPlan, "id")
    )
    mount_plan__id = Field(
        attribute="mount_plan",
        column_name="mount_plan__id",
        widget=ForeignKeyWidget(MountPlan, "id"),
    )
    plan__plan_number = Field(
        attribute="plan",
        column_name="plan__plan_number",
        widget=ForeignKeyWidget(Plan, "plan_number"),
    )

    class Meta(AbstractFurnitureSignpostResource.Meta):
        model = FurnitureSignpostPlan

        fields = AbstractFurnitureSignpostResource.Meta.common_fields + (
            "mount_plan__id",
            "plan__plan_number",
        )
        export_order = fields


class FurnitureSignpostRealResource(AbstractFurnitureSignpostResource):
    parent__id = Field(
        attribute="parent", column_name="parent__id", widget=ForeignKeyWidget(FurnitureSignpostReal, "id")
    )
    condition = ResourceEnumIntegerField(
        attribute="condition", column_name="condition", enum=Condition, default=Condition.VERY_GOOD
    )
    furniture_signpost_plan__id = Field(
        attribute="furniture_signpost_plan",
        column_name="furniture_signpost_plan__id",
        widget=ForeignKeyWidget(FurnitureSignpostPlan, "id"),
    )
    mount_real__id = Field(
        attribute="mount_real",
        column_name="mount_real__id",
        widget=ForeignKeyWidget(MountReal, "id"),
    )

    class Meta(AbstractFurnitureSignpostResource.Meta):
        model = FurnitureSignpostReal

        fields = AbstractFurnitureSignpostResource.Meta.common_fields + (
            "condition",
            "installation_date",
            "furniture_signpost_plan__id",
            "mount_real__id",
        )
        export_order = fields


class FurnitureSignpostPlanTemplateResource(AbstractFurnitureSignpostResource):
    """Resource for exporting a Plan and making the output importable as a real"""

    parent__id = Field()
    condition = Field()
    installation_date = Field()
    furniture_signpost_plan__id = Field()
    mount_real__id = Field()

    class Meta(AbstractFurnitureSignpostResource.Meta):
        model = FurnitureSignpostPlan

        fields = AbstractFurnitureSignpostResource.Meta.common_fields
        export_order = fields

    def dehydrate_id(self, obj: FurnitureSignpostPlan):
        return None

    def dehydrate_furniture_signpost_plan__id(self, obj: FurnitureSignpostPlan):
        return obj.id

    def export_field(self, field, obj):
        field_name = self.get_field_name(field)
        method = getattr(self, "dehydrate_%s" % field_name, None)
        if method is not None:
            return method(obj)
        return field.export(obj)

    def __str__(self):
        return "Template for Real Import"

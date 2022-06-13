from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget

from traffic_control.enums import Condition, Lifecycle
from traffic_control.models import (
    MountPlan,
    MountReal,
    MountType,
    Owner,
    Plan,
    ResponsibleEntity,
    SignpostPlan,
    SignpostReal,
    TrafficControlDeviceType,
)
from traffic_control.models.signpost import LocationSpecifier
from traffic_control.resources.common import (
    GenericDeviceBaseResource,
    ResourceEnumIntegerField,
    ResponsibleEntityPermissionImportMixin,
)


class AbstractSignpostResource(ResponsibleEntityPermissionImportMixin, GenericDeviceBaseResource):
    lifecycle = ResourceEnumIntegerField(attribute="lifecycle", enum=Lifecycle, default=Lifecycle.ACTIVE)
    owner__name_fi = Field(attribute="owner", column_name="owner__name_fi", widget=ForeignKeyWidget(Owner, "name_fi"))
    responsible_entity__name = Field(
        attribute="responsible_entity",
        column_name="responsible_entity__name",
        widget=ForeignKeyWidget(ResponsibleEntity, "name"),
    )
    device_type__code = Field(
        attribute="device_type",
        column_name="device_type__code",
        widget=ForeignKeyWidget(TrafficControlDeviceType, "code"),
    )
    mount_type__code = Field(
        attribute="mount_type", column_name="mount_type__code", widget=ForeignKeyWidget(MountType, "code")
    )
    location_specifier = ResourceEnumIntegerField(
        attribute="location_specifier",
        enum=LocationSpecifier,
        default=LocationSpecifier.RIGHT,
    )

    class Meta(GenericDeviceBaseResource.Meta):
        common_fields = (
            "id",
            "owner__name_fi",
            "responsible_entity__name",
            "lifecycle",
            "location",
            "road_name",
            "lane_number",
            "lane_type",
            "location_specifier",
            "direction",
            "height",
            "mount_type__code",
            "device_type__code",
            "value",
            "txt",
            "size",
            "reflection_class",
            "attachment_class",
            "target_id",
            "target_txt",
            "validity_period_start",
            "validity_period_end",
            "seasonal_validity_period_start",
            "seasonal_validity_period_end",
            "parent__id",
        )


class SignpostPlanResource(AbstractSignpostResource):
    parent__id = Field(attribute="parent", column_name="parent__id", widget=ForeignKeyWidget(SignpostPlan, "id"))
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

    class Meta(AbstractSignpostResource.Meta):
        model = SignpostPlan

        fields = AbstractSignpostResource.Meta.common_fields + (
            "mount_plan__id",
            "plan__plan_number",
        )
        export_order = fields


class SignpostRealResource(AbstractSignpostResource):
    parent__id = Field(attribute="parent", column_name="parent__id", widget=ForeignKeyWidget(SignpostReal, "id"))
    condition = ResourceEnumIntegerField(attribute="condition", enum=Condition, default=Condition.VERY_GOOD)
    signpost_plan__id = Field(
        attribute="signpost_plan",
        column_name="signpost_plan__id",
        widget=ForeignKeyWidget(SignpostPlan, "id"),
    )
    mount_real__id = Field(
        attribute="mount_real",
        column_name="mount_real__id",
        widget=ForeignKeyWidget(MountReal, "id"),
    )

    class Meta(AbstractSignpostResource.Meta):
        model = SignpostReal

        fields = AbstractSignpostResource.Meta.common_fields + (
            "signpost_plan__id",
            "mount_real__id",
            "material",
            "organization",
            "manufacturer",
        )
        export_order = fields

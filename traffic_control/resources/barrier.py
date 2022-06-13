from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget

from traffic_control.enums import Lifecycle
from traffic_control.models import BarrierPlan, BarrierReal, Owner, Plan, ResponsibleEntity, TrafficControlDeviceType
from traffic_control.models.barrier import ConnectionType, LocationSpecifier
from traffic_control.resources.common import (
    GenericDeviceBaseResource,
    ResourceEnumIntegerField,
    ResponsibleEntityPermissionImportMixin,
)


class AbstractBarrierResource(ResponsibleEntityPermissionImportMixin, GenericDeviceBaseResource):
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
    location_specifier = ResourceEnumIntegerField(
        attribute="location_specifier",
        enum=LocationSpecifier,
        default=LocationSpecifier.RIGHT,
    )
    connection_type = ResourceEnumIntegerField(
        attribute="connection_type", enum=ConnectionType, default=ConnectionType.CLOSED
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
            "device_type__code",
            "connection_type",
            "material",
            "is_electric",
            "reflective",
            "validity_period_start",
            "validity_period_end",
            "length",
            "count",
            "txt",
        )


class BarrierPlanResource(AbstractBarrierResource):
    plan__plan_number = Field(
        attribute="plan",
        column_name="plan__plan_number",
        widget=ForeignKeyWidget(Plan, "plan_number"),
    )

    class Meta(AbstractBarrierResource.Meta):
        model = BarrierPlan

        fields = AbstractBarrierResource.Meta.common_fields + ("plan__plan_number",)
        export_order = fields


class BarrierRealResource(AbstractBarrierResource):
    barrier_plan__id = Field(
        attribute="barrier_plan",
        column_name="barrier_plan__id",
        widget=ForeignKeyWidget(BarrierPlan, "id"),
    )

    class Meta(AbstractBarrierResource.Meta):
        model = BarrierReal

        fields = AbstractBarrierResource.Meta.common_fields + ("barrier_plan__id",)
        export_order = fields

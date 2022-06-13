from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget

from traffic_control.enums import Lifecycle
from traffic_control.models import (
    AdditionalSignPlan,
    AdditionalSignReal,
    CoverageArea,
    MountPlan,
    MountReal,
    MountType,
    Owner,
    Plan,
    ResponsibleEntity,
)
from traffic_control.models.additional_sign import Color
from traffic_control.models.traffic_sign import LocationSpecifier, TrafficSignPlan, TrafficSignReal
from traffic_control.resources.common import (
    GenericDeviceBaseResource,
    ResourceEnumIntegerField,
    ResponsibleEntityPermissionImportMixin,
)


class AbstractAdditionalSignResource(ResponsibleEntityPermissionImportMixin, GenericDeviceBaseResource):
    lifecycle = ResourceEnumIntegerField(attribute="lifecycle", enum=Lifecycle, default=Lifecycle.ACTIVE)
    owner__name_fi = Field(attribute="owner", column_name="owner__name_fi", widget=ForeignKeyWidget(Owner, "name_fi"))
    responsible_entity__name = Field(
        attribute="responsible_entity",
        column_name="responsible_entity__name",
        widget=ForeignKeyWidget(ResponsibleEntity, "name"),
    )
    mount_type__code = Field(
        attribute="mount_type", column_name="mount_type__code", widget=ForeignKeyWidget(MountType, "code")
    )
    color = ResourceEnumIntegerField(attribute="color", enum=Color, default=Color.BLUE)
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
            "height",
            "direction",
            "reflection_class",
            "surface_class",
            "color",
            "mount_type__code",
            "road_name",
            "lane_number",
            "lane_type",
            "location_specifier",
            "validity_period_start",
            "validity_period_end",
            "seasonal_validity_period_start",
            "seasonal_validity_period_end",
            "parent__id",
        )


class AdditionalSignPlanResource(AbstractAdditionalSignResource):
    parent__id = Field(attribute="parent", column_name="parent__id", widget=ForeignKeyWidget(TrafficSignPlan, "id"))
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

    class Meta(AbstractAdditionalSignResource.Meta):
        model = AdditionalSignPlan

        fields = AbstractAdditionalSignResource.Meta.common_fields + (
            "mount_plan__id",
            "plan__plan_number",
        )
        export_order = fields


class AdditionalSignRealResource(AbstractAdditionalSignResource):
    parent__id = Field(attribute="parent", column_name="parent__id", widget=ForeignKeyWidget(TrafficSignReal, "id"))
    additional_sign_plan__id = Field(
        attribute="additional_sign_plan",
        column_name="additional_sign_plan__id",
        widget=ForeignKeyWidget(AdditionalSignPlan, "id"),
    )
    mount_real__id = Field(
        attribute="mount_real",
        column_name="mount_real__id",
        widget=ForeignKeyWidget(MountReal, "id"),
    )
    coverage_area__id = Field(
        attribute="coverage_area",
        column_name="coverage_area__id",
        widget=ForeignKeyWidget(CoverageArea, "id"),
    )

    class Meta(AbstractAdditionalSignResource.Meta):
        model = AdditionalSignReal

        fields = AbstractAdditionalSignResource.Meta.common_fields + (
            "installation_date",
            "additional_sign_plan__id",
            "mount_real__id",
            "installation_id",
            "installation_details",
            "installed_by",
            "manufacturer",
            "rfid",
            "legacy_code",
            "permit_decision_id",
            "operation",
            "attachment_url",
            "coverage_area__id",
        )
        export_order = fields

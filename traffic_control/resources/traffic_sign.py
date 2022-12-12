from django.utils.translation import gettext as _
from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget

from traffic_control.models import (
    CoverageArea,
    MountPlan,
    MountReal,
    MountType,
    Owner,
    Plan,
    ResponsibleEntity,
    TrafficControlDeviceType,
    TrafficSignPlan,
    TrafficSignReal,
)
from traffic_control.resources.common import GenericDeviceBaseResource, ResponsibleEntityPermissionImportMixin


class AbstractTrafficSignResource(ResponsibleEntityPermissionImportMixin, GenericDeviceBaseResource):
    owner__name_fi = Field(
        attribute="owner",
        column_name="owner__name_fi",
        widget=ForeignKeyWidget(Owner, "name_fi"),
    )
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
        attribute="mount_type",
        column_name="mount_type__code",
        widget=ForeignKeyWidget(MountType, "code"),
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
            "device_type__code",
            "direction",
            "height",
            "mount_type__code",
            "value",
            "size",
            "reflection_class",
            "surface_class",
            "txt",
            "location_specifier",
            "validity_period_start",
            "validity_period_end",
            "seasonal_validity_period_start",
            "seasonal_validity_period_end",
        )


class TrafficSignPlanResource(AbstractTrafficSignResource):
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

    class Meta(AbstractTrafficSignResource.Meta):
        model = TrafficSignPlan

        fields = AbstractTrafficSignResource.Meta.common_fields + (
            "mount_plan__id",
            "plan__plan_number",
        )
        export_order = fields


class TrafficSignRealResource(AbstractTrafficSignResource):
    traffic_sign_plan__id = Field(
        attribute="traffic_sign_plan",
        column_name="traffic_sign_plan__id",
        widget=ForeignKeyWidget(TrafficSignPlan, "id"),
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

    class Meta(AbstractTrafficSignResource.Meta):
        model = TrafficSignReal

        fields = AbstractTrafficSignResource.Meta.common_fields + (
            "condition",
            "legacy_code",
            "traffic_sign_plan__id",
            "mount_real__id",
            "installation_id",
            "installation_details",
            "permit_decision_id",
            "coverage_area__id",
            "manufacturer",
            "rfid",
            "operation",
            "attachment_url",
        )
        export_order = fields


class TrafficSignPlanToRealTemplateResource(TrafficSignRealResource):
    class Meta(AbstractTrafficSignResource.Meta):
        model = TrafficSignPlan
        verbose_name = _("Template for Real Import")

    def dehydrate_id(self, obj: TrafficSignPlan):
        related_reals = list(TrafficSignReal.objects.filter(traffic_sign_plan=obj.id))
        if related_reals:
            return related_reals[0].id
        else:
            return None

    def dehydrate_traffic_sign_plan__id(self, obj: TrafficSignPlan):
        return obj.id

    def dehydrate_mount_real__id(self, obj: TrafficSignPlan):
        if not obj.mount_plan:
            return None

        mount_reals = list(MountReal.objects.filter(mount_plan=obj.mount_plan))
        if not mount_reals:
            return None

        return mount_reals[0].id

    def __str__(self):
        return self.Meta.verbose_name

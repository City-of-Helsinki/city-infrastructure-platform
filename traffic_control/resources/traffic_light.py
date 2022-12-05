from django.utils.translation import gettext as _
from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget

from traffic_control.enums import LaneNumber, LaneType, Lifecycle
from traffic_control.models import (
    MountPlan,
    MountReal,
    MountType,
    Owner,
    Plan,
    ResponsibleEntity,
    TrafficControlDeviceType,
    TrafficLightPlan,
    TrafficLightReal,
    TrafficLightType,
)
from traffic_control.models.traffic_light import (
    LocationSpecifier,
    PushButton,
    TrafficLightSoundBeaconValue,
    VehicleRecognition,
)
from traffic_control.resources.common import (
    GenericDeviceBaseResource,
    ResourceEnumIntegerField,
    ResponsibleEntityPermissionImportMixin,
)


class AbstractTrafficLightResource(ResponsibleEntityPermissionImportMixin, GenericDeviceBaseResource):
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
    lane_number = ResourceEnumIntegerField(attribute="lane_number", enum=LaneNumber, default=LaneNumber.MAIN_1)
    lane_type = ResourceEnumIntegerField(attribute="lane_type", enum=LaneType, default=LaneType.MAIN)
    type = ResourceEnumIntegerField(attribute="type", enum=TrafficLightType, default=TrafficLightType.SIGNAL)
    push_button = ResourceEnumIntegerField(attribute="push_button", enum=PushButton, default=PushButton.NO)
    sound_beacon = ResourceEnumIntegerField(
        attribute="sound_beacon",
        enum=TrafficLightSoundBeaconValue,
        default=TrafficLightSoundBeaconValue.NO,
    )
    vehicle_recognition = ResourceEnumIntegerField(
        attribute="vehicle_recognition", enum=VehicleRecognition, default=None
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
            "type",
            "device_type__code",
            "txt",
            "push_button",
            "sound_beacon",
            "vehicle_recognition",
            "validity_period_start",
            "validity_period_end",
            "location_specifier",
            "mount_type__code",
            "height",
            "direction",
        )


class TrafficLightPlanResource(AbstractTrafficLightResource):
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

    class Meta(AbstractTrafficLightResource.Meta):
        model = TrafficLightPlan

        fields = AbstractTrafficLightResource.Meta.common_fields + (
            "mount_plan__id",
            "plan__plan_number",
        )
        export_order = fields


class TrafficLightRealResource(AbstractTrafficLightResource):
    traffic_light_plan__id = Field(
        attribute="traffic_light_plan",
        column_name="traffic_light_plan__id",
        widget=ForeignKeyWidget(TrafficLightPlan, "id"),
    )
    mount_real__id = Field(
        attribute="mount_real",
        column_name="mount_real__id",
        widget=ForeignKeyWidget(MountReal, "id"),
    )

    class Meta(AbstractTrafficLightResource.Meta):
        model = TrafficLightReal

        fields = AbstractTrafficLightResource.Meta.common_fields + (
            "traffic_light_plan__id",
            "mount_real__id",
        )
        export_order = fields


class TrafficLightPlanToRealTemplateResource(TrafficLightRealResource):
    class Meta(AbstractTrafficLightResource.Meta):
        model = TrafficLightPlan
        verbose_name = _("Template for Real Import")

    def dehydrate_id(self, obj: TrafficLightPlan):
        related_reals = list(TrafficLightReal.objects.filter(traffic_light_plan=obj.id))
        if related_reals:
            return related_reals[0].id
        else:
            return None

    def dehydrate_traffic_light_plan__id(self, obj: TrafficLightPlan):
        return obj.id

    def dehydrate_mount_real__id(self, obj: TrafficLightPlan):
        if not obj.mount_plan:
            return None

        mount_reals = list(MountReal.objects.filter(mount_plan=obj.mount_plan))
        if not mount_reals:
            return None

        return mount_reals[0].id

    def __str__(self):
        return self.Meta.verbose_name

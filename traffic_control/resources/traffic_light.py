from django.utils.translation import gettext as _
from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget

from traffic_control.models import (
    MountPlan,
    MountReal,
    MountType,
    Owner,
    Plan,
    ResponsibleEntity,
    TrafficControlDeviceType,
    TrafficLightPlan,
    TrafficLightPlanReplacement,
    TrafficLightReal,
)
from traffic_control.resources.common import (
    GenericDeviceBaseResource,
    ReplacementField,
    ReplacementWidget,
    ResponsibleEntityPermissionImportMixin,
)
from traffic_control.services.traffic_light import traffic_light_plan_replace, traffic_light_plan_unreplace


class AbstractTrafficLightResource(ResponsibleEntityPermissionImportMixin, GenericDeviceBaseResource):
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
    plan__decision_id = Field(
        attribute="plan",
        column_name="plan__decision_id",
        widget=ForeignKeyWidget(Plan, "decision_id"),
    )
    replaces = ReplacementField(
        attribute="replacement_to_old",
        column_name="replaces",
        widget=ReplacementWidget(TrafficLightPlanReplacement, "old__id"),
        replace_method=traffic_light_plan_replace,
        unreplace_method=traffic_light_plan_unreplace,
    )
    replaced_by = ReplacementField(
        attribute="replacement_to_new",
        column_name="replaced_by",
        widget=ReplacementWidget(TrafficLightPlanReplacement, "new__id"),
        readonly=True,
    )

    class Meta(AbstractTrafficLightResource.Meta):
        model = TrafficLightPlan

        fields = AbstractTrafficLightResource.Meta.common_fields + (
            "mount_plan__id",
            "plan__decision_id",
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

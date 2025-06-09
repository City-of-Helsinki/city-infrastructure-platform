from django.utils.translation import gettext as _
from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget

from traffic_control.models import (
    Owner,
    Plan,
    ResponsibleEntity,
    RoadMarkingPlan,
    RoadMarkingPlanReplacement,
    RoadMarkingReal,
    TrafficControlDeviceType,
    TrafficSignPlan,
    TrafficSignReal,
)
from traffic_control.resources.common import (
    GenericDeviceBaseResource,
    ReplacementField,
    ReplacementWidget,
    ResponsibleEntityPermissionImportMixin,
    SOURCE_NAME_ID_FIELDS,
)
from traffic_control.services.road_marking import road_marking_plan_replace, road_marking_plan_unreplace


class AbstractRoadMarkingResource(ResponsibleEntityPermissionImportMixin, GenericDeviceBaseResource):
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
            "line_direction",
            "device_type__code",
            "arrow_direction",
            "value",
            "material",
            "color",
            "type_specifier",
            "validity_period_start",
            "validity_period_end",
            "seasonal_validity_period_information",
            "symbol",
            "size",
            "length",
            "width",
            "is_raised",
            "is_grinded",
            "additional_info",
            "amount",
        ) + SOURCE_NAME_ID_FIELDS


class RoadMarkingPlanResource(AbstractRoadMarkingResource):
    traffic_sign_plan__id = Field(
        attribute="traffic_sign_plan",
        column_name="traffic_sign_plan__id",
        widget=ForeignKeyWidget(TrafficSignPlan, "id"),
    )
    plan__decision_id = Field(
        attribute="plan",
        column_name="plan__decision_id",
        widget=ForeignKeyWidget(Plan, "decision_id"),
    )
    replaces = ReplacementField(
        attribute="replacement_to_old",
        column_name="replaces",
        widget=ReplacementWidget(RoadMarkingPlanReplacement, "old__id"),
        replace_method=road_marking_plan_replace,
        unreplace_method=road_marking_plan_unreplace,
    )
    replaced_by = ReplacementField(
        attribute="replacement_to_new",
        column_name="replaced_by",
        widget=ReplacementWidget(RoadMarkingPlanReplacement, "new__id"),
        readonly=True,
    )

    class Meta(AbstractRoadMarkingResource.Meta):
        model = RoadMarkingPlan

        fields = AbstractRoadMarkingResource.Meta.common_fields + (
            "traffic_sign_plan__id",
            "plan__decision_id",
        )
        export_order = fields


class RoadMarkingRealResource(AbstractRoadMarkingResource):
    road_marking_plan__id = Field(
        attribute="road_marking_plan",
        column_name="road_marking_plan__id",
        widget=ForeignKeyWidget(RoadMarkingPlan, "id"),
    )
    traffic_sign_real__id = Field(
        attribute="traffic_sign_real",
        column_name="traffic_sign_real__id",
        widget=ForeignKeyWidget(TrafficSignReal, "id"),
    )

    class Meta(AbstractRoadMarkingResource.Meta):
        model = RoadMarkingReal

        fields = AbstractRoadMarkingResource.Meta.common_fields + (
            "condition",
            "installation_date",
            "road_marking_plan__id",
            "traffic_sign_real__id",
            "missing_traffic_sign_real_txt",
        )
        export_order = fields


class RoadMarkingPlanToRealTemplateResource(RoadMarkingRealResource):
    class Meta(AbstractRoadMarkingResource.Meta):
        model = RoadMarkingPlan
        verbose_name = _("Template for Real Import")

    def dehydrate_id(self, obj: RoadMarkingPlan):
        related_reals = list(RoadMarkingReal.objects.filter(road_marking_plan=obj.id))
        if related_reals:
            return related_reals[0].id
        else:
            return None

    def dehydrate_road_marking_plan__id(self, obj: RoadMarkingPlan):
        return obj.id

    def dehydrate_traffic_sign_real__id(self, obj: RoadMarkingPlan):
        if not obj.traffic_sign_plan:
            return None

        traffic_sign_plans = list(TrafficSignReal.objects.filter(traffic_sign_plan=obj.traffic_sign_plan))
        if not traffic_sign_plans:
            return None

        return traffic_sign_plans[0].id

    def __str__(self):
        return self.Meta.verbose_name

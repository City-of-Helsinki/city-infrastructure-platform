from django.utils.translation import gettext as _
from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget

from traffic_control.models import (
    BarrierPlan,
    BarrierPlanReplacement,
    BarrierReal,
    Owner,
    Plan,
    TrafficControlDeviceType,
)
from traffic_control.resources.common import (
    GenericDeviceBaseResource,
    ReplacementField,
    ReplacementWidget,
    SOURCE_NAME_ID_FIELDS,
)
from traffic_control.services.barrier import barrier_plan_replace, barrier_plan_unreplace


class AbstractBarrierResource(GenericDeviceBaseResource):
    owner__name_fi = Field(
        attribute="owner",
        column_name="owner__name_fi",
        widget=ForeignKeyWidget(Owner, "name_fi"),
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
        ) + SOURCE_NAME_ID_FIELDS


class BarrierPlanResource(AbstractBarrierResource):
    plan__decision_id = Field(
        attribute="plan",
        column_name="plan__decision_id",
        widget=ForeignKeyWidget(Plan, "decision_id"),
    )
    replaces = ReplacementField(
        attribute="replacement_to_old",
        column_name="replaces",
        widget=ReplacementWidget(BarrierPlanReplacement, "old__id"),
        replace_method=barrier_plan_replace,
        unreplace_method=barrier_plan_unreplace,
    )
    replaced_by = ReplacementField(
        attribute="replacement_to_new",
        column_name="replaced_by",
        widget=ReplacementWidget(BarrierPlanReplacement, "new__id"),
        readonly=True,
    )

    class Meta(AbstractBarrierResource.Meta):
        model = BarrierPlan

        fields = AbstractBarrierResource.Meta.common_fields + ("plan__decision_id",)
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


class BarrierPlanToRealTemplateResource(BarrierRealResource):
    class Meta(AbstractBarrierResource.Meta):
        model = BarrierPlan
        verbose_name = _("Template for Real Import")

    def dehydrate_id(self, obj: BarrierPlan):
        related_reals = list(BarrierReal.objects.filter(barrier_plan=obj.id))
        if related_reals:
            return related_reals[0].id
        else:
            return None

    def dehydrate_barrier_plan__id(self, obj: BarrierPlan):
        return obj.id

    def __str__(self):
        return self.Meta.verbose_name

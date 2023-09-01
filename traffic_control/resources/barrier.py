from django.utils.translation import gettext as _
from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget

from traffic_control.models import BarrierPlan, BarrierReal, Owner, Plan, ResponsibleEntity, TrafficControlDeviceType
from traffic_control.resources.common import GenericDeviceBaseResource, ResponsibleEntityPermissionImportMixin


class AbstractBarrierResource(ResponsibleEntityPermissionImportMixin, GenericDeviceBaseResource):
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
    plan__decision_id = Field(
        attribute="plan",
        column_name="plan__decision_id",
        widget=ForeignKeyWidget(Plan, "decision_id"),
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

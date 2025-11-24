from django.utils.translation import gettext as _
from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget

from traffic_control.models import (
    MountPlan,
    MountReal,
    MountType,
    Owner,
    Plan,
    SignpostPlan,
    SignpostPlanReplacement,
    SignpostReal,
    TrafficControlDeviceType,
)
from traffic_control.resources.common import (
    GenericDeviceBaseResource,
    ParentChildReplacementImportMixin,
    ParentChildReplacementPlanToRealExportMixin,
    ReplacementField,
    ReplacementWidget,
    SOURCE_NAME_ID_FIELDS,
)
from traffic_control.services.signpost import signpost_plan_replace, signpost_plan_unreplace


class AbstractSignpostResource(
    ParentChildReplacementImportMixin,
    GenericDeviceBaseResource,
):
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
    mount_type__code = Field(
        attribute="mount_type",
        column_name="mount_type__code",
        widget=ForeignKeyWidget(MountType, "code"),
    )

    class Meta(
        ParentChildReplacementImportMixin.Meta,
        GenericDeviceBaseResource.Meta,
    ):
        common_fields = (
            "id",
            "owner__name_fi",
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
            "seasonal_validity_period_information",
            "parent__id",
        ) + SOURCE_NAME_ID_FIELDS


class SignpostPlanResource(AbstractSignpostResource):
    parent__id = Field(
        attribute="parent",
        column_name="parent__id",
        widget=ForeignKeyWidget(SignpostPlan, "id"),
    )
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
        widget=ReplacementWidget(SignpostPlanReplacement, "old__id"),
        replace_method=signpost_plan_replace,
        unreplace_method=signpost_plan_unreplace,
    )
    replaced_by = ReplacementField(
        attribute="replacement_to_new",
        column_name="replaced_by",
        widget=ReplacementWidget(SignpostPlanReplacement, "new__id"),
        readonly=True,
    )

    class Meta(AbstractSignpostResource.Meta):
        model = SignpostPlan

        fields = AbstractSignpostResource.Meta.common_fields + (
            "mount_plan__id",
            "plan__decision_id",
        )
        export_order = fields


class SignpostRealResource(AbstractSignpostResource):
    parent__id = Field(
        attribute="parent",
        column_name="parent__id",
        widget=ForeignKeyWidget(SignpostReal, "id"),
    )
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
            "condition",
        )
        export_order = fields


class SignpostPlanToRealTemplateResource(
    ParentChildReplacementPlanToRealExportMixin,
    SignpostRealResource,
):
    def dehydrate_id(self, obj: SignpostPlan):
        related_reals = list(SignpostReal.objects.filter(signpost_plan=obj.id))
        if related_reals:
            return related_reals[0].id
        else:
            return None

    def dehydrate_signpost_plan__id(self, obj: SignpostPlan):
        return obj.id

    def dehydrate_mount_real__id(self, obj: SignpostPlan):
        if not obj.mount_plan:
            return None

        mount_reals = list(MountReal.objects.filter(mount_plan=obj.mount_plan))
        if not mount_reals:
            return None

        return mount_reals[0].id

    def dehydrate_parent__id(self, obj: SignpostPlan):
        if not obj.parent:
            return None

        parents = list(SignpostReal.objects.filter(signpost_plan=obj.parent))
        if not parents:
            return None

        return parents[0].id

    def __str__(self):
        return self.Meta.verbose_name

    class Meta(
        ParentChildReplacementPlanToRealExportMixin.Meta,
        SignpostRealResource.Meta,
    ):
        model = SignpostPlan
        plan_id_header = "signpost_plan__id"
        real_model = SignpostReal
        real_model_plan_id_field = "signpost_plan_id"
        verbose_name = _("Template for Real Import")

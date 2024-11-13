from django.utils.translation import gettext as _
from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget

from traffic_control.models import (
    MountPlan,
    MountPlanReplacement,
    MountReal,
    MountType,
    Owner,
    Plan,
    PortalType,
    ResponsibleEntity,
)
from traffic_control.resources.common import (
    GenericDeviceBaseResource,
    ReplacementField,
    ReplacementWidget,
    ResponsibleEntityPermissionImportMixin,
    SOURCE_NAME_ID_FIELDS,
)
from traffic_control.services.mount import mount_plan_replace, mount_plan_unreplace


class AbstractMountResource(ResponsibleEntityPermissionImportMixin, GenericDeviceBaseResource):
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
    mount_type__code = Field(
        attribute="mount_type",
        column_name="mount_type__code",
        widget=ForeignKeyWidget(MountType, "code"),
    )
    portal_type__id = Field(
        attribute="portal_type",
        column_name="portal_type__id",
        widget=ForeignKeyWidget(PortalType, "id"),
    )
    base = Field(attribute="base", column_name="base", default="")

    class Meta(GenericDeviceBaseResource.Meta):
        common_fields = (
            "id",
            "owner__name_fi",
            "responsible_entity__name",
            "lifecycle",
            "location",
            "height",
            "mount_type__code",
            "base",
            "portal_type__id",
            "material",
            "validity_period_start",
            "validity_period_end",
            "txt",
            "electric_accountable",
            "is_foldable",
            "cross_bar_length",
        ) + SOURCE_NAME_ID_FIELDS


class MountPlanResource(AbstractMountResource):
    plan__decision_id = Field(
        attribute="plan",
        column_name="plan__decision_id",
        widget=ForeignKeyWidget(Plan, "decision_id"),
    )
    replaces = ReplacementField(
        attribute="replacement_to_old",
        column_name="replaces",
        widget=ReplacementWidget(MountPlanReplacement, "old__id"),
        replace_method=mount_plan_replace,
        unreplace_method=mount_plan_unreplace,
    )
    replaced_by = ReplacementField(
        attribute="replacement_to_new",
        column_name="replaced_by",
        widget=ReplacementWidget(MountPlanReplacement, "new__id"),
        readonly=True,
    )

    class Meta(AbstractMountResource.Meta):
        model = MountPlan

        fields = AbstractMountResource.Meta.common_fields + ("plan__decision_id",)
        export_order = fields


class MountRealResource(AbstractMountResource):
    mount_plan__id = Field(
        attribute="mount_plan",
        column_name="mount_plan__id",
        widget=ForeignKeyWidget(MountPlan, "id"),
    )

    class Meta(AbstractMountResource.Meta):
        model = MountReal

        fields = AbstractMountResource.Meta.common_fields + (
            "inspected_at",
            "diameter",
            "mount_plan__id",
        )
        export_order = fields


class MountPlanToRealTemplateResource(MountRealResource):
    class Meta(AbstractMountResource.Meta):
        model = MountPlan
        verbose_name = _("Template for Real Import")

    def dehydrate_id(self, obj: MountPlan):
        related_reals = list(MountReal.objects.filter(mount_plan=obj.id))
        if related_reals:
            return related_reals[0].id
        else:
            return None

    def dehydrate_mount_plan__id(self, obj: MountPlan):
        return obj.id

    def __str__(self):
        return self.Meta.verbose_name

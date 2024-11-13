from django.utils.translation import gettext as _
from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget

from city_furniture.models import FurnitureSignpostPlan, FurnitureSignpostReal
from city_furniture.models.common import CityFurnitureColor, CityFurnitureDeviceType, CityFurnitureTarget
from traffic_control.models import MountPlan, MountReal, MountType, Owner, Plan, ResponsibleEntity
from traffic_control.resources.common import (
    GenericDeviceBaseResource,
    ParentChildReplacementImportMixin,
    ParentChildReplacementPlanToRealExportMixin,
    ResponsibleEntityPermissionImportMixin,
    SOURCE_NAME_ID_FIELDS,
)


class AbstractFurnitureSignpostResource(
    ResponsibleEntityPermissionImportMixin,
    ParentChildReplacementImportMixin,
    GenericDeviceBaseResource,
):
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
        widget=ForeignKeyWidget(CityFurnitureDeviceType, "code"),
    )
    mount_type__code = Field(
        attribute="mount_type",
        column_name="mount_type__code",
        widget=ForeignKeyWidget(MountType, "code"),
    )
    target__name_fi = Field(
        attribute="target",
        column_name="target__name_fi",
        widget=ForeignKeyWidget(CityFurnitureTarget, "name_fi"),
    )
    color__name = Field(
        attribute="color",
        column_name="color__name",
        widget=ForeignKeyWidget(CityFurnitureColor, "name"),
    )

    class Meta(
        ParentChildReplacementImportMixin.Meta,
        GenericDeviceBaseResource.Meta,
    ):
        common_fields = (
            "id",
            "owner__name_fi",
            "responsible_entity__name",
            "location",
            "location_name_fi",
            "location_name_sw",
            "location_name_en",
            "location_additional_info",
            "direction",
            "device_type__code",
            "color__name",
            "height",
            "mount_type__code",
            "parent__id",
            "order",
            "pictogram",
            "value",
            "size",
            "arrow_direction",
            "target__name_fi",
            "content_responsible_entity",
            "text_content_fi",
            "text_content_sw",
            "text_content_en",
            "validity_period_start",
            "validity_period_end",
            "additional_material_url",
            "lifecycle",
        ) + SOURCE_NAME_ID_FIELDS


class FurnitureSignpostPlanResource(AbstractFurnitureSignpostResource):
    parent__id = Field(
        attribute="parent",
        column_name="parent__id",
        widget=ForeignKeyWidget(FurnitureSignpostPlan, "id"),
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

    class Meta(AbstractFurnitureSignpostResource.Meta):
        model = FurnitureSignpostPlan

        fields = AbstractFurnitureSignpostResource.Meta.common_fields + (
            "mount_plan__id",
            "plan__decision_id",
        )
        export_order = fields


class FurnitureSignpostRealResource(AbstractFurnitureSignpostResource):
    parent__id = Field(
        attribute="parent",
        column_name="parent__id",
        widget=ForeignKeyWidget(FurnitureSignpostReal, "id"),
    )
    furniture_signpost_plan__id = Field(
        attribute="furniture_signpost_plan",
        column_name="furniture_signpost_plan__id",
        widget=ForeignKeyWidget(FurnitureSignpostPlan, "id"),
    )
    mount_real__id = Field(
        attribute="mount_real",
        column_name="mount_real__id",
        widget=ForeignKeyWidget(MountReal, "id"),
    )

    class Meta(AbstractFurnitureSignpostResource.Meta):
        model = FurnitureSignpostReal

        fields = AbstractFurnitureSignpostResource.Meta.common_fields + (
            "condition",
            "installation_date",
            "furniture_signpost_plan__id",
            "mount_real__id",
        )
        export_order = fields


class FurnitureSignpostPlanTemplateResource(
    ParentChildReplacementPlanToRealExportMixin,
    FurnitureSignpostRealResource,
):
    """Resource for exporting a Plan and making the output importable as a real"""

    def dehydrate_id(self, obj: FurnitureSignpostPlan):
        related_reals = list(FurnitureSignpostReal.objects.filter(furniture_signpost_plan=obj.id))
        if related_reals:
            return related_reals[0].id
        else:
            return None

    def dehydrate_furniture_signpost_plan__id(self, obj: FurnitureSignpostPlan):
        return obj.id

    def dehydrate_mount_real__id(self, obj: FurnitureSignpostPlan):
        if not obj.mount_plan:
            return None

        mount_reals = list(MountReal.objects.filter(mount_plan=obj.mount_plan))
        if not mount_reals:
            return None

        return mount_reals[0].id

    def dehydrate_parent__id(self, obj: FurnitureSignpostPlan):
        if not obj.parent:
            return None

        parents = list(FurnitureSignpostReal.objects.filter(furniture_signpost_plan=obj.parent))
        if not parents:
            return None

        return parents[0].id

    def __str__(self):
        return self.Meta.verbose_name

    class Meta(
        ParentChildReplacementPlanToRealExportMixin.Meta,
        FurnitureSignpostRealResource.Meta,
    ):
        model = FurnitureSignpostPlan
        plan_id_header = "furniture_signpost_plan__id"
        real_model = FurnitureSignpostReal
        real_model_plan_id_field = "furniture_signpost_plan_id"
        verbose_name = _("Template for Real Import")

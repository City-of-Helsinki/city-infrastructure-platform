from import_export import resources
from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget

from city_furniture.models import FurnitureSignpostPlan, FurnitureSignpostReal
from city_furniture.models.common import CityFurnitureDeviceType, CityFurnitureTarget, ResponsibleEntity
from city_furniture.resources.common import ResourceEnumIntegerField
from traffic_control.enums import Condition, InstallationStatus, Lifecycle
from traffic_control.models import MountType, Owner
from users.utils import get_system_user


class AbstractFurnitureSignpostResource(resources.ModelResource):
    lifecycle = ResourceEnumIntegerField(attribute="lifecycle", column_name="lifecycle", enum=Lifecycle)
    condition = ResourceEnumIntegerField(attribute="condition", column_name="condition", enum=Condition)
    installation_status = ResourceEnumIntegerField(
        attribute="installation_status",
        column_name="installation_status",
        enum=InstallationStatus,
    )
    owner = Field(
        attribute="owner",
        column_name="owner__name_fi",
        widget=ForeignKeyWidget(Owner, "name_fi"),
    )
    responsible_entity = Field(
        attribute="responsible_entity",
        column_name="responsible_entity__name",
        widget=ForeignKeyWidget(ResponsibleEntity, "name"),
    )
    device_type = Field(
        attribute="device_type",
        column_name="device_type__code",
        widget=ForeignKeyWidget(CityFurnitureDeviceType, "code"),
    )
    mount_type = Field(
        attribute="mount_type",
        column_name="mount_type__code",
        widget=ForeignKeyWidget(MountType, "code"),
    )
    target = Field(
        attribute="target",
        column_name="target__name_fi",
        widget=ForeignKeyWidget(CityFurnitureTarget, "name_fi"),
    )

    class Meta:
        exclude = (
            "is_active",
            "deleted_at",
            "deleted_by",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        )
        common_fields = (
            "id",
            "source_name",
            "source_id",
            "project_id",
            "owner__name_fi",
            "responsible_entity__name",
            "location",  # TODO: Split into Lat and Long?
            "location_name",
            "location_additional_info",
            "direction",
            "device_type__code",
            "color__name",
            "height",
            "mount_type__code",
            "parent",
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
            "validity_period_end",
            "validity_period_start",
            "additional_material_url",
            "lifecycle",
        )

    def get_queryset(self):
        return self._meta.model.objects.active()

    def after_import_instance(self, instance, new, row_number=None, **kwargs):
        """Set created_by and updated_by users"""
        user = kwargs.pop("user", None)
        if user is None:
            user = get_system_user()

        instance.updated_by = user
        if new:
            instance.created_by = user

        super().after_import_instance(instance, new, row_number=None, **kwargs)


class FurnitureSignpostPlanResource(AbstractFurnitureSignpostResource):
    class Meta(AbstractFurnitureSignpostResource.Meta):
        model = FurnitureSignpostPlan

        fields = AbstractFurnitureSignpostResource.Meta.common_fields + (
            "mount_plan",
            "plan",
        )
        export_order = fields


class FurnitureSignpostRealResource(AbstractFurnitureSignpostResource):
    class Meta(AbstractFurnitureSignpostResource.Meta):
        model = FurnitureSignpostReal

        fields = AbstractFurnitureSignpostResource.Meta.common_fields + (
            "condition",
            "installation_status",
            "installation_date",
            "furniture_signpost_plan__id",
            "mount_real__id",
        )
        export_order = fields

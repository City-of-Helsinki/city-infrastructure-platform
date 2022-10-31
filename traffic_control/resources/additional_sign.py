import json
from uuid import UUID

from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget, Widget
from tablib import Dataset

from traffic_control.enums import Lifecycle
from traffic_control.models import (
    AdditionalSignPlan,
    AdditionalSignReal,
    CoverageArea,
    MountPlan,
    MountReal,
    MountType,
    Owner,
    Plan,
    ResponsibleEntity,
)
from traffic_control.models.additional_sign import Color
from traffic_control.models.common import TrafficControlDeviceType
from traffic_control.models.traffic_sign import LocationSpecifier, TrafficSignPlan, TrafficSignReal
from traffic_control.resources.common import (
    GenericDeviceBaseResource,
    ResourceEnumIntegerField,
    ResponsibleEntityPermissionImportMixin,
)


class StructuredContentWidget(Widget):
    def clean(self, value, row=None, *args, **kwargs):
        return value

    def render(self, value, obj=None):
        # Render value as raw value, not string
        return value


class AbstractAdditionalSignResource(ResponsibleEntityPermissionImportMixin, GenericDeviceBaseResource):
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
    color = ResourceEnumIntegerField(attribute="color", enum=Color, default=Color.BLUE)
    location_specifier = ResourceEnumIntegerField(
        attribute="location_specifier",
        enum=LocationSpecifier,
        default=LocationSpecifier.RIGHT,
    )

    # `content_s` column is destructured to several columns in after_export() and built back in before_import()
    content_s = Field(
        attribute="content_s",
        column_name="content_s",
        widget=StructuredContentWidget(),
    )

    class Meta(GenericDeviceBaseResource.Meta):
        common_fields = (
            "id",
            "owner__name_fi",
            "responsible_entity__name",
            "device_type__code",
            "order",
            "lifecycle",
            "location",
            "height",
            "direction",
            "reflection_class",
            "surface_class",
            "color",
            "mount_type__code",
            "road_name",
            "lane_number",
            "lane_type",
            "location_specifier",
            "validity_period_start",
            "validity_period_end",
            "seasonal_validity_period_start",
            "seasonal_validity_period_end",
            "parent__id",
        )

    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        self._content_s_from_columns(dataset)

    def after_export(self, queryset, data, *args, **kwargs):
        self._content_s_to_columns(data)

    def _content_s_from_columns(self, dataset: Dataset):
        """
        Reads `dataset` table's columns named `content_s.<property name>`
        and builds `content_s` structured content JSON object for each row.
        Modifies `dataset` in-place.
        """
        device_type_column_in_dataset = True if "device_type__code" in dataset.headers else False

        if device_type_column_in_dataset:
            # Get schemas for the devices used in import dataset
            device_type_codes = set(dataset["device_type__code"])
            device_types_schemas = dict(
                TrafficControlDeviceType.objects.filter(code__in=device_type_codes).values_list(
                    "code", "content_schema"
                )
            )
        else:
            # If device type code column is not present in the dataset, there will be  no changes
            # to device types, so we can use schemas from the database.
            device_type_ids = list(
                self.Meta.model.objects.filter(id__in=dataset["id"]).values_list("device_type", flat=True)
            )
            additional_sign_device_types = dict(
                self.Meta.model.objects.filter(id__in=dataset["id"]).values_list("id", "device_type__code")
            )
            device_types_schemas = dict(
                TrafficControlDeviceType.objects.filter(id__in=device_type_ids).values_list("code", "content_schema")
            )

        column_names: list[str] = dataset.headers
        content_columns = [name for name in column_names if name is not None and name.startswith("content_s.")]

        content_s_rows = []
        for row in dataset.dict:
            if device_type_column_in_dataset:
                device_type_code = row.get("device_type__code")
            else:
                device_type_code = additional_sign_device_types[UUID(row["id"])]

            schema = device_types_schemas.get(device_type_code)

            if schema is None:
                content_s_rows.append(None)
            else:
                schema_properties = schema.get("properties")
                required_properties = schema.get("required", [])

                content_s = {}
                for property_name in schema_properties:
                    property_type = schema_properties[property_name].get("type")
                    column_name = f"content_s.{property_name}"
                    is_required = property_name in required_properties

                    value_from_data = row.get(column_name)
                    value = self._clean_up_value(value_from_data, property_type, is_required)

                    if value is not None:
                        content_s[property_name] = value
                    else:
                        if is_required:
                            content_s[property_name] = value

                if content_s:
                    content_s_rows.append(content_s)
                else:
                    content_s_rows.append(None)

        dataset.append_col(content_s_rows, header="content_s")

        for content_column in content_columns:
            del dataset[content_column]

    @staticmethod
    def _clean_up_value(value, property_type: str, is_required: bool):
        if property_type == "boolean":
            return AbstractAdditionalSignResource._clean_value_boolean(value, is_required)
        elif property_type == "integer":
            return AbstractAdditionalSignResource._clean_value_integer(value, is_required)
        elif property_type == "number":
            return AbstractAdditionalSignResource._clean_value_number(value, is_required)
        elif property_type == "string":
            return AbstractAdditionalSignResource._clean_value_string(value, is_required)
        elif property_type == "array":
            return AbstractAdditionalSignResource._clean_value_array(value, is_required)
        elif property_type == "object":
            return AbstractAdditionalSignResource._clean_value_object(value, is_required)
        else:
            return value

    @staticmethod
    def _clean_value_boolean(value, is_required: bool):
        if value in ["1", 1, True, "true", "TRUE", "True"]:
            return True
        elif value in ["0", 0, False, "false", "FALSE", "False"]:
            return False
        elif not is_required and value in ["", None]:
            return None

        return value

    @staticmethod
    def _clean_value_integer(value, is_required: bool):
        if not is_required and value in [None, ""]:
            return None
        elif type(value) == str:
            try:
                return int(value)
            except ValueError:
                # Ignore conversion errors. Invalid values are handled in schema validation.
                pass
        return value

    @staticmethod
    def _clean_value_number(value, is_required: bool):
        if not is_required and value in [None, ""]:
            return None
        elif type(value) == str:
            try:
                return float(value)
            except ValueError:
                # Ignore conversion errors. Invalid values are handled in schema validation.
                pass
        return value

    @staticmethod
    def _clean_value_string(value, is_required: bool):
        if value in [None, ""]:
            if is_required:
                return ""
            else:
                return None
        return str(value)

    @staticmethod
    def _clean_value_array(value, is_required: bool):
        # JSON arrays are decoded just like objects
        return AbstractAdditionalSignResource._clean_value_object(value, is_required)

    @staticmethod
    def _clean_value_object(value, is_required: bool):
        if not is_required and value in [None, ""]:
            return None
        elif type(value) == str:
            try:
                return json.loads(value)
            except json.decoder.JSONDecodeError:
                # Ignore JSON parsing error. Invalid values are handled in schema validation.
                return value
        else:
            return value

    def _content_s_to_columns(self, data: Dataset):
        content_rows = data["content_s"]

        # Collect all content_s properties names from every row.
        # Use dict to retain properties order as they appear in data.
        content_properties = {}
        for row in content_rows:
            for key in row:
                content_properties[key] = None

        for property in content_properties:
            values = self._get_values_for_property(property, content_rows)

            # Convert arrays and objects to JSON strings
            values = self._structured_values_to_string(values)

            data.append_col(values, header=f"content_s.{property}")

        del data["content_s"]

    @staticmethod
    def _get_values_for_property(property, content_rows):
        values = []
        for row in content_rows:
            if type(row) == str:
                values.append(None)
            else:
                values.append(row.get(property))
        return values

    @staticmethod
    def _structured_values_to_string(values: list):
        out_values = []
        for value in values:
            if type(value) in [list, dict]:
                out_values.append(json.dumps(value))
            else:
                out_values.append(value)
        return out_values


class AdditionalSignPlanResource(AbstractAdditionalSignResource):
    parent__id = Field(attribute="parent", column_name="parent__id", widget=ForeignKeyWidget(TrafficSignPlan, "id"))
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

    class Meta(AbstractAdditionalSignResource.Meta):
        model = AdditionalSignPlan

        fields = AbstractAdditionalSignResource.Meta.common_fields + (
            "mount_plan__id",
            "plan__plan_number",
        )
        export_order = fields
        clean_model_instances = True


class AdditionalSignRealResource(AbstractAdditionalSignResource):
    parent__id = Field(attribute="parent", column_name="parent__id", widget=ForeignKeyWidget(TrafficSignReal, "id"))
    additional_sign_plan__id = Field(
        attribute="additional_sign_plan",
        column_name="additional_sign_plan__id",
        widget=ForeignKeyWidget(AdditionalSignPlan, "id"),
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

    class Meta(AbstractAdditionalSignResource.Meta):
        model = AdditionalSignReal

        fields = AbstractAdditionalSignResource.Meta.common_fields + (
            "installation_date",
            "additional_sign_plan__id",
            "mount_real__id",
            "installation_id",
            "installation_details",
            "installed_by",
            "manufacturer",
            "rfid",
            "legacy_code",
            "permit_decision_id",
            "operation",
            "attachment_url",
            "coverage_area__id",
        )
        export_order = fields
        clean_model_instances = True

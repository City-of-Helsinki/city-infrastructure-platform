import json
from typing import Optional, OrderedDict
from uuid import UUID

from django.utils.translation import gettext as _
from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget, Widget
from tablib import Dataset

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
    TrafficControlDeviceType,
    TrafficSignPlan,
    TrafficSignReal,
)
from traffic_control.resources.common import GenericDeviceBaseResource, ResponsibleEntityPermissionImportMixin


def _clean_up_value(value, property_type: str, is_required: bool):
    cleaning_functions = {
        "boolean": _clean_value_boolean,
        "integer": _clean_value_integer,
        "number": _clean_value_number,
        "string": _clean_value_string,
        "array": _clean_value_array,
        "object": _clean_value_object,
    }

    cleaning_function = cleaning_functions.get(property_type)
    if cleaning_function:
        return cleaning_function(value, is_required)
    else:
        return value


def _clean_value_boolean(value, is_required: bool):
    if _is_true(value):
        return True
    elif _is_false(value):
        return False
    elif not is_required and _is_none(value):
        return None
    return value


def _clean_value_integer(value, is_required: bool):
    if not is_required and _is_none(value):
        return None
    elif isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            # Ignore conversion errors. Invalid values are handled in schema validation.
            pass
    return value


def _clean_value_number(value, is_required: bool):
    if not is_required and _is_none(value):
        return None
    elif isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            # Ignore conversion errors. Invalid values are handled in schema validation.
            pass
    return value


def _clean_value_string(value, is_required: bool):
    if _is_none(value):
        if is_required:
            return ""
        else:
            return None
    return str(value)


def _clean_value_array(value, is_required: bool):
    # JSON arrays are decoded just like objects
    return _clean_value_object(value, is_required)


def _clean_value_object(value, is_required: bool):
    if not is_required and _is_none(value):
        return None
    elif isinstance(value, str):
        try:
            return json.loads(value)
        except json.decoder.JSONDecodeError:
            # Ignore JSON parsing error. Invalid values are handled in schema validation.
            return value
    else:
        return value


def _is_false(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in ["false", "0"]
    else:
        return value in [False, 0]


def _is_true(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in ["true", "1"]
    else:
        return value in [True, 1]


def _is_none(value) -> bool:
    return value is None or value == ""


class StructuredContentWidget(Widget):
    def clean(self, value, row=None, *args, **kwargs):
        return value

    def render(self, value, obj=None):
        # Render value as raw value, not string
        return value


class AbstractAdditionalSignResource(ResponsibleEntityPermissionImportMixin, GenericDeviceBaseResource):
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
            "size",
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
            "additional_information",
            "missing_content",
        )

    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        super().before_import(dataset, using_transactions, dry_run, **kwargs)
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
        id_column_in_dataset = True if "id" in dataset.headers else False

        if device_type_column_in_dataset:
            # Get schemas for the devices used in import dataset
            device_type_codes = set(dataset["device_type__code"])
            device_types_schemas = dict(
                TrafficControlDeviceType.objects.filter(code__in=device_type_codes).values_list(
                    "code", "content_schema"
                )
            )
        elif id_column_in_dataset:
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
        else:
            return

        column_names: list[str] = dataset.headers
        content_columns = [name for name in column_names if name is not None and name.startswith("content_s.")]

        content_s_rows = []
        for row in dataset.dict:
            if device_type_column_in_dataset:
                device_type_code = row.get("device_type__code")
            elif row.get("id"):
                device_type_code = additional_sign_device_types.get(UUID(row.get("id")))
            else:
                device_type_code = None

            schema = device_types_schemas.get(device_type_code)
            missing_content = row.get("missing_content", False)

            content_s = self._content_s_from_row(row, schema, missing_content)
            content_s_rows.append(content_s)

        dataset.append_col(content_s_rows, header="content_s")

        for content_column in content_columns:
            del dataset[content_column]

    def _content_s_from_row(self, row: OrderedDict, schema: Optional[dict], missing_content: bool) -> Optional[dict]:
        if schema is None:
            return None

        schema_properties = schema.get("properties")
        required_properties = schema.get("required", [])

        content_s = {}
        for property_name in schema_properties:
            property_type = schema_properties[property_name].get("type")
            column_name = f"content_s.{property_name}"
            is_required = property_name in required_properties and _is_false(missing_content)

            value_from_data = row.get(column_name)
            value = _clean_up_value(value_from_data, property_type, is_required)

            if value is not None or is_required:
                content_s[property_name] = value

        return content_s or None

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
            if isinstance(row, str):
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
    parent__id = Field(
        attribute="parent",
        column_name="parent__id",
        widget=ForeignKeyWidget(TrafficSignPlan, "id"),
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

    class Meta(AbstractAdditionalSignResource.Meta):
        model = AdditionalSignPlan

        fields = AbstractAdditionalSignResource.Meta.common_fields + (
            "mount_plan__id",
            "plan__decision_id",
        )
        export_order = fields
        clean_model_instances = True


class AdditionalSignRealResource(AbstractAdditionalSignResource):
    parent__id = Field(
        attribute="parent",
        column_name="parent__id",
        widget=ForeignKeyWidget(TrafficSignReal, "id"),
    )
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
            "condition",
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


class AdditionalSignPlanToRealTemplateResource(AdditionalSignRealResource):
    class Meta(AbstractAdditionalSignResource.Meta):
        model = AdditionalSignPlan
        verbose_name = _("Template for Real Import")

    def dehydrate_id(self, obj: AdditionalSignPlan):
        related_reals = list(AdditionalSignReal.objects.filter(additional_sign_plan=obj.id))
        if related_reals:
            return related_reals[0].id
        else:
            return None

    def dehydrate_additional_sign_plan__id(self, obj: AdditionalSignPlan):
        return obj.id

    def dehydrate_parent__id(self, obj: AdditionalSignPlan):
        if not obj.parent:
            return None

        parents = list(TrafficSignReal.objects.filter(traffic_sign_plan=obj.parent))
        if not parents:
            return None

        return parents[0].id

    def dehydrate_mount_real__id(self, obj: AdditionalSignPlan):
        if not obj.mount_plan:
            return None

        mount_reals = list(MountReal.objects.filter(mount_plan=obj.mount_plan))
        if not mount_reals:
            return None

        return mount_reals[0].id

    def __str__(self):
        return self.Meta.verbose_name

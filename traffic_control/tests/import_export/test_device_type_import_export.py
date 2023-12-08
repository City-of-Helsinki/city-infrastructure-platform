import json

import pytest

from traffic_control.enums import DeviceTypeTargetModel, TrafficControlDeviceTypeType
from traffic_control.models import TrafficControlDeviceType
from traffic_control.resources.device_type import TrafficControlDeviceTypeResource
from traffic_control.tests.factories import get_traffic_control_device_type
from traffic_control.tests.import_export.utils import file_formats, get_import_dataset


@pytest.mark.parametrize(
    ("icon", "value", "unit", "size"),
    (
        ("A11.svg", "value", "unit", "size"),
        ("", "", "", ""),
    ),
    ids=("with_str_fields", "no_str_fields"),
)
@pytest.mark.parametrize(
    ("legacy_code", "legacy_description"),
    (
        ("123", "Legacy description"),
        (None, None),
    ),
    ids=("with_legacy", "no_legacy"),
)
@pytest.mark.parametrize(
    "target_model",
    (DeviceTypeTargetModel.TRAFFIC_SIGN, None),
    ids=("with_target_model", "no_target_model"),
)
@pytest.mark.parametrize(
    "dt_type",
    (TrafficControlDeviceTypeType.LONGITUDINAL, None),
    ids=("with_type", "no_type"),
)
@pytest.mark.parametrize(
    "content_schema",
    ({"string": "value", "int": 1}, None),
    ids=("with_content_schema", "no_content_schema"),
)
@pytest.mark.django_db
def test__traffic_control_device_type__export(  # noqa: C901
    icon,
    value,
    unit,
    size,
    legacy_code,
    legacy_description,
    target_model,
    dt_type,
    content_schema,
):
    """Test simple export of a single traffic control device type with multiple variations"""

    kwargs = {}
    if icon:
        kwargs["icon"] = icon
    if value:
        kwargs["value"] = value
    if unit:
        kwargs["unit"] = unit
    if size:
        kwargs["size"] = size
    if legacy_code:
        kwargs["legacy_code"] = legacy_code
    if legacy_description:
        kwargs["legacy_description"] = legacy_description
    if target_model:
        kwargs["target_model"] = target_model
    if dt_type:
        kwargs["type"] = dt_type
    if content_schema:
        kwargs["content_schema"] = content_schema

    dt = get_traffic_control_device_type(**kwargs)

    dataset = TrafficControlDeviceTypeResource().export()

    assert len(dataset) == 1
    assert dataset.dict[0]["id"] == str(dt.id)
    assert dataset.dict[0]["code"] == dt.code
    assert dataset.dict[0]["icon"] == dt.icon
    assert dataset.dict[0]["description"] == dt.description
    assert dataset.dict[0]["value"] == dt.value
    assert dataset.dict[0]["unit"] == dt.unit
    assert dataset.dict[0]["size"] == dt.size

    # Nullable fields are "" when value is None
    if legacy_code:
        assert dataset.dict[0]["legacy_code"] == dt.legacy_code
    else:
        assert dataset.dict[0]["legacy_code"] == ""

    if legacy_description:
        assert dataset.dict[0]["legacy_description"] == dt.legacy_description
    else:
        assert dataset.dict[0]["legacy_description"] == ""

    if target_model:
        assert dataset.dict[0]["target_model"] == dt.target_model.name
    else:
        assert dataset.dict[0]["target_model"] == ""

    if dt_type:
        assert dataset.dict[0]["type"] == dt.type.name
    else:
        assert dataset.dict[0]["type"] == ""

    if content_schema:
        assert dataset.dict[0]["content_schema"] == json.dumps(dt.content_schema)
    else:
        assert dataset.dict[0]["content_schema"] == ""


@pytest.mark.parametrize(
    ("icon", "value", "unit", "size"),
    (
        ("A11.svg", "value", "unit", "size"),
        ("", "", "", ""),
    ),
    ids=("with_str_fields", "no_str_fields"),
)
@pytest.mark.parametrize(
    ("legacy_code", "legacy_description"),
    (
        ("123", "Legacy description"),
        ("", ""),
    ),
    ids=("with_legacy", "no_legacy"),
)
@pytest.mark.parametrize(
    "target_model",
    (DeviceTypeTargetModel.ADDITIONAL_SIGN, None),
    ids=("with_target_model", "no_target_model"),
)
@pytest.mark.parametrize(
    "dt_type",
    (TrafficControlDeviceTypeType.LONGITUDINAL, None),
    ids=("with_type", "no_type"),
)
@pytest.mark.parametrize(
    "content_schema",
    ({"string": "value", "int": 1}, None),
    ids=("with_content_schema", "no_content_schema"),
)
@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db
def test__traffic_control_device_type__import(
    icon,
    value,
    unit,
    size,
    legacy_code,
    legacy_description,
    target_model,
    dt_type,
    content_schema,
    format,
):
    """Test simple import of a single traffic control device type with multiple variations"""
    kwargs = {}
    if icon:
        kwargs["icon"] = icon
    if value:
        kwargs["value"] = value
    if unit:
        kwargs["unit"] = unit
    if size:
        kwargs["size"] = size
    if legacy_code:
        kwargs["legacy_code"] = legacy_code
    if legacy_description:
        kwargs["legacy_description"] = legacy_description
    if target_model:
        kwargs["target_model"] = target_model
    if dt_type:
        kwargs["type"] = dt_type
    if content_schema:
        kwargs["content_schema"] = content_schema

    get_traffic_control_device_type(**kwargs)

    dataset = get_import_dataset(TrafficControlDeviceTypeResource, format=format, delete_columns=["id"])
    TrafficControlDeviceType.objects.all().delete()
    assert TrafficControlDeviceType.objects.count() == 0
    result = TrafficControlDeviceTypeResource().import_data(dataset, raise_errors=False, collect_failed_rows=True)

    assert not result.has_validation_errors()
    assert not result.has_errors()
    assert result.totals["new"] == 1
    assert TrafficControlDeviceType.objects.count() == 1
    imported_dt = TrafficControlDeviceType.objects.first()

    assert imported_dt.icon == icon
    assert imported_dt.content_schema == content_schema
    assert imported_dt.value == value
    assert imported_dt.unit == unit
    assert imported_dt.size == size
    assert imported_dt.legacy_code == legacy_code
    assert imported_dt.legacy_description == legacy_description
    assert imported_dt.target_model == target_model
    assert imported_dt.type == dt_type


@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db
def test__traffic_control_device_type__import__invalid_content_schema(format):
    get_traffic_control_device_type()
    dataset = get_import_dataset(
        TrafficControlDeviceTypeResource,
        format=format,
        delete_columns=["id", "content_schema"],
    )
    dataset.append_col(['{"invalid", "json}'], header="content_schema")
    TrafficControlDeviceType.objects.all().delete()

    result = TrafficControlDeviceTypeResource().import_data(dataset, raise_errors=False, collect_failed_rows=True)
    assert not result.has_errors()
    assert result.has_validation_errors()
    assert result.invalid_rows[0].field_specific_errors.get("content_schema")
    assert TrafficControlDeviceType.objects.count() == 0


@pytest.mark.parametrize(
    "to_values",
    (
        {
            "code": "VALUES-2",
            "icon": "A2.svg",
            "description": "Description 2",
            "value": "value2",
            "unit": "unit2",
            "size": "size2",
            "legacy_code": "456",
            "legacy_description": "Legacy description 2",
            "target_model": DeviceTypeTargetModel.ADDITIONAL_SIGN,
            "type": TrafficControlDeviceTypeType.TRANSVERSE,
            "content_schema": {"string2": "value2", "int2": 2},
        },
        {
            "code": "EMPTY-2",
            "icon": "",
            "description": "",
            "value": "",
            "unit": "",
            "size": "",
            "legacy_code": "",
            "legacy_description": "",
            "target_model": None,
            "type": None,
            "content_schema": None,
        },
    ),
    ids=("to_values", "to_empty"),
)
@pytest.mark.parametrize(
    "from_values",
    (
        {
            "code": "VALUES-1",
            "icon": "A1.svg",
            "description": "Description 1",
            "value": "value1",
            "unit": "unit1",
            "size": "size1",
            "legacy_code": "123",
            "legacy_description": "Legacy description 1",
            "target_model": DeviceTypeTargetModel.ADDITIONAL_SIGN,
            "type": TrafficControlDeviceTypeType.LONGITUDINAL,
            "content_schema": {"string": "value", "int": 1},
        },
        {
            "code": "EMPTY",
            "icon": "",
            "description": "",
            "value": "",
            "unit": "",
            "size": "",
            "legacy_code": "",
            "legacy_description": "",
            "target_model": None,
            "type": None,
            "content_schema": None,
        },
    ),
    ids=("from_values", "from_empty"),
)
@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db
def test__traffic_control_device_type__import__update(
    to_values,
    from_values,
    format,
):
    device_type = get_traffic_control_device_type(**to_values)
    dataset = get_import_dataset(TrafficControlDeviceTypeResource, format=format)

    device_type.code = from_values["code"]
    device_type.icon = from_values["icon"]
    device_type.description = from_values["description"]
    device_type.value = from_values["value"]
    device_type.unit = from_values["unit"]
    device_type.size = from_values["size"]
    device_type.legacy_code = from_values["legacy_code"]
    device_type.legacy_description = from_values["legacy_description"]
    device_type.target_model = from_values["target_model"]
    device_type.type = from_values["type"]
    device_type.content_schema = from_values["content_schema"]
    device_type.save()

    result = TrafficControlDeviceTypeResource().import_data(dataset, raise_errors=False, collect_failed_rows=True)

    assert not result.has_validation_errors()
    assert not result.has_errors()
    assert result.totals["update"] == 1
    assert TrafficControlDeviceType.objects.count() == 1
    imported_dt = TrafficControlDeviceType.objects.first()

    assert imported_dt.code == to_values["code"]
    assert imported_dt.icon == to_values["icon"]
    assert imported_dt.description == to_values["description"]
    assert imported_dt.value == to_values["value"]
    assert imported_dt.unit == to_values["unit"]
    assert imported_dt.size == to_values["size"]
    assert imported_dt.legacy_code == to_values["legacy_code"]
    assert imported_dt.legacy_description == to_values["legacy_description"]
    assert imported_dt.target_model == to_values["target_model"]
    assert imported_dt.type == to_values["type"]
    assert imported_dt.content_schema == to_values["content_schema"]

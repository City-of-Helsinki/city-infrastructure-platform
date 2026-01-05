import json

import pytest

from traffic_control.enums import DeviceTypeTargetModel, TrafficControlDeviceTypeType
from traffic_control.models import TrafficControlDeviceType
from traffic_control.resources.device_type import TrafficControlDeviceTypeResource
from traffic_control.tests import DEVICE_TYPE_COUNT_OFFSET
from traffic_control.tests.factories import TrafficControlDeviceTypeFactory, TrafficControlDeviceTypeIconFactory
from traffic_control.tests.test_import_export.utils import file_formats, get_import_dataset


@pytest.mark.parametrize(
    ("icon_file", "value", "unit", "size"),
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
    icon_file,
    value,
    unit,
    size,
    legacy_code,
    legacy_description,
    target_model,
    dt_type,
    content_schema,
):
    """Test simple export of a single traffic control device type with multiple variations
    One device type is created to database in migrations, that is why assert len(dataset) == 1 + 1
    """
    kwargs = {"code": "123", "legacy_code": None, "legacy_description": None, "target_model": None}
    if icon_file:
        kwargs["icon_file"] = TrafficControlDeviceTypeIconFactory(file__filename=icon_file)
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
    dt = TrafficControlDeviceTypeFactory(**kwargs)

    dataset = TrafficControlDeviceTypeResource().export()
    added_data = None
    # find the added data row, DummyDT is created in migrations
    for d in dataset.dict:
        if d["code"] != "DummyDT":
            added_data = d
    assert len(dataset) == 1 + DEVICE_TYPE_COUNT_OFFSET
    assert added_data["code"] == dt.code
    assert added_data["icon_file"] == dt.icon_file.file
    assert added_data["description"] == dt.description
    assert added_data["value"] == dt.value
    assert added_data["unit"] == dt.unit
    assert added_data["size"] == dt.size
    assert added_data["id"] == str(dt.id)

    # Nullable fields are "" when value is None
    if legacy_code:
        assert added_data["legacy_code"] == dt.legacy_code
    else:
        assert added_data["legacy_code"] == ""

    if legacy_description:
        assert added_data["legacy_description"] == dt.legacy_description
    else:
        assert added_data["legacy_description"] == ""

    if target_model:
        assert added_data["target_model"] == dt.target_model.name
    else:
        assert added_data["target_model"] == ""

    if dt_type:
        assert added_data["type"] == dt.type.name
    else:
        assert added_data["type"] == ""

    if content_schema:
        assert json.loads(added_data["content_schema"]) == dt.content_schema
    else:
        assert added_data["content_schema"] == ""


@pytest.mark.parametrize(
    ("icon_file", "value", "unit", "size"),
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
    temp_icon_storage,
    icon_file,
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
    kwargs = {"code": "123"}
    icon_file_obj = TrafficControlDeviceTypeIconFactory(file__filename=icon_file) if icon_file else None
    kwargs["icon_file"] = icon_file_obj
    kwargs["value"] = value or ""
    kwargs["legacy_code"] = legacy_code or ""
    kwargs["legacy_description"] = legacy_description or ""
    if unit:
        kwargs["unit"] = unit
    if size:
        kwargs["size"] = size
    if target_model:
        kwargs["target_model"] = target_model
    if dt_type:
        kwargs["type"] = dt_type
    if content_schema:
        kwargs["content_schema"] = content_schema

    orig_uuid = TrafficControlDeviceTypeFactory(**kwargs).id

    dataset = get_import_dataset(TrafficControlDeviceTypeResource, format=format)
    TrafficControlDeviceType.objects.all().delete()
    assert TrafficControlDeviceType.objects.count() == 0
    result = TrafficControlDeviceTypeResource().import_data(dataset, raise_errors=False, collect_failed_rows=True)

    assert not result.has_validation_errors()
    assert not result.has_errors()
    assert result.totals["new"] == 1 + DEVICE_TYPE_COUNT_OFFSET
    assert TrafficControlDeviceType.objects.count() == 1 + DEVICE_TYPE_COUNT_OFFSET
    imported_dt = TrafficControlDeviceType.objects.exclude(code="DummyDT").first()

    assert imported_dt.code == "123"
    assert imported_dt.icon_file == icon_file_obj
    assert imported_dt.content_schema == content_schema
    assert imported_dt.value == value
    assert imported_dt.unit == unit
    assert imported_dt.size == size
    assert imported_dt.legacy_code == legacy_code
    assert imported_dt.legacy_description == legacy_description
    assert imported_dt.target_model == target_model
    assert imported_dt.type == dt_type
    # id in import phase should be ignored
    assert imported_dt.id != orig_uuid


@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db
def test__traffic_control_device_type__import__invalid_content_schema(format):
    TrafficControlDeviceTypeFactory()
    dataset = get_import_dataset(
        TrafficControlDeviceTypeResource,
        format=format,
        delete_columns=["content_schema"],
        queryset=TrafficControlDeviceType.objects.exclude(code="DummyDT"),
    )
    dataset.append_col(['{"invalid", "json}'], header="content_schema")
    TrafficControlDeviceType.objects.exclude(code="DummyDT").delete()

    result = TrafficControlDeviceTypeResource().import_data(dataset, raise_errors=False, collect_failed_rows=True)
    assert not result.has_errors()
    assert result.has_validation_errors()
    assert result.invalid_rows[0].field_specific_errors.get("content_schema")
    assert TrafficControlDeviceType.objects.count() == DEVICE_TYPE_COUNT_OFFSET


@pytest.mark.parametrize(
    "to_values",
    (
        {
            "code": "VALUE",
            "icon_file": "A2.svg",
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
            "code": "VALUE",
            "icon_file": "",
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
            "code": "VALUE",
            "icon_file": "A1.svg",
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
            "code": "VALUE",
            "icon_file": "",
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
    temp_icon_storage,
    to_values,
    from_values,
    format,
):
    from_icon = (
        TrafficControlDeviceTypeIconFactory(file__filename=from_values["icon_file"])
        if from_values["icon_file"]
        else None
    )
    to_icon = (
        TrafficControlDeviceTypeIconFactory(file__filename=to_values["icon_file"]) if to_values["icon_file"] else None
    )

    factory_kwargs = to_values.copy()
    del factory_kwargs["icon_file"]
    device_type = TrafficControlDeviceTypeFactory(icon_file=to_icon, **factory_kwargs)
    dataset = get_import_dataset(TrafficControlDeviceTypeResource, format=format)
    assert len(dataset) == 1 + DEVICE_TYPE_COUNT_OFFSET

    device_type.code = from_values["code"]
    device_type.icon_file = from_icon
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
    assert result.totals["update"] == 1 + DEVICE_TYPE_COUNT_OFFSET
    assert TrafficControlDeviceType.objects.count() == 1 + DEVICE_TYPE_COUNT_OFFSET
    imported_dt = TrafficControlDeviceType.objects.exclude(code="DummyDT").first()

    assert imported_dt.code == to_values["code"]
    assert imported_dt.icon_file == to_icon
    assert imported_dt.description == to_values["description"]
    assert imported_dt.value == to_values["value"]
    assert imported_dt.unit == to_values["unit"]
    assert imported_dt.size == to_values["size"]
    assert imported_dt.legacy_code == to_values["legacy_code"]
    assert imported_dt.legacy_description == to_values["legacy_description"]
    assert imported_dt.target_model == to_values["target_model"]
    assert imported_dt.type == to_values["type"]
    assert imported_dt.content_schema == to_values["content_schema"]
    assert imported_dt.id == device_type.id

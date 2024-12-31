import pytest
from tablib import Dataset

from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.models import AdditionalSignPlan, AdditionalSignReal
from traffic_control.resources.additional_sign import (
    AdditionalSignPlanResource,
    AdditionalSignPlanToRealTemplateResource,
    AdditionalSignRealResource,
)
from traffic_control.tests.factories import (
    AdditionalSignPlanFactory,
    AdditionalSignRealFactory,
    get_additional_sign_plan,
    get_mount_plan,
    get_mount_real,
    get_owner,
    get_traffic_control_device_type,
    get_traffic_sign_plan,
    get_traffic_sign_real,
    TrafficSignRealFactory,
)
from traffic_control.tests.test_base_api import test_point
from traffic_control.tests.test_import_export.utils import file_formats, get_import_dataset


@pytest.mark.django_db
def test__additional_sign_real__export():
    obj = AdditionalSignRealFactory()
    dataset = AdditionalSignRealResource().export()

    assert dataset.dict[0]["location"] == str(obj.location)
    assert dataset.dict[0]["owner__name_fi"] == obj.owner.name_fi
    assert dataset.dict[0]["lifecycle"] == obj.lifecycle.name


@pytest.mark.parametrize(
    "resource, model, factory",
    (
        (AdditionalSignPlanResource, AdditionalSignPlan, get_additional_sign_plan),
        (AdditionalSignRealResource, AdditionalSignReal, AdditionalSignRealFactory),
    ),
)
@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db
def test__additional_sign_real__import(resource, model, factory, format):
    fid = factory().id
    dataset = get_import_dataset(resource, format=format, delete_columns=["id"])
    model.objects.all().delete()

    assert model.objects.all().count() == 0
    result = resource().import_data(dataset, raise_errors=False, collect_failed_rows=True)

    assert not result.has_errors()
    assert result.totals["new"] == 1
    assert model.objects.all().count() == 1
    assert model.objects.all().first().id != fid


schema_1 = {
    "type": "object",
    "properties": {
        "bool": {
            "type": "boolean",
        },
        "num": {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
        },
        "int": {
            "type": "integer",
            "minimum": 0,
            "maximum": 100,
        },
        "str": {
            "type": "string",
            "minLength": 2,
            "maxLength": 20,
        },
        "str_nolimit": {
            "type": "string",
        },
        "enum": {
            "type": "string",
            "enum": ["Value 1", "Value 2"],
        },
        "obj": {
            "type": "object",
            "properties": {"str": {"type": "string"}},
            "additionalProperties": False,
            "required": ["str"],
        },
        "list": {
            "type": "array",
            "maxContains": 2,
        },
        "not_required": {
            "type": "string",
            "minLength": 1,
        },
    },
    "additionalProperties": False,
    "required": [
        "bool",
        "num",
        "int",
        "str",
        "str_nolimit",
        "enum",
        "obj",
        "list",
    ],
}
content_1 = {
    "bool": True,
    "num": 50.5,
    "int": 10,
    "str": "String value",
    "str_nolimit": "",
    "enum": "Value 1",
    "obj": {"str": "asdf"},
    "list": ["one", "two"],
}

schema_2 = {
    "type": "object",
    "properties": {
        "int": {
            "type": "integer",
        },
        "another_int": {
            "type": "integer",
        },
    },
    "additionalProperties": False,
    "required": [
        "int",
        "another_int",
    ],
}
content_2 = {
    "int": 1234,
    "another_int": 4321,
}


@pytest.mark.parametrize("resource", (AdditionalSignRealResource, AdditionalSignPlanResource))
@pytest.mark.django_db
def test_additional_sign_template__export(resource):
    """test template export, this happens when no data is provided."""
    get_traffic_control_device_type(
        code="type1",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        content_schema=schema_1,
    )
    dataset = resource().export()
    assert dataset.dict == []
    # check that all content_s fields from schema_1 are present
    assert "content_s.bool" in dataset.headers
    assert "content_s.num" in dataset.headers
    assert "content_s.int" in dataset.headers
    assert "content_s.str" in dataset.headers
    assert "content_s.str_nolimit" in dataset.headers
    assert "content_s.enum" in dataset.headers
    assert "content_s.obj" in dataset.headers
    assert "content_s.list" in dataset.headers
    assert "content_s.not_required" in dataset.headers


@pytest.mark.parametrize(
    "resource, factory",
    (
        (AdditionalSignPlanResource, AdditionalSignPlanFactory),
        (AdditionalSignRealResource, AdditionalSignRealFactory),
    ),
)
@pytest.mark.django_db
def test__additional_sign__export_with_content(resource, factory):
    dt_with_schema_1 = get_traffic_control_device_type(
        code="type1",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        content_schema=schema_1,
    )
    dt_with_schema_2 = get_traffic_control_device_type(
        code="type2",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        content_schema=schema_2,
    )
    dt_no_schema = get_traffic_control_device_type(
        code="type3",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
    )
    additional_sign_0 = factory(
        device_type=dt_with_schema_1,
        content_s=content_1,
    )
    additional_sign_1 = factory(
        device_type=dt_with_schema_2,
        content_s=content_2,
    )
    additional_sign_2 = factory(
        device_type=dt_no_schema,
    )

    dataset = resource().export()

    assert len(dataset) == 3

    assert dataset.dict[0]["device_type__code"] == additional_sign_0.device_type.code
    assert dataset.dict[0]["content_s.bool"] is additional_sign_0.content_s["bool"]
    assert dataset.dict[0]["content_s.num"] == additional_sign_0.content_s["num"]
    assert dataset.dict[0]["content_s.int"] == additional_sign_0.content_s["int"]
    assert dataset.dict[0]["content_s.str"] == additional_sign_0.content_s["str"]
    assert dataset.dict[0]["content_s.enum"] == additional_sign_0.content_s["enum"]
    assert dataset.dict[0]["content_s.another_int"] is None
    assert dataset.dict[0]["source_name"] == additional_sign_0.source_name
    assert dataset.dict[0]["source_id"] == additional_sign_0.source_id

    assert dataset.dict[1]["device_type__code"] == additional_sign_1.device_type.code
    assert dataset.dict[1]["content_s.bool"] is None
    assert dataset.dict[1]["content_s.num"] is None
    assert dataset.dict[1]["content_s.int"] == additional_sign_1.content_s["int"]
    assert dataset.dict[1]["content_s.str"] is None
    assert dataset.dict[1]["content_s.enum"] is None
    assert dataset.dict[1]["content_s.another_int"] == additional_sign_1.content_s["another_int"]
    assert dataset.dict[1]["source_name"] == additional_sign_1.source_name
    assert dataset.dict[1]["source_id"] == additional_sign_1.source_id

    assert dataset.dict[2]["device_type__code"] == additional_sign_2.device_type.code
    assert dataset.dict[2]["content_s.bool"] is None
    assert dataset.dict[2]["content_s.num"] is None
    assert dataset.dict[2]["content_s.int"] is None
    assert dataset.dict[2]["content_s.str"] is None
    assert dataset.dict[2]["content_s.enum"] is None
    assert dataset.dict[2]["content_s.another_int"] is None
    assert dataset.dict[2]["source_name"] == additional_sign_2.source_name
    assert dataset.dict[2]["source_id"] == additional_sign_2.source_id


@pytest.mark.parametrize(
    "model, resource, factory",
    (
        (AdditionalSignPlan, AdditionalSignPlanResource, AdditionalSignPlanFactory),
        (AdditionalSignReal, AdditionalSignRealResource, AdditionalSignRealFactory),
    ),
)
@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db
def test__additional_sign__import__create_with_content(model, resource, factory, format):
    dt_with_schema_1 = get_traffic_control_device_type(
        code="type1",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        content_schema=schema_1,
    )
    dt_with_schema_2 = get_traffic_control_device_type(
        code="type2",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        content_schema=schema_2,
    )
    dt_no_schema = get_traffic_control_device_type(
        code="type3",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
    )

    factory(
        device_type=dt_with_schema_1,
        content_s=content_1,
        missing_content=False,
        source_name="SCHEMA_1",
        source_id="SCHEMA_1",
    )
    factory(
        device_type=dt_with_schema_2,
        content_s=content_2,
        missing_content=False,
        source_name="SCHEMA_2",
        source_id="SCHEMA_2",
    )
    factory(
        device_type=dt_no_schema,
        missing_content=True,
        source_name="NO_SCHEMA",
        source_id="NO_SCHEMA",
    )

    dataset = get_import_dataset(resource, format=format, delete_columns=["id"])
    # add content_s column that does not exist in the device type, it should just be ignored
    dataset.dict[0]["content_s.does_not_exits_in_schema"] = "Some value"
    dataset.dict[1]["content_s.does_not_exits_in_schema"] = "Some value"
    dataset.dict[2]["content_s.does_not_exits_in_schema"] = "Some value"
    model.objects.all().delete()

    result = resource().import_data(dataset, raise_errors=True, collect_failed_rows=True)

    assert not result.has_validation_errors()
    assert not result.has_errors()

    assert model.objects.all().count() == 3
    obj1 = model.objects.get(source_name="SCHEMA_1", source_id="SCHEMA_1")
    assert obj1.content_s == content_1
    assert obj1.device_type == dt_with_schema_1

    obj2 = model.objects.get(source_name="SCHEMA_2", source_id="SCHEMA_2")
    assert obj2.content_s == content_2
    assert obj2.device_type == dt_with_schema_2

    obj3 = model.objects.get(source_name="NO_SCHEMA", source_id="NO_SCHEMA")
    assert obj3.content_s is None
    assert obj3.device_type == dt_no_schema


@pytest.mark.parametrize(
    "model, resource, factory",
    (
        (AdditionalSignPlan, AdditionalSignPlanResource, AdditionalSignPlanFactory),
        (AdditionalSignReal, AdditionalSignRealResource, AdditionalSignRealFactory),
    ),
    ids=("plan", "real"),
)
@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db
def test__additional_sign__import__create_with_missing_content(model, resource, factory, format):
    dt_with_schema_1 = get_traffic_control_device_type(
        code="type1",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        content_schema=schema_1,
    )
    dt_with_schema_2 = get_traffic_control_device_type(
        code="type2",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        content_schema=schema_2,
    )
    dt_no_schema = get_traffic_control_device_type(
        code="type3",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
    )

    factory(
        device_type=dt_with_schema_1,
        content_s=None,
        missing_content=True,
        source_name="SCHEMA_1",
        source_id="SCHEMA_1",
    )
    factory(
        device_type=dt_with_schema_2,
        content_s=None,
        missing_content=True,
        source_name="SCHEMA_2",
        source_id="SCHEMA_2",
    )
    factory(
        device_type=dt_no_schema,
        missing_content=True,
        source_name="NO_SCHEMA",
        source_id="NO_SCHEMA",
    )

    dataset = get_import_dataset(resource, format=format, delete_columns=["id"])
    model.objects.all().delete()

    result = resource().import_data(dataset, raise_errors=True, collect_failed_rows=True)

    assert not result.has_validation_errors()
    assert not result.has_errors()

    assert model.objects.all().count() == 3
    obj1 = model.objects.get(source_name="SCHEMA_1", source_id="SCHEMA_1")
    assert obj1.content_s is None
    assert obj1.missing_content is True
    assert obj1.device_type == dt_with_schema_1

    obj2 = model.objects.get(source_name="SCHEMA_2", source_id="SCHEMA_2")
    assert obj2.content_s is None
    assert obj2.missing_content is True
    assert obj2.device_type == dt_with_schema_2

    obj3 = model.objects.get(source_name="NO_SCHEMA", source_id="NO_SCHEMA")
    assert obj3.content_s is None
    assert obj2.missing_content is True
    assert obj3.device_type == dt_no_schema


@pytest.mark.parametrize(
    "model, resource, factory",
    (
        (AdditionalSignPlan, AdditionalSignPlanResource, get_additional_sign_plan),
        (AdditionalSignReal, AdditionalSignRealResource, AdditionalSignRealFactory),
    ),
    ids=("plan", "real"),
)
@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db
def test__additional_sign__import__create_fails_with_content_and_missing_content(model, resource, factory, format):
    dt_with_schema_1 = get_traffic_control_device_type(
        code="type1",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        content_schema=schema_1,
    )

    factory(
        device_type=dt_with_schema_1,
        content_s=content_1,
        missing_content=True,
    )

    dataset = get_import_dataset(resource, format=format, delete_columns=["id"])
    model.objects.all().delete()

    result = resource().import_data(dataset, raise_errors=False, collect_failed_rows=True)

    assert result.has_validation_errors()
    assert not result.has_errors()
    assert model.objects.all().count() == 0


@pytest.mark.parametrize(
    "model, resource, factory",
    (
        (AdditionalSignPlan, AdditionalSignPlanResource, AdditionalSignPlanFactory),
        (AdditionalSignReal, AdditionalSignRealResource, AdditionalSignRealFactory),
    ),
)
@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db
def test__additional_sign__import__create_with_invalid_content(model, resource, factory, format):
    dt_with_schema_1 = get_traffic_control_device_type(
        code="type1",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        content_schema=schema_1,
    )
    dt_with_schema_2 = get_traffic_control_device_type(
        code="type2",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        content_schema=schema_2,
    )
    dt_no_schema = get_traffic_control_device_type(
        code="type3",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
    )

    factory(
        device_type=dt_with_schema_1,
        content_s={"invalid_prop": "invalid_val"},
        source_name="SCHEMA_1",
        source_id="SCHEMA_1",
        missing_content=False,
    )
    factory(
        device_type=dt_with_schema_2,
        content_s=content_2,
        source_name="SCHEMA_2",
        source_id="SCHEMA_2",
        missing_content=False,
    )
    factory(
        device_type=dt_no_schema,
        source_name="NO_SCHEMA",
        source_id="NO_SCHEMA",
        missing_content=False,
    )

    dataset = get_import_dataset(resource, format=format, delete_columns=["id"])
    model.objects.all().delete()

    result = resource().import_data(dataset, raise_errors=False, collect_failed_rows=True)

    assert result.has_validation_errors()
    assert not result.has_errors()


@pytest.mark.parametrize(
    "model, resource, factory",
    (
        (AdditionalSignPlan, AdditionalSignPlanResource, get_additional_sign_plan),
        (AdditionalSignReal, AdditionalSignRealResource, AdditionalSignRealFactory),
    ),
)
@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db
def test__additional_sign__import__create_with_invalid_device_type(model, resource, factory, format):
    dt_with_schema_1 = get_traffic_control_device_type(
        code="type1",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        content_schema=schema_1,
    )

    factory(
        device_type=dt_with_schema_1,
        content_s=content_1,
    )

    dataset = get_import_dataset(resource, format=format, delete_columns=["id"])
    row = dataset.dict[0]
    row["device_type__code"] = "nonexistent"
    dataset.dict = [row]

    model.objects.all().delete()
    result = resource().import_data(dataset, raise_errors=False, collect_failed_rows=True)

    # TODO: Non-existing device type should be validation error, not actual error with stacktrace.
    assert not result.has_validation_errors()
    assert result.has_errors()
    assert result.failed_dataset.dict[0]["Error"] == "TrafficControlDeviceType matching query does not exist."


@pytest.mark.parametrize(
    "model, resource, factory",
    (
        (AdditionalSignPlan, AdditionalSignPlanResource, get_additional_sign_plan),
        (AdditionalSignReal, AdditionalSignRealResource, AdditionalSignRealFactory),
    ),
)
@pytest.mark.parametrize(
    "columns",
    (
        ("parent__id", "location", "owner__name_fi"),
        ("parent__id", "location", "owner__name_fi", "id"),
        ("parent__id", "location", "owner__name_fi", "device_type__code"),
        ("parent__id", "location", "owner__name_fi", "id", "device_type__code"),
    ),
)
@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db
def test__additional_sign__import__create_with_minimal_columns(model, resource, factory, columns, format):
    factory()

    dataset = get_import_dataset(resource, format=format)
    all_columns = dataset.headers.copy()
    for dataset_column in all_columns:
        if dataset_column not in columns:
            del dataset[dataset_column]
    assert set(dataset.headers) == set(columns)

    model.objects.all().delete()
    assert model.objects.all().count() == 0
    result = resource().import_data(dataset, raise_errors=False, collect_failed_rows=True)

    assert not result.has_validation_errors()
    assert not result.has_errors()
    assert model.objects.all().count() == 1


@pytest.mark.parametrize(
    "model, resource, factory",
    (
        (AdditionalSignPlan, AdditionalSignPlanResource, get_additional_sign_plan),
        (AdditionalSignReal, AdditionalSignRealResource, AdditionalSignRealFactory),
    ),
)
@pytest.mark.parametrize("has_device_type_column", (True, False))
@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db
def test__additional_sign__import__update_with_content(model, resource, factory, has_device_type_column, format):
    dt_with_schema_1 = get_traffic_control_device_type(
        code="type1",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        content_schema=schema_1,
    )

    additional_sign = factory(
        device_type=dt_with_schema_1,
        content_s=content_1,
        missing_content=False,
    )

    deleted_columns = [] if has_device_type_column else ["device_type__code"]
    dataset = get_import_dataset(resource, format=format, delete_columns=deleted_columns)
    row = dataset.dict[0]
    row["content_s.str"] = "Other value"
    # add content_s column that does not exist in the device type, it should just be ignored
    row["content_s.does_not_exits_in_schema"] = "Some value"
    dataset.dict = [row]

    result = resource().import_data(dataset, raise_errors=False, collect_failed_rows=True)

    assert not result.has_validation_errors()
    assert not result.has_errors()
    assert model.objects.all().count() == 1
    assert model.objects.all()[0].id == additional_sign.id
    assert str(model.objects.all()[0].id) == dataset.dict[0]["id"]
    assert model.objects.all()[0].content_s == {**content_1, "str": "Other value"}
    assert model.objects.all()[0].source_name == additional_sign.source_name
    assert model.objects.all()[0].source_id == additional_sign.source_id


@pytest.mark.parametrize(
    "model, resource, factory",
    (
        (AdditionalSignPlan, AdditionalSignPlanResource, AdditionalSignPlanFactory),
        (AdditionalSignReal, AdditionalSignRealResource, AdditionalSignRealFactory),
    ),
    ids=("plan", "real"),
)
@pytest.mark.parametrize("has_device_type_column", (True, False), ids=("with_device_type", "no_device_type"))
@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db
def test__additional_sign__import__update_with_missing_content(
    model, resource, factory, has_device_type_column, format
):
    """Test it is possible to add valid content and remove missing_content flag with import"""
    dt_with_schema_2 = get_traffic_control_device_type(
        code="type2",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        content_schema=schema_2,
    )

    additional_sign = factory(
        device_type=dt_with_schema_2,
        content_s=None,
        missing_content=True,
    )

    deleted_columns = [] if has_device_type_column else ["device_type__code"]
    dataset = get_import_dataset(resource, format=format, delete_columns=deleted_columns)
    row = dataset.dict[0]
    row["content_s.int"] = "1"
    row["content_s.another_int"] = "2"
    row["missing_content"] = "0"
    dataset.dict = [row]

    result = resource().import_data(dataset, raise_errors=False, collect_failed_rows=True)

    assert not result.has_validation_errors()
    assert not result.has_errors()
    assert model.objects.all().count() == 1
    assert model.objects.all()[0].id == additional_sign.id
    assert str(model.objects.all()[0].id) == dataset.dict[0]["id"]
    assert model.objects.all()[0].content_s == {"int": 1, "another_int": 2}
    assert model.objects.all()[0].source_name == additional_sign.source_name
    assert model.objects.all()[0].source_id == additional_sign.source_id


@pytest.mark.parametrize(
    "model, resource, factory",
    (
        (AdditionalSignPlan, AdditionalSignPlanResource, AdditionalSignPlanFactory),
        (AdditionalSignReal, AdditionalSignRealResource, AdditionalSignRealFactory),
    ),
)
@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db
def test__additional_sign__import__update_device_type_with_content(model, resource, factory, format):
    dt_with_schema_1 = get_traffic_control_device_type(
        code="type1",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        content_schema=schema_1,
    )

    dt_with_schema_2 = get_traffic_control_device_type(
        code="type2",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        content_schema=schema_2,
    )

    # Dataset to-be-import updates to new device type and appropriate content
    additional_sign = factory(
        device_type=dt_with_schema_1,
        content_s=content_1,
        missing_content=False,
    )
    dataset = get_import_dataset(resource, format=format)

    additional_sign.device_type = dt_with_schema_2
    additional_sign.content_s = content_2
    additional_sign.save()
    assert model.objects.all()[0].device_type == dt_with_schema_2
    assert model.objects.all()[0].content_s == content_2

    result = resource().import_data(dataset, raise_errors=False, collect_failed_rows=True)

    assert not result.has_validation_errors()
    assert not result.has_errors()
    assert model.objects.all().count() == 1
    assert model.objects.all()[0].id == additional_sign.id
    assert model.objects.all()[0].device_type == dt_with_schema_1
    assert model.objects.all()[0].content_s == content_1
    assert model.objects.all()[0].source_name == additional_sign.source_name
    assert model.objects.all()[0].source_id == additional_sign.source_id


@pytest.mark.parametrize(
    "model, resource, factory",
    (
        (AdditionalSignPlan, AdditionalSignPlanResource, AdditionalSignPlanFactory),
        (AdditionalSignReal, AdditionalSignRealResource, AdditionalSignRealFactory),
    ),
)
@pytest.mark.parametrize("has_device_type_column", (True, False))
@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db
def test__additional_sign__import__update_with_invalid_content(
    model, resource, factory, has_device_type_column, format
):
    dt_with_schema_1 = get_traffic_control_device_type(
        code="type1",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        content_schema=schema_1,
    )

    # Dataset to-be-import updates content invalid to device type schema
    additional_sign = factory(
        device_type=dt_with_schema_1,
        content_s={"invalid_prop": "invalid_val"},
        missing_content=False,
    )
    deleted_columns = [] if has_device_type_column else ["device_type__code"]
    dataset = get_import_dataset(resource, format=format, delete_columns=deleted_columns)

    additional_sign.content_s = content_1
    additional_sign.save()
    assert model.objects.all()[0].content_s == content_1

    result = resource().import_data(dataset, raise_errors=False, collect_failed_rows=True)

    assert result.has_validation_errors()
    assert not result.has_errors()
    assert model.objects.all().count() == 1
    assert model.objects.all()[0].id == additional_sign.id
    assert model.objects.all()[0].content_s == content_1
    assert model.objects.all()[0].source_name == additional_sign.source_name
    assert model.objects.all()[0].source_id == additional_sign.source_id


@pytest.mark.parametrize(
    "model, resource, factory",
    (
        (AdditionalSignPlan, AdditionalSignPlanResource, AdditionalSignPlanFactory),
        (AdditionalSignReal, AdditionalSignRealResource, AdditionalSignRealFactory),
    ),
)
@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db
def test__additional_sign__import__update_device_type_with_invalid_content(model, resource, factory, format):
    dt_with_schema_1 = get_traffic_control_device_type(
        code="type1",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        content_schema=schema_1,
    )

    dt_with_schema_2 = get_traffic_control_device_type(
        code="type2",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        content_schema=schema_2,
    )

    # Dataset to-be-import retains content, but changes device type to another with different schema
    additional_sign = factory(
        device_type=dt_with_schema_2,
        content_s=content_1,
        missing_content=False,
    )
    dataset = get_import_dataset(resource, format=format)

    additional_sign.device_type = dt_with_schema_1
    additional_sign.save()
    assert model.objects.all()[0].device_type == dt_with_schema_1
    assert model.objects.all()[0].content_s == content_1

    result = resource().import_data(dataset, raise_errors=False, collect_failed_rows=True)

    assert result.has_validation_errors()
    assert result.invalid_rows[0].error_dict == {"content_s": ["another_int: None is not of type 'integer'"]}
    assert not result.has_errors()
    assert model.objects.all().count() == 1
    assert model.objects.all()[0].id == additional_sign.id
    assert model.objects.all()[0].device_type == dt_with_schema_1
    assert model.objects.all()[0].content_s == content_1
    assert model.objects.all()[0].source_name == additional_sign.source_name
    assert model.objects.all()[0].source_id == additional_sign.source_id


schema_properties = (
    {
        "name": "bool",
        "property": {
            "bool": {
                "type": "boolean",
            }
        },
        "valid": [
            True,
            False,
            "true",
            "True",
            "false",
            "False",
            "1",
            "0",
            1,
            0,
        ],
        "invalid": [
            "asdf",
            "None",
            {},
            {"key": "value"},
            [],
            ["asdf"],
            None,
        ],
    },
    {
        "name": "num",
        "property": {
            "num": {
                "type": "number",
                "minimum": -5,
            }
        },
        "valid": [
            -1,
            -1.0,
            0,
            0.0,
            1,
            0.5,
            1.55555555,
            123456789012345678901234567890,
            "1",
            "1.55555",
        ],
        "invalid": [
            -6,
            "asdf",
            {},
            {"key": "value"},
            [],
            ["asdf"],
            None,
        ],
    },
    {
        "name": "int",
        "property": {
            "int": {
                "type": "integer",
                "minimum": -5,
            }
        },
        "valid": [
            -1,
            0,
            1,
            100,
            123456789012345678901234567890,
            "1",
        ],
        "invalid": [
            -6,
            0.5,
            True,
            False,
            "asdf",
            {},
            {"key": "value"},
            [],
            ["asdf"],
            None,
        ],
    },
    {
        "name": "str",
        "property": {
            "str": {
                "type": "string",
                "minLength": 1,
            }
        },
        "valid": [
            "a",
            "abc efg",
            "emoji 🚸",
            -1,
            0,
            0.5,
            1,
            True,
            False,
            {},
            {"key": "value"},
            [],
            ["asdf"],
        ],
        "invalid": [
            "",
            None,
        ],
    },
    {
        "name": "list",
        "property": {
            "list": {
                "type": "array",
                "maxItems": 2,
            }
        },
        "valid": [
            [],
            ["str", 123],
            "[]",
            '["str", 123]',
        ],
        "invalid": [
            ["str", 123, True],
            True,
            False,
            "asdf",
            {},
            {"key": "value"},
            None,
        ],
    },
    {
        "name": "obj",
        "property": {
            "obj": {
                "type": "object",
                "properties": {"str": {"type": "string"}},
                "additionalProperties": False,
                "required": ["str"],
            },
        },
        "valid": [
            {"str": ""},
            {"str": "text"},
            '{"str": ""}',
            '{"str": "text"}',
        ],
        "invalid": [
            {},
            {"other": "value"},
            {"str": "text", "other": "value"},
            "",
            -1,
            0,
            0.5,
            1,
            True,
            False,
            [],
            ["asdf"],
            None,
        ],
    },
)


@pytest.mark.parametrize(
    "model, resource",
    (
        (AdditionalSignPlan, AdditionalSignPlanResource),
        (AdditionalSignReal, AdditionalSignRealResource),
    ),
)
@pytest.mark.parametrize("validity", ("valid", "invalid"))
@pytest.mark.parametrize("schema_property", schema_properties, ids=lambda x: x["name"])
@pytest.mark.django_db
def test__additional_sign__import__valid_and_invalid_content_properties(schema_property, validity, model, resource):
    property_name = schema_property["name"]
    properties = schema_property["property"]

    schema = {
        "properties": properties,
        "additionalProperties": False,
        "required": [property_name],
    }

    dt = get_traffic_control_device_type(
        code="type1",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        content_schema=schema,
    )
    owner = get_owner()
    location = test_point
    additional_sign_data = {
        "device_type__code": dt.code,
        "location": str(location),
        "owner__name_fi": str(owner.name_fi),
    }

    if model == AdditionalSignReal:
        additional_sign_data.update({"parent__id": TrafficSignRealFactory().pk})

    expect_valid = True if validity == "valid" else False

    for value in schema_property[validity]:
        content_s_columns = {f"content_s.{property_name}": value}
        dataset = Dataset()
        dataset.dict = [{**additional_sign_data, **content_s_columns}]

        result = resource().import_data(dataset, raise_errors=False, collect_failed_rows=True)

        if expect_valid:
            assert not result.has_validation_errors()
            assert not result.has_errors()
            assert model.objects.all().count() == 1
            model.objects.all().delete()
        else:
            assert result.has_validation_errors()
            assert not result.has_errors()
            assert model.objects.all().count() == 0


@pytest.mark.parametrize("has_mount_plan", (True, False), ids=lambda x: "mount_plan" if x else "no_mount_plan")
@pytest.mark.parametrize("has_mount_real", (True, False), ids=lambda x: "mount_real" if x else "no_mount_real")
@pytest.mark.parametrize(
    "has_traffic_sign_plan",
    (True, False),
    ids=lambda x: "traffic_sign_plan" if x else "no_traffic_sign_plan",
)
@pytest.mark.parametrize(
    "has_traffic_sign_real",
    (True, False),
    ids=lambda x: "traffic_sign_real" if x else "no_traffic_sign_real",
)
@pytest.mark.parametrize("real_preexists", (True, False), ids=lambda x: "real_preexists" if x else "real_nonexists")
@pytest.mark.django_db
def test__additional_sign_plan_export_real_import(
    has_mount_plan,
    has_mount_real,
    has_traffic_sign_plan,
    has_traffic_sign_real,
    real_preexists,
):
    """Test that a plan object can be exported as its real object (referencing to the plan)"""

    mount_plan = get_mount_plan() if has_mount_plan else None
    mount_real = get_mount_real() if has_mount_real else None
    traffic_sign_plan = get_traffic_sign_plan() if has_traffic_sign_plan else None
    traffic_sign_real = get_traffic_sign_real() if has_traffic_sign_real else None

    plan_obj = get_additional_sign_plan(mount_plan=mount_plan, parent=traffic_sign_plan)
    real_obj = AdditionalSignRealFactory(additional_sign_plan=plan_obj) if real_preexists else None

    exported_dataset = AdditionalSignPlanToRealTemplateResource().export()

    real = exported_dataset.dict[0]
    assert real["additional_sign_plan__id"] == plan_obj.id

    if has_mount_plan and has_mount_real:
        assert real["mount_real__id"] == mount_real.id
    else:
        assert real["mount_real__id"] is None

    if has_traffic_sign_plan and has_traffic_sign_real:
        assert real["parent__id"] == traffic_sign_real.id
    else:
        assert real["parent__id"] is None

    if real_preexists:
        assert real["id"] == real_obj.id
    else:
        assert real["id"] is None

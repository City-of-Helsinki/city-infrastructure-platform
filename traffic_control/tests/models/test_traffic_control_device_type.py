from contextlib import nullcontext as does_not_raise

import pytest
from django.core.exceptions import ValidationError
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _

from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.models.traffic_sign import AbstractTrafficSign
from traffic_control.tests.factories import (
    AdditionalSignPlanFactory,
    AdditionalSignRealFactory,
    get_barrier_plan,
    get_barrier_real,
    get_road_marking_plan,
    get_road_marking_real,
    get_signpost_plan,
    get_signpost_real,
    get_traffic_light_plan,
    get_traffic_light_real,
    get_traffic_sign_plan,
    get_traffic_sign_real,
    TrafficControlDeviceTypeFactory,
    TrafficControlDeviceTypeIconFactory,
    TrafficSignPlanFactory,
    TrafficSignRealFactory,
)

simple_schema = {
    "type": "object",
    "properties": {
        "prop_str": {"type": "string"},
    },
    "additionalProperties": False,
}


content_valid_by_simple_schema = {
    "prop_str": "string value",
}

another_content_valid_by_simple_schema = {
    "prop_str": "another string value",
}

content_invalid_by_simple_schema = {
    "prop_str": 123,
}

simple_schema_2 = {
    "type": "object",
    "properties": {
        "prop_num": {"type": "number"},
    },
    "additionalProperties": False,
}

content_valid_by_simple_schema_2 = {
    "prop_num": 123,
}

content_invalid_by_simple_schema_2 = {
    "prop_num": "string value",
}

invalid_schema = {"type": "asdf"}


@pytest.mark.parametrize(
    "allowed_values,factory",
    (
        ([DeviceTypeTargetModel.BARRIER], get_barrier_plan),
        ([DeviceTypeTargetModel.BARRIER], get_barrier_real),
        ([DeviceTypeTargetModel.ROAD_MARKING], get_road_marking_plan),
        ([DeviceTypeTargetModel.ROAD_MARKING], get_road_marking_real),
        ([DeviceTypeTargetModel.SIGNPOST], get_signpost_plan),
        ([DeviceTypeTargetModel.SIGNPOST], get_signpost_real),
        ([DeviceTypeTargetModel.TRAFFIC_LIGHT], get_traffic_light_plan),
        ([DeviceTypeTargetModel.TRAFFIC_LIGHT], get_traffic_light_real),
        (AbstractTrafficSign.ALLOWED_TARGET_MODELS, get_traffic_sign_plan),
        (AbstractTrafficSign.ALLOWED_TARGET_MODELS, get_traffic_sign_real),
        ([DeviceTypeTargetModel.ADDITIONAL_SIGN], AdditionalSignPlanFactory),
        ([DeviceTypeTargetModel.ADDITIONAL_SIGN], AdditionalSignRealFactory),
    ),
)
@pytest.mark.django_db
def test__traffic_control_device_type__target_model__restricts_relations(allowed_values, factory):
    related_obj = factory()
    for choice in DeviceTypeTargetModel:
        device_type = TrafficControlDeviceTypeFactory(code=get_random_string(length=12), target_model=choice)
        if choice in allowed_values:
            related_obj.device_type = device_type
            related_obj.save(update_fields=["device_type"])
            related_obj.refresh_from_db()
            assert related_obj.device_type == device_type
        else:
            with pytest.raises(ValidationError):
                related_obj.device_type = device_type
                related_obj.save(update_fields=["device_type"])


@pytest.mark.parametrize(
    "new_target_model,factory",
    (
        (DeviceTypeTargetModel.BARRIER, get_barrier_plan),
        (DeviceTypeTargetModel.BARRIER, get_barrier_real),
        (DeviceTypeTargetModel.ROAD_MARKING, get_road_marking_plan),
        (DeviceTypeTargetModel.ROAD_MARKING, get_road_marking_real),
        (DeviceTypeTargetModel.SIGNPOST, get_signpost_plan),
        (DeviceTypeTargetModel.SIGNPOST, get_signpost_real),
        (DeviceTypeTargetModel.TRAFFIC_LIGHT, get_traffic_light_plan),
        (DeviceTypeTargetModel.TRAFFIC_LIGHT, get_traffic_light_real),
        (DeviceTypeTargetModel.TRAFFIC_SIGN, get_traffic_sign_plan),
        (DeviceTypeTargetModel.TRAFFIC_SIGN, get_traffic_sign_real),
        (DeviceTypeTargetModel.ADDITIONAL_SIGN, AdditionalSignPlanFactory),
        (DeviceTypeTargetModel.ADDITIONAL_SIGN, AdditionalSignRealFactory),
    ),
)
@pytest.mark.django_db
def test__traffic_control_device_type__target_model__update_is_valid(new_target_model, factory):
    device_type = TrafficControlDeviceTypeFactory()
    factory(device_type=device_type)

    device_type.target_model = new_target_model
    device_type.save()

    device_type.refresh_from_db()
    assert device_type.target_model is new_target_model


@pytest.mark.parametrize(
    "new_target_model,factory",
    (
        (DeviceTypeTargetModel.ROAD_MARKING, get_barrier_plan),
        (DeviceTypeTargetModel.ROAD_MARKING, get_barrier_real),
        (DeviceTypeTargetModel.SIGNPOST, get_road_marking_plan),
        (DeviceTypeTargetModel.SIGNPOST, get_road_marking_real),
        (DeviceTypeTargetModel.TRAFFIC_LIGHT, get_signpost_plan),
        (DeviceTypeTargetModel.TRAFFIC_LIGHT, get_signpost_real),
        (DeviceTypeTargetModel.TRAFFIC_SIGN, get_traffic_light_plan),
        (DeviceTypeTargetModel.TRAFFIC_SIGN, get_traffic_light_real),
        (DeviceTypeTargetModel.ADDITIONAL_SIGN, get_traffic_sign_plan),
        (DeviceTypeTargetModel.ADDITIONAL_SIGN, get_traffic_sign_real),
        (DeviceTypeTargetModel.BARRIER, AdditionalSignPlanFactory),
        (DeviceTypeTargetModel.BARRIER, AdditionalSignRealFactory),
    ),
)
@pytest.mark.django_db
def test__traffic_control_device_type__target_model__update_is_invalid(new_target_model, factory):
    device_type = TrafficControlDeviceTypeFactory()
    factory(device_type=device_type)

    with pytest.raises(ValidationError):
        device_type.target_model = new_target_model
        device_type.save()

    device_type.refresh_from_db()
    assert not device_type.target_model


@pytest.mark.django_db
def test__traffic_control_device_type__target_model__validate_multiple_invalid_relations():
    device_type = TrafficControlDeviceTypeFactory()
    get_barrier_plan(device_type=device_type)
    get_barrier_real(device_type=device_type)
    get_road_marking_plan(device_type=device_type)
    get_road_marking_real(device_type=device_type)
    get_signpost_plan(device_type=device_type)
    get_signpost_real(device_type=device_type)
    get_traffic_light_plan(device_type=device_type)
    get_traffic_light_real(device_type=device_type)
    get_traffic_sign_plan(device_type=device_type)
    get_traffic_sign_real(device_type=device_type)
    AdditionalSignPlanFactory(device_type=device_type)
    AdditionalSignRealFactory(device_type=device_type)

    for target_model in DeviceTypeTargetModel:
        with pytest.raises(ValidationError):
            device_type.target_model = target_model
            device_type.save()

        device_type.refresh_from_db()
        assert not device_type.target_model


@pytest.mark.parametrize(
    "code,expected_value",
    (
        ("A1", _("Warning sign")),
        ("B1", _("Priority or give-way sign")),
        ("C1", _("Prohibitory or restrictive sign")),
        ("D1", _("Mandatory sign")),
        ("E1", _("Regulatory sign")),
        ("F1", _("Information sign")),
        ("G1", _("Service sign")),
        ("H1", _("Additional sign")),
        ("I1", _("Other road sign")),
        ("X", None),
        ("123", None),
    ),
)
@pytest.mark.django_db
def test__traffic_control_device_type__traffic_sign_type(code, expected_value):
    device_type = TrafficControlDeviceTypeFactory(code=code)

    assert device_type.traffic_sign_type == expected_value


@pytest.mark.parametrize(
    "schema,expect_valid",
    (
        (None, True),
        (simple_schema, True),
        (invalid_schema, False),
        ({}, True),
        (True, False),
        (False, False),
        (123, False),
        ("string", False),
        ([], False),
        (["string in array"], False),
        ([{}], False),
    ),
    ids=lambda x: str(x),
)
@pytest.mark.django_db
def test__traffic_control_device_type__content_schema__valid_values(schema, expect_valid):
    expectation = does_not_raise() if expect_valid else pytest.raises(ValidationError)

    device_type = TrafficControlDeviceTypeFactory(content_schema=schema)
    with expectation:
        device_type.full_clean()

    if expect_valid:
        assert device_type.content_schema == schema


@pytest.mark.parametrize(
    "target_model,expect_valid",
    (
        (DeviceTypeTargetModel.ADDITIONAL_SIGN, True),
        (DeviceTypeTargetModel.ROAD_MARKING, False),
        (DeviceTypeTargetModel.SIGNPOST, False),
        (DeviceTypeTargetModel.TRAFFIC_LIGHT, False),
        (DeviceTypeTargetModel.TRAFFIC_SIGN, False),
        (DeviceTypeTargetModel.BARRIER, False),
        (DeviceTypeTargetModel.OTHER, False),
        (None, True),
    ),
)
@pytest.mark.django_db
def test__traffic_control_device_type__content_schema__valid_for_target_models(target_model, expect_valid):
    content_schema = simple_schema
    device_type = TrafficControlDeviceTypeFactory(target_model=target_model, content_schema=content_schema)

    if expect_valid:
        device_type.full_clean()
        assert device_type.target_model == target_model
        assert device_type.content_schema == content_schema
    else:
        with pytest.raises(ValidationError):
            device_type.full_clean()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model_factory, target_model",
    (
        (TrafficSignRealFactory, DeviceTypeTargetModel.SIGNPOST),
        (TrafficSignRealFactory, DeviceTypeTargetModel.BARRIER),
        (TrafficSignRealFactory, DeviceTypeTargetModel.TRAFFIC_SIGN),
        (TrafficSignPlanFactory, DeviceTypeTargetModel.SIGNPOST),
        (TrafficSignPlanFactory, DeviceTypeTargetModel.BARRIER),
        (TrafficSignPlanFactory, DeviceTypeTargetModel.TRAFFIC_SIGN),
    ),
)
def test__object_with_mismatching_target_model_can_be_changed(model_factory, target_model):
    """Currently possible only for trafficsignreals/plans that can have devicetype with additional target_models.
    See AbstractTrafficSign.ALLOWED_TARGET_MODELS for more details.
    Tests that device type objects other fields can still be modified.
    """
    orig_icon = TrafficControlDeviceTypeIconFactory()
    dt = TrafficControlDeviceTypeFactory(
        code="test", description="test desc", icon_file=orig_icon, target_model=target_model
    )
    model_factory(device_type=dt)
    dt.description = "test desc2"
    new_icon = TrafficControlDeviceTypeIconFactory()
    dt.icon = new_icon
    dt.save(update_fields=["description", "icon_file"])
    dt.refresh_from_db()
    assert dt.description == "test desc2"
    assert dt.icon == new_icon

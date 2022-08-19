import pytest
from django.core.exceptions import ValidationError
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _

from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.tests.factories import (
    get_additional_sign_plan,
    get_additional_sign_real,
    get_barrier_plan,
    get_barrier_real,
    get_road_marking_plan,
    get_road_marking_real,
    get_signpost_plan,
    get_signpost_real,
    get_traffic_control_device_type,
    get_traffic_light_plan,
    get_traffic_light_real,
    get_traffic_sign_plan,
    get_traffic_sign_real,
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
    "allowed_value,factory",
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
        (DeviceTypeTargetModel.ADDITIONAL_SIGN, get_additional_sign_plan),
        (DeviceTypeTargetModel.ADDITIONAL_SIGN, get_additional_sign_real),
    ),
)
@pytest.mark.django_db
def test__traffic_control_device_type__target_model__restricts_relations(allowed_value, factory):
    related_obj = factory()

    for choice in DeviceTypeTargetModel:
        device_type = get_traffic_control_device_type(code=get_random_string(length=12), target_model=choice)

        if choice == allowed_value:
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
        (DeviceTypeTargetModel.ADDITIONAL_SIGN, get_additional_sign_plan),
        (DeviceTypeTargetModel.ADDITIONAL_SIGN, get_additional_sign_real),
    ),
)
@pytest.mark.django_db
def test__traffic_control_device_type__target_model__update_is_valid(new_target_model, factory):
    device_type = get_traffic_control_device_type()
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
        (DeviceTypeTargetModel.BARRIER, get_additional_sign_plan),
        (DeviceTypeTargetModel.BARRIER, get_additional_sign_real),
    ),
)
@pytest.mark.django_db
def test__traffic_control_device_type__target_model__update_is_invalid(new_target_model, factory):
    device_type = get_traffic_control_device_type()
    factory(device_type=device_type)

    with pytest.raises(ValidationError):
        device_type.target_model = new_target_model
        device_type.save()

    device_type.refresh_from_db()
    assert not device_type.target_model


@pytest.mark.django_db
def test__traffic_control_device_type__target_model__validate_multiple_invalid_relations():
    device_type = get_traffic_control_device_type()
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
    get_additional_sign_plan(device_type=device_type)
    get_additional_sign_real(device_type=device_type)

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
    device_type = get_traffic_control_device_type(code=code)

    assert device_type.traffic_sign_type == expected_value

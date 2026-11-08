"""Tests that device type validation is reported as inline field errors.

The rules are enforced in both ``clean()`` (so the Django admin renders them next to
the field) and ``save()`` (so importers and API serializers keep their guard).
"""
import pytest
from django.core.exceptions import ValidationError

from city_furniture.enums import CityFurnitureDeviceTypeTargetModel
from city_furniture.tests.factories import (
    CityFurnitureDeviceTypeFactory,
    FurnitureSignpostRealFactory,
)
from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.models import AdditionalSignReal, BarrierReal
from traffic_control.tests.factories import (
    AdditionalSignRealFactory,
    BarrierRealFactory,
    RoadMarkingRealFactory,
    SignpostRealFactory,
    TrafficControlDeviceTypeFactory,
    TrafficLightRealFactory,
    TrafficSignRealFactory,
)

DEVICE_MODEL_CASES = [
    (BarrierRealFactory, DeviceTypeTargetModel.SIGNPOST, "barriers"),
    (SignpostRealFactory, DeviceTypeTargetModel.BARRIER, "signposts"),
    (TrafficLightRealFactory, DeviceTypeTargetModel.BARRIER, "traffic lights"),
    (RoadMarkingRealFactory, DeviceTypeTargetModel.BARRIER, "road markings"),
    (AdditionalSignRealFactory, DeviceTypeTargetModel.BARRIER, "additional signs"),
    (TrafficSignRealFactory, DeviceTypeTargetModel.ROAD_MARKING, "traffic signs"),
]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "factory_class,invalid_target_model,error_target",
    DEVICE_MODEL_CASES,
    ids=[case[2] for case in DEVICE_MODEL_CASES],
)
def test__device_type_relation__clean__reports_inline_field_error(
    factory_class, invalid_target_model: DeviceTypeTargetModel, error_target: str
) -> None:
    """Disallowed device types are reported as a `device_type` field error by clean()."""
    device = factory_class()
    device.device_type = TrafficControlDeviceTypeFactory(target_model=invalid_target_model)

    with pytest.raises(ValidationError) as exc_info:
        device.clean()

    assert "device_type" in exc_info.value.message_dict
    assert f"is not allowed for {error_target}" in exc_info.value.message_dict["device_type"][0]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "factory_class,invalid_target_model,error_target",
    DEVICE_MODEL_CASES,
    ids=[case[2] for case in DEVICE_MODEL_CASES],
)
def test__device_type_relation__save__still_raises(
    factory_class, invalid_target_model: DeviceTypeTargetModel, error_target: str
) -> None:
    """Paths that skip full_clean() (API, importers) keep the save() guard."""
    device = factory_class()
    device.device_type = TrafficControlDeviceTypeFactory(target_model=invalid_target_model)

    with pytest.raises(ValidationError) as exc_info:
        device.save()

    assert "device_type" in exc_info.value.message_dict


@pytest.mark.django_db
@pytest.mark.parametrize(
    "factory_class",
    [BarrierRealFactory, SignpostRealFactory, TrafficLightRealFactory, RoadMarkingRealFactory, TrafficSignRealFactory],
)
def test__device_type_relation__clean__allows_device_type_without_target_model(factory_class) -> None:
    """A device type without a target model is allowed for every device."""
    device = factory_class()
    device.device_type = TrafficControlDeviceTypeFactory(target_model=None)

    device.clean()
    device.save()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "allowed_target_model",
    [DeviceTypeTargetModel.TRAFFIC_SIGN, DeviceTypeTargetModel.SIGNPOST, DeviceTypeTargetModel.BARRIER],
)
def test__traffic_sign__clean__allows_all_allowed_target_models(
    allowed_target_model: DeviceTypeTargetModel,
) -> None:
    """Traffic signs accept every target model listed in ALLOWED_TARGET_MODELS."""
    device = TrafficSignRealFactory()
    device.device_type = TrafficControlDeviceTypeFactory(target_model=allowed_target_model)

    device.clean()


@pytest.mark.django_db
def test__device_type_relation__full_clean__collects_field_error() -> None:
    """full_clean(), as called by ModelForm._post_clean, collects the field error."""
    barrier = BarrierRealFactory()
    barrier.device_type = TrafficControlDeviceTypeFactory(target_model=DeviceTypeTargetModel.SIGNPOST)

    with pytest.raises(ValidationError) as exc_info:
        barrier.full_clean()

    assert "device_type" in exc_info.value.message_dict


@pytest.mark.django_db
@pytest.mark.parametrize("model_class", [BarrierReal, AdditionalSignReal])
def test__device_type_relation__clean__does_not_raise_when_device_type_is_unset(model_class) -> None:
    """clean() must not blow up on an unset non-nullable device type, as the admin calls it anyway."""
    model_class().clean()


@pytest.mark.django_db
def test__furniture_signpost__clean__reports_inline_field_error(monkeypatch) -> None:
    """Disallowed device types on furniture signposts are reported inline.

    `CityFurnitureDeviceTypeTargetModel` currently has a single member, so the
    rejecting branch is forced through the device type's own validation method.
    """
    signpost = FurnitureSignpostRealFactory()
    monkeypatch.setattr(type(signpost.device_type), "validate_relation", lambda self, model: False)

    with pytest.raises(ValidationError) as exc_info:
        signpost.clean()

    assert "device_type" in exc_info.value.message_dict
    assert "is not allowed for furniture signposts" in exc_info.value.message_dict["device_type"][0]


@pytest.mark.django_db
def test__city_furniture_device_type__clean__validates_target_model_change(monkeypatch) -> None:
    """Changing target model to one that breaks existing relations is reported by clean()."""
    device_type = CityFurnitureDeviceTypeFactory(code="TargetModelChange", target_model=None)
    FurnitureSignpostRealFactory(device_type=device_type)
    device_type.target_model = CityFurnitureDeviceTypeTargetModel.FURNITURE_SIGNPOST
    monkeypatch.setattr(type(device_type), "_has_invalid_related_models", lambda self, target_type: True)

    with pytest.raises(ValidationError):
        device_type.clean()

import pytest
from django.contrib.admin import AdminSite

from traffic_control.admin.common import DeviceTypeTargetModelFilter
from traffic_control.admin.traffic_sign import TrafficControlDeviceTypeAdmin
from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.forms import TrafficControlDeviceTypeForm
from traffic_control.models import TrafficControlDeviceType
from traffic_control.tests.factories import (
    AdditionalSignRealFactory,
    get_user,
    TrafficControlDeviceTypeFactory,
    TrafficControlDeviceTypeIconFactory,
)


@pytest.fixture
def device_type_admin():
    return TrafficControlDeviceTypeAdmin(TrafficControlDeviceType, AdminSite())


@pytest.mark.parametrize("create_related_object, expect_valid", ((False, True), (True, False)))
@pytest.mark.django_db
def test__traffic_control_device_type_admin__change_target_model(create_related_object, expect_valid):
    """
    The traffic control device type form prevents an editor from altering the target
    model of a traffic control device type that is currently in use. The error message
    will be informative.

    """
    data = {
        "code": "D123",
        "icon_file": TrafficControlDeviceTypeIconFactory(),
        "description": "A test device type",
        "legacy_code": "123D",
        "legacy_description": "A legacy description",
        "target_model": DeviceTypeTargetModel.ADDITIONAL_SIGN,
    }
    dt = TrafficControlDeviceTypeFactory(**data)
    data["target_model"] = DeviceTypeTargetModel.TRAFFIC_SIGN

    if create_related_object is True:
        AdditionalSignRealFactory(device_type=dt)
    else:
        pass

    form = TrafficControlDeviceTypeForm(data, instance=dt)
    if expect_valid:
        assert form.is_valid() is True
        form.save()
    else:
        assert form.is_valid() is False
        with pytest.raises(ValueError):
            form.save()
        assert "devices related to this device type instance will become invalid" in form.errors["__all__"][0]


@pytest.mark.django_db
def test__device_type_target_model_filter__lookups(rf, device_type_admin):
    """Filter offers all device type target model choices as lookups."""
    request = rf.get("/")
    request.user = get_user(admin=True)
    filter_instance = DeviceTypeTargetModelFilter(request, {}, TrafficControlDeviceType, device_type_admin)

    assert list(filter_instance.lookups(request, device_type_admin)) == list(DeviceTypeTargetModel.choices)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "target_model",
    (
        DeviceTypeTargetModel.BARRIER,
        DeviceTypeTargetModel.ROAD_MARKING,
        DeviceTypeTargetModel.SIGNPOST,
        DeviceTypeTargetModel.TRAFFIC_LIGHT,
        DeviceTypeTargetModel.TRAFFIC_SIGN,
        DeviceTypeTargetModel.ADDITIONAL_SIGN,
        DeviceTypeTargetModel.OTHER,
    ),
)
def test__device_type_target_model_filter__filters_by_target_model(rf, device_type_admin, target_model):
    """Changelist contains only device types having the selected target model."""
    expected = TrafficControlDeviceTypeFactory(code=f"DT-{target_model.value}", target_model=target_model)
    for other_model in DeviceTypeTargetModel:
        if other_model != target_model:
            TrafficControlDeviceTypeFactory(code=f"OTHER-{other_model.value}", target_model=other_model)
    TrafficControlDeviceTypeFactory(code="NO-TARGET-MODEL", target_model=None)

    request = rf.get("/", {DeviceTypeTargetModelFilter.parameter_name: target_model.value})
    request.user = get_user(admin=True)
    changelist = device_type_admin.get_changelist_instance(request)

    assert list(changelist.get_queryset(request)) == [expected]


@pytest.mark.django_db
def test__device_type_target_model_filter__no_value_returns_all(rf, device_type_admin):
    """Changelist is not filtered when no target model is selected."""
    TrafficControlDeviceTypeFactory(code="DT-1", target_model=DeviceTypeTargetModel.BARRIER)
    TrafficControlDeviceTypeFactory(code="DT-2", target_model=DeviceTypeTargetModel.TRAFFIC_SIGN)
    TrafficControlDeviceTypeFactory(code="DT-3", target_model=None)

    request = rf.get("/")
    request.user = get_user(admin=True)
    changelist = device_type_admin.get_changelist_instance(request)

    codes = set(changelist.get_queryset(request).values_list("code", flat=True))
    assert {"DT-1", "DT-2", "DT-3"}.issubset(codes)
    assert len(codes) == TrafficControlDeviceType.objects.count()

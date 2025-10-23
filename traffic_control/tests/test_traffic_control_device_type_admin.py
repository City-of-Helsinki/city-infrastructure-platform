import pytest

from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.forms import TrafficControlDeviceTypeForm
from traffic_control.tests.factories import (
    AdditionalSignRealFactory,
    TrafficControlDeviceTypeFactory,
    TrafficControlDeviceTypeIconFactory,
)


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

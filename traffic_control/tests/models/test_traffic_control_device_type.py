import pytest
from django.core.exceptions import ValidationError
from django.utils.crypto import get_random_string

from traffic_control.models.common import DeviceTypeTargetModel
from traffic_control.tests.factories import (
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
    ),
)
@pytest.mark.django_db
def test__traffic_control_device_type__target_model__restricts_relations(
    allowed_value, factory
):
    related_obj = factory()

    for choice in DeviceTypeTargetModel:
        device_type = get_traffic_control_device_type(
            code=get_random_string(), target_model=choice
        )

        if choice == allowed_value:
            related_obj.device_type = device_type
            related_obj.save(update_fields=["device_type"])
            related_obj.refresh_from_db()
            assert related_obj.device_type == device_type
        else:
            with pytest.raises(ValidationError):
                related_obj.device_type = device_type
                related_obj.save(update_fields=["device_type"])


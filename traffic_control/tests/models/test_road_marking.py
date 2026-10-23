import pytest
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError

from traffic_control.enums import DeviceTypeTargetModel, TrafficControlDeviceTypeType
from traffic_control.models import RoadMarkingPlan, RoadMarkingReal
from traffic_control.models.common import TrafficControlDeviceType
from traffic_control.tests.factories import get_owner, get_user


@pytest.mark.django_db
@pytest.mark.parametrize("model_class", [RoadMarkingPlan, RoadMarkingReal])
def test_save_traverse_road_marking_without_road_name_raise_validation_error(model_class, settings):
    device_type = TrafficControlDeviceType.objects.create(
        code="L11",
        target_model=DeviceTypeTargetModel.ROAD_MARKING,
        type=TrafficControlDeviceTypeType.TRANSVERSE,
    )
    user = get_user("test_user")
    with pytest.raises(ValidationError) as e:
        model_class.objects.create(
            device_type=device_type,
            location=Point(1, 1, 0, srid=settings.SRID),
            road_name="",
            owner=get_owner(),
            created_by=user,
            updated_by=user,
        )
        assert str(e) == f'Road name is required for "{TrafficControlDeviceTypeType.TRANSVERSE.value}" road marking'

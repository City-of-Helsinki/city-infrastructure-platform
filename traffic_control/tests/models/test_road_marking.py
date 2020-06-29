from datetime import date

from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.test import TestCase

from traffic_control.models import RoadMarkingPlan, RoadMarkingReal
from traffic_control.models.common import (
    DeviceTypeTargetModel,
    TrafficControlDeviceType,
    TrafficControlDeviceTypeType,
)
from traffic_control.tests.factories import get_user


class RoadMarkingPlanTestCase(TestCase):
    def test_save_traverse_road_marking_without_road_name_raise_validation_error(self):
        device_type = TrafficControlDeviceType.objects.create(
            code="L11",
            target_model=DeviceTypeTargetModel.ROAD_MARKING,
            type=TrafficControlDeviceTypeType.TRANSVERSE,
        )
        user = get_user("test_user")
        with self.assertRaises(ValidationError) as e:
            RoadMarkingPlan.objects.create(
                device_type=device_type,
                location=Point(1, 1, srid=settings.SRID),
                road_name="",
                decision_date=date(2020, 6, 29),
                created_by=user,
                updated_by=user,
            )
            self.assertEqual(
                str(e),
                f'Road name is required for "{TrafficControlDeviceTypeType.TRANSVERSE.value}" road marking',
            )


class RoadMarkingRealTestCase(TestCase):
    def test_save_traverse_road_marking_without_road_name_raise_validation_error(self):
        device_type = TrafficControlDeviceType.objects.create(
            code="L11",
            target_model=DeviceTypeTargetModel.ROAD_MARKING,
            type=TrafficControlDeviceTypeType.TRANSVERSE,
        )
        user = get_user("test_user")
        with self.assertRaises(ValidationError) as e:
            RoadMarkingReal.objects.create(
                device_type=device_type,
                location=Point(1, 1, srid=settings.SRID),
                road_name="",
                created_by=user,
                updated_by=user,
            )
            self.assertEqual(
                str(e),
                f'Road name is required for "{TrafficControlDeviceTypeType.TRANSVERSE.value}" road marking',
            )

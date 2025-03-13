import pytest
from django.core.management import call_command

from traffic_control.models import ParkingZoneUpdateInfo
from traffic_control.tests.factories import AdditionalSignRealFactory, TrafficControlDeviceTypeFactory


@pytest.mark.parametrize("update", (True, False))
@pytest.mark.django_db
def test_parking_zone_update(update):
    dt = TrafficControlDeviceTypeFactory(code="H20.8", content_schema={"jotain": "jossain"})
    adsr1 = AdditionalSignRealFactory(
        device_type=dt, additional_information="text: A/B; numbercode:", content_s=None, missing_content=True
    )
    adsr2 = AdditionalSignRealFactory(
        device_type=dt, additional_information="text: A/B; numbercode:", content_s={"test": "me"}, missing_content=False
    )

    call_command("parking_zone_update", update=update)
    adsr1.refresh_from_db()
    adsr2.refresh_from_db()

    assert ParkingZoneUpdateInfo.objects.count() == 1
    parking_zone_info = ParkingZoneUpdateInfo.objects.first()
    assert len(parking_zone_info.update_infos) == 2
    assert parking_zone_info.database_update == update

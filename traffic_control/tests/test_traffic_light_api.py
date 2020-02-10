import datetime

import pytest
from django.urls import reverse
from rest_framework import status

from traffic_control.models import (
    MountType,
    TrafficLightPlan,
    TrafficLightReal,
    TrafficLightSoundBeaconValue,
    TrafficLightType,
)

from .factories import get_api_client, get_traffic_light_plan, get_traffic_light_real
from .test_base_api import point_location_test_data, TrafficControlAPIBaseTestCase


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,query_location,expected", point_location_test_data,
)
def test_filter_traffic_light_plans_location(location, query_location, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    get_traffic_light_plan(location)
    response = api_client.get(
        reverse("api:trafficlightplan-list"), {"location": query_location.ewkt}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == expected


class TrafficLightPlanTests(TrafficControlAPIBaseTestCase):
    def test_get_all_traffic_light_plans(self):
        """
        Ensure we can get all traffic light plan objects.
        """
        count = 3
        for i in range(count):
            self.__create_test_traffic_light_plan()
        response = self.client.get(reverse("api:trafficlightplan-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

    def test_get_traffic_light_detail(self):
        """
        Ensure we can get one traffic light plan object.
        """
        traffic_light = self.__create_test_traffic_light_plan()
        response = self.client.get(
            reverse("api:trafficlightplan-detail", kwargs={"pk": traffic_light.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(traffic_light.id))

    def test_create_traffic_light_plan(self):
        """
        Ensure we can create a new traffic light plan object.
        """
        data = {
            "code": self.test_code.id,
            "type": TrafficLightType.TRAFFIC_LIGHT.value,
            "location": self.test_point.ewkt,
            "decision_date": "2020-01-02",
            "lifecycle": self.test_lifecycle.value,
            "owner": self.test_owner,
        }
        response = self.client.post(
            reverse("api:trafficlightplan-list"), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TrafficLightPlan.objects.count(), 1)
        traffic_light = TrafficLightPlan.objects.first()
        self.assertEqual(traffic_light.code.id, data["code"])
        self.assertEqual(traffic_light.type.value, data["type"])
        self.assertEqual(traffic_light.location.ewkt, data["location"])
        self.assertEqual(
            traffic_light.decision_date.strftime("%Y-%m-%d"), data["decision_date"]
        )
        self.assertEqual(traffic_light.lifecycle.value, data["lifecycle"])

    def test_update_traffic_light_plan(self):
        """
        Ensure we can update existing traffic light plan object.
        """
        traffic_light = self.__create_test_traffic_light_plan()
        data = {
            "code": self.test_code.id,
            "type": TrafficLightType.BUTTON.value,
            "location": self.test_point.ewkt,
            "decision_date": "2020-01-02",
            "lifecycle": self.test_lifecycle_2.value,
            "owner": self.test_owner,
        }
        response = self.client.put(
            reverse("api:trafficlightplan-detail", kwargs={"pk": traffic_light.id}),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TrafficLightPlan.objects.count(), 1)
        traffic_light = TrafficLightPlan.objects.first()
        self.assertEqual(traffic_light.code.id, data["code"])
        self.assertEqual(traffic_light.type.value, data["type"])
        self.assertEqual(traffic_light.location.ewkt, data["location"])
        self.assertEqual(
            traffic_light.decision_date.strftime("%Y-%m-%d"), data["decision_date"]
        )
        self.assertEqual(traffic_light.lifecycle.value, data["lifecycle"])

    def test_delete_traffic_light_plan_detail(self):
        """
        Ensure we can soft-delete one traffic light plan object.
        """
        traffic_light = self.__create_test_traffic_light_plan()
        response = self.client.delete(
            reverse("api:trafficlightplan-detail", kwargs={"pk": traffic_light.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TrafficLightPlan.objects.count(), 1)
        deleted_traffic_light = TrafficLightPlan.objects.get(id=str(traffic_light.id))
        self.assertEqual(deleted_traffic_light.id, traffic_light.id)
        self.assertEqual(deleted_traffic_light.deleted_by, self.user)
        self.assertTrue(deleted_traffic_light.deleted_at)

    def __create_test_traffic_light_plan(self):
        return TrafficLightPlan.objects.create(
            code=self.test_code,
            location=self.test_point,
            type=TrafficLightType.TRAFFIC_LIGHT,
            decision_date=datetime.datetime.strptime("01012020", "%d%m%Y").date(),
            lifecycle=self.test_lifecycle,
            mount_type=MountType.POST,
            road_name="Testingroad",
            sound_beacon=TrafficLightSoundBeaconValue.YES,
            created_by=self.user,
            updated_by=self.user,
        )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,query_location,expected", point_location_test_data,
)
def test_filter_traffic_light_reals_location(location, query_location, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    get_traffic_light_real(location)
    response = api_client.get(
        reverse("api:trafficlightreal-list"), {"location": query_location.ewkt}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == expected


class TrafficLightRealTests(TrafficControlAPIBaseTestCase):
    def test_get_all_traffic_light_reals(self):
        """
        Ensure we can get all real traffic light objects.
        """
        count = 3
        for i in range(count):
            self.__create_test_traffic_light_real()
        response = self.client.get(reverse("api:trafficlightreal-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

    def test_get_traffic_light_real_detail(self):
        """
        Ensure we can get one real traffic light object.
        """
        traffic_light_real = self.__create_test_traffic_light_real()
        response = self.client.get(
            reverse("api:trafficlightreal-detail", kwargs={"pk": traffic_light_real.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(traffic_light_real.id))

    def test_create_traffic_light_real(self):
        """
        Ensure we can create a new real traffic light object.
        """
        data = {
            "code": self.test_code.id,
            "type": TrafficLightType.TRAFFIC_LIGHT.value,
            "location": self.test_point.ewkt,
            "installation_date": "2020-01-02",
            "lifecycle": self.test_lifecycle.value,
            "owner": self.test_owner,
        }
        response = self.client.post(
            reverse("api:trafficlightreal-list"), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TrafficLightReal.objects.count(), 1)
        traffic_light_real = TrafficLightReal.objects.first()
        self.assertEqual(traffic_light_real.code.id, data["code"])
        self.assertEqual(traffic_light_real.type.value, data["type"])
        self.assertEqual(traffic_light_real.location.ewkt, data["location"])
        self.assertEqual(
            traffic_light_real.installation_date.strftime("%Y-%m-%d"),
            data["installation_date"],
        )
        self.assertEqual(traffic_light_real.lifecycle.value, data["lifecycle"])

    def test_update_traffic_light_real(self):
        """
        Ensure we can update existing real traffic light object.
        """
        traffic_light_real = self.__create_test_traffic_light_real()
        data = {
            "code": self.test_code_2.id,
            "type": TrafficLightType.SOUND_BEACON.value,
            "location": self.test_point.ewkt,
            "installation_date": "2020-01-21",
            "lifecycle": self.test_lifecycle_2.value,
            "owner": self.test_owner,
        }
        response = self.client.put(
            reverse(
                "api:trafficlightreal-detail", kwargs={"pk": traffic_light_real.id}
            ),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TrafficLightReal.objects.count(), 1)
        traffic_light_real = TrafficLightReal.objects.first()
        self.assertEqual(traffic_light_real.code.id, data["code"])
        self.assertEqual(traffic_light_real.type.value, data["type"])
        self.assertEqual(traffic_light_real.location.ewkt, data["location"])
        self.assertEqual(
            traffic_light_real.installation_date.strftime("%Y-%m-%d"),
            data["installation_date"],
        )
        self.assertEqual(traffic_light_real.lifecycle.value, data["lifecycle"])

    def test_delete_traffic_light_real_detail(self):
        """
        Ensure we can soft-delete one real traffic light object.
        """
        traffic_light_real = self.__create_test_traffic_light_real()
        response = self.client.delete(
            reverse(
                "api:trafficlightreal-detail", kwargs={"pk": traffic_light_real.id}
            ),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TrafficLightReal.objects.count(), 1)
        deleted_traffic_light_real = TrafficLightReal.objects.get(
            id=str(traffic_light_real.id)
        )
        self.assertEqual(deleted_traffic_light_real.id, traffic_light_real.id)
        self.assertEqual(deleted_traffic_light_real.deleted_by, self.user)
        self.assertTrue(deleted_traffic_light_real.deleted_at)

    def __create_test_traffic_light_real(self):
        traffic_light_plan = TrafficLightPlan.objects.create(
            code=self.test_code,
            location=self.test_point,
            type=TrafficLightType.TRAFFIC_LIGHT,
            decision_date=datetime.datetime.strptime("01012020", "%d%m%Y").date(),
            lifecycle=self.test_lifecycle,
            mount_type=MountType.POST,
            road_name="Testingroad",
            sound_beacon=TrafficLightSoundBeaconValue.YES,
            created_by=self.user,
            updated_by=self.user,
        )

        return TrafficLightReal.objects.create(
            code=self.test_code,
            traffic_light_plan=traffic_light_plan,
            location=self.test_point,
            type=TrafficLightType.TRAFFIC_LIGHT,
            installation_date=datetime.datetime.strptime("01012020", "%d%m%Y").date(),
            lifecycle=self.test_lifecycle,
            mount_type=MountType.POST,
            road_name="Testingroad",
            sound_beacon=TrafficLightSoundBeaconValue.YES,
            created_by=self.user,
            updated_by=self.user,
        )

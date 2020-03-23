import datetime
import io

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework_gis.fields import GeoJsonDict

from traffic_control.models import (
    MountType,
    TrafficLightPlan,
    TrafficLightReal,
    TrafficLightSoundBeaconValue,
    TrafficLightType,
)

from .factories import get_api_client, get_traffic_light_plan, get_traffic_light_real
from .test_base_api import (
    point_location_error_test_data,
    point_location_test_data,
    TrafficControlAPIBaseTestCase,
)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected", point_location_test_data,
)
def test_filter_traffic_light_plans_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    traffic_light_plan = get_traffic_light_plan(location)
    response = api_client.get(
        reverse("api:trafficlightplan-list"), {"location": location_query.ewkt}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == expected

    if expected == 1:
        data = response.data.get("results")[0]
        assert str(traffic_light_plan.id) == data.get("id")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected", point_location_error_test_data,
)
def test_filter_error_traffic_light_plans_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    get_traffic_light_plan(location)
    response = api_client.get(
        reverse("api:trafficlightplan-list"), {"location": location_query}
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data.get("location")[0] == expected


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

        results = response.data.get("results")
        for result in results:
            traffic_light_plan = TrafficLightPlan.objects.get(id=result.get("id"))
            self.assertEqual(result.get("location"), traffic_light_plan.location.ewkt)

    def test_get_all_traffic_light_plans__geojson(self):
        """
        Ensure we can get all traffic light plan objects with GeoJSON location.
        """
        count = 3
        for i in range(count):
            self.__create_test_traffic_light_plan()
        response = self.client.get(
            reverse("api:trafficlightplan-list"), data={"geo_format": "geojson"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

        results = response.data.get("results")
        for result in results:
            traffic_light_plan = TrafficLightPlan.objects.get(id=result.get("id"))
            self.assertEqual(
                result.get("location"), GeoJsonDict(traffic_light_plan.location.json)
            )

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
        self.assertEqual(traffic_light.location.ewkt, response.data.get("location"))

    def test_get_traffic_light_detail__geojson(self):
        """
        Ensure we can get one traffic light plan object with GeoJSON location.
        """
        traffic_light = self.__create_test_traffic_light_plan()
        response = self.client.get(
            reverse("api:trafficlightplan-detail", kwargs={"pk": traffic_light.id}),
            data={"geo_format": "geojson"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(traffic_light.id))
        traffic_light_geojson = GeoJsonDict(traffic_light.location.json)
        self.assertEqual(traffic_light_geojson, response.data.get("location"))

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
        self.assertEqual(response.data.get("location"), data["location"])
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

    def test_traffic_light_plan_files(self):
        """
        Ensure that traffic light plan document can be uploaded, rewritten and deleted.
        """
        traffic_light_plan = self.__create_test_traffic_light_plan()

        # Upload
        data = {"file": io.BytesIO(b"File contents")}

        post_response = self.client.post(
            reverse(
                "api:trafficlightplan-post-file", kwargs={"pk": traffic_light_plan.id}
            ),
            data=data,
            format="multipart",
        )

        self.assertEqual(post_response.status_code, status.HTTP_200_OK)
        self.assertEqual(TrafficLightPlan.objects.count(), 1)
        changed_traffic_light_plan = TrafficLightPlan.objects.get(
            id=str(traffic_light_plan.id)
        )
        self.assertEqual(changed_traffic_light_plan.files.count(), 1)

        # Rewrite
        data = {"file": io.BytesIO(b"Rewritten file contents")}

        patch_response = self.client.patch(
            reverse(
                "api:trafficlightplan-change-file",
                kwargs={
                    "pk": traffic_light_plan.id,
                    "file_pk": changed_traffic_light_plan.files.first().id,
                },
            ),
            data=data,
            format="multipart",
        )

        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(TrafficLightPlan.objects.count(), 1)
        rewritten_traffic_light_plan = TrafficLightPlan.objects.get(
            id=str(traffic_light_plan.id)
        )
        self.assertEqual(rewritten_traffic_light_plan.files.count(), 1)
        self.assertNotEqual(
            post_response.data.get("file"), patch_response.data.get("file")
        )

        # Delete
        delete_response = self.client.delete(
            reverse(
                "api:trafficlightplan-change-file",
                kwargs={
                    "pk": traffic_light_plan.id,
                    "file_pk": changed_traffic_light_plan.files.first().id,
                },
            ),
        )

        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TrafficLightPlan.objects.count(), 1)
        deleted_traffic_light_plan_file = TrafficLightPlan.objects.get(
            id=str(traffic_light_plan.id)
        )
        self.assertEqual(deleted_traffic_light_plan_file.files.count(), 0)

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
    "location,location_query,expected", point_location_test_data,
)
def test_filter_traffic_light_reals_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    traffic_light_real = get_traffic_light_real(location)
    response = api_client.get(
        reverse("api:trafficlightreal-list"), {"location": location_query.ewkt}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == expected

    if expected == 1:
        data = response.data.get("results")[0]
        assert str(traffic_light_real.id) == data.get("id")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected", point_location_error_test_data,
)
def test_filter_error_traffic_light_reals_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    get_traffic_light_real(location)
    response = api_client.get(
        reverse("api:trafficlightreal-list"), {"location": location_query}
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data.get("location")[0] == expected


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

        results = response.data.get("results")
        for result in results:
            traffic_light_real = TrafficLightReal.objects.get(id=result.get("id"))
            self.assertEqual(result.get("location"), traffic_light_real.location.ewkt)

    def test_get_all_traffic_light_reals__geojson(self):
        """
        Ensure we can get all real traffic light objects with GeoJSON location.
        """
        count = 3
        for i in range(count):
            self.__create_test_traffic_light_real()
        response = self.client.get(
            reverse("api:trafficlightreal-list"), data={"geo_format": "geojson"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

        results = response.data.get("results")
        for result in results:
            traffic_light_real = TrafficLightReal.objects.get(id=result.get("id"))
            self.assertEqual(
                result.get("location"), GeoJsonDict(traffic_light_real.location.json)
            )

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
        self.assertEqual(
            traffic_light_real.location.ewkt, response.data.get("location")
        )

    def test_get_traffic_light_real_detail__geojson(self):
        """
        Ensure we can get one real traffic light object with GeoJSON location.
        """
        traffic_light_real = self.__create_test_traffic_light_real()
        response = self.client.get(
            reverse(
                "api:trafficlightreal-detail", kwargs={"pk": traffic_light_real.id}
            ),
            data={"geo_format": "geojson"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(traffic_light_real.id))
        traffic_light_real_geojson = GeoJsonDict(traffic_light_real.location.json)
        self.assertEqual(traffic_light_real_geojson, response.data.get("location"))

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
        self.assertEqual(response.data.get("location"), data["location"])
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

import datetime

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework_gis.fields import GeoJsonDict

from traffic_control.models import MountPlan, MountReal

from .factories import get_api_client, get_mount_plan, get_mount_real
from .test_base_api import (
    line_location_error_test_data,
    line_location_test_data,
    point_location_error_test_data,
    point_location_test_data,
    TrafficControlAPIBaseTestCase,
)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    [*point_location_test_data, *line_location_test_data],
)
def test_filter_mount_plans_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    mount_plan = get_mount_plan(location)
    response = api_client.get(
        reverse("v1:mountplan-list"), {"location": location_query.ewkt}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == expected

    if expected == 1:
        data = response.data.get("results")[0]
        assert str(mount_plan.id) == data.get("id")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    [*point_location_error_test_data, *line_location_error_test_data],
)
def test_filter_error_mount_plans_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    get_mount_plan(location)
    response = api_client.get(
        reverse("v1:mountplan-list"), {"location": location_query}
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data.get("location")[0] == expected


class MountPlanTests(TrafficControlAPIBaseTestCase):
    def test_get_all_mount_plans(self):
        """
        Ensure we can get all mount plan objects.
        """
        count = 3
        for i in range(count):
            self.__create_test_mount_plan()
        response = self.client.get(reverse("v1:mountplan-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

        results = response.data.get("results")
        for result in results:
            mount_plan = MountPlan.objects.get(id=result.get("id"))
            self.assertEqual(result.get("location"), mount_plan.location.ewkt)

    def test_get_all_mount_plans__geojson(self):
        """
        Ensure we can get all mount plan objects with GeoJSON location.
        """
        count = 3
        for i in range(count):
            self.__create_test_mount_plan()
        response = self.client.get(
            reverse("v1:mountplan-list"), data={"geo_format": "geojson"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

        results = response.data.get("results")
        for result in results:
            mount_plan = MountPlan.objects.get(id=result.get("id"))
            self.assertEqual(
                result.get("location"), GeoJsonDict(mount_plan.location.json)
            )

    def test_get_mount_plan_detail(self):
        """
        Ensure we can get one mount plan object.
        """
        mount_plan = self.__create_test_mount_plan()
        response = self.client.get(
            reverse("v1:mountplan-detail", kwargs={"pk": mount_plan.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(mount_plan.id))
        self.assertEqual(mount_plan.location.ewkt, response.data.get("location"))

    def test_get_mount_plan_detail__geojson(self):
        """
        Ensure we can get one mount plan object with GeoJSON location.
        """
        mount_plan = self.__create_test_mount_plan()
        response = self.client.get(
            reverse("v1:mountplan-detail", kwargs={"pk": mount_plan.id}),
            data={"geo_format": "geojson"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(mount_plan.id))
        mount_plan_geojson = GeoJsonDict(mount_plan.location.json)
        self.assertEqual(mount_plan_geojson, response.data.get("location"))

    def test_create_mount_plan(self):
        """
        Ensure we can create a new mount plan object.
        """
        data = {
            "type": self.test_type.value,
            "location": self.test_point.ewkt,
            "decision_date": "2020-01-02",
            "lifecycle": self.test_lifecycle.value,
            "owner": self.test_owner,
        }
        response = self.client.post(reverse("v1:mountplan-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MountPlan.objects.count(), 1)
        self.assertEqual(response.data.get("location"), data["location"])
        mount_plan = MountPlan.objects.first()
        self.assertEqual(mount_plan.type.value, data["type"])
        self.assertEqual(mount_plan.location.ewkt, data["location"])
        self.assertEqual(
            mount_plan.decision_date.strftime("%Y-%m-%d"), data["decision_date"]
        )
        self.assertEqual(mount_plan.lifecycle.value, data["lifecycle"])

    def test_update_mount_plan(self):
        """
        Ensure we can update existing mount plan object.
        """
        mount_plan = self.__create_test_mount_plan()
        data = {
            "type": self.test_type_2.value,
            "location": self.test_point.ewkt,
            "decision_date": "2020-01-03",
            "lifecycle": self.test_lifecycle_2.value,
            "owner": self.test_owner,
        }
        response = self.client.put(
            reverse("v1:mountplan-detail", kwargs={"pk": mount_plan.id}),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(MountPlan.objects.count(), 1)
        mount_plan = MountPlan.objects.first()
        self.assertEqual(mount_plan.type.value, data["type"])
        self.assertEqual(mount_plan.location.ewkt, data["location"])
        self.assertEqual(
            mount_plan.decision_date.strftime("%Y-%m-%d"), data["decision_date"]
        )
        self.assertEqual(mount_plan.lifecycle.value, data["lifecycle"])

    def test_delete_mount_plan_detail(self):
        """
        Ensure we can soft-delete one mount plan object.
        """
        mount_plan = self.__create_test_mount_plan()
        response = self.client.delete(
            reverse("v1:mountplan-detail", kwargs={"pk": mount_plan.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(MountPlan.objects.count(), 1)
        deleted_mount_plan = MountPlan.objects.get(id=str(mount_plan.id))
        self.assertEqual(deleted_mount_plan.id, mount_plan.id)
        self.assertFalse(deleted_mount_plan.is_active)
        self.assertEqual(deleted_mount_plan.deleted_by, self.user)
        self.assertTrue(deleted_mount_plan.deleted_at)

    def test_get_deleted_mount_plan_returns_not_found(self):
        mount_plan = self.__create_test_mount_plan()
        response = self.client.delete(
            reverse("v1:mountplan-detail", kwargs={"pk": mount_plan.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get(
            reverse("v1:mountplan-detail", kwargs={"pk": mount_plan.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def __create_test_mount_plan(self):
        return MountPlan.objects.create(
            type=self.test_type,
            location=self.test_point,
            decision_date=datetime.datetime.strptime("01012020", "%d%m%Y").date(),
            lifecycle=self.test_lifecycle,
            created_by=self.user,
            updated_by=self.user,
        )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    [*point_location_test_data, *line_location_test_data],
)
def test_filter_mount_reals_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    mount_real = get_mount_real(location)
    response = api_client.get(
        reverse("v1:mountreal-list"), {"location": location_query.ewkt}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == expected

    if expected == 1:
        data = response.data.get("results")[0]
        assert str(mount_real.id) == data.get("id")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    [*point_location_error_test_data, *line_location_error_test_data],
)
def test_filter_error_mount_reals_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    get_mount_real(location)
    response = api_client.get(
        reverse("v1:mountreal-list"), {"location": location_query}
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data.get("location")[0] == expected


class MountRealTests(TrafficControlAPIBaseTestCase):
    def test_get_all_mount_reals(self):
        """
        Ensure we can get all mount real objects.
        """
        count = 3
        for i in range(count):
            self.__create_test_mount_real()
        response = self.client.get(reverse("v1:mountreal-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

        results = response.data.get("results")
        for result in results:
            mount_real = MountReal.objects.get(id=result.get("id"))
            self.assertEqual(result.get("location"), mount_real.location.ewkt)

    def test_get_all_mount_reals__geojson(self):
        """
        Ensure we can get all mount real objects with GeoJSON location.
        """
        count = 3
        for i in range(count):
            self.__create_test_mount_real()
        response = self.client.get(
            reverse("v1:mountreal-list"), data={"geo_format": "geojson"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

        results = response.data.get("results")
        for result in results:
            mount_real = MountReal.objects.get(id=result.get("id"))
            self.assertEqual(
                result.get("location"), GeoJsonDict(mount_real.location.json)
            )

    def test_get_mount_real_detail(self):
        """
        Ensure we can get one mount real object.
        """
        mount_real = self.__create_test_mount_real()
        response = self.client.get(
            reverse("v1:mountreal-detail", kwargs={"pk": mount_real.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(mount_real.id))

    def test_get_mount_real_detail__geojson(self):
        """
        Ensure we can get one mount real object.
        """
        mount_real = self.__create_test_mount_real()
        response = self.client.get(
            reverse("v1:mountreal-detail", kwargs={"pk": mount_real.id}),
            data={"geo_format": "geojson"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(mount_real.id))
        mount_real_geojson = GeoJsonDict(mount_real.location.json)
        self.assertEqual(mount_real_geojson, response.data.get("location"))

    def test_create_mount_plan(self):
        """
        Ensure we can create a new mount real object.
        """
        data = {
            "type": self.test_type.value,
            "location": self.test_point.ewkt,
            "installation_date": "2020-01-02",
            "lifecycle": self.test_lifecycle.value,
            "owner": self.test_owner,
        }
        response = self.client.post(reverse("v1:mountreal-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MountReal.objects.count(), 1)
        self.assertEqual(response.data.get("location"), data["location"])
        mount_real = MountReal.objects.first()
        self.assertEqual(mount_real.type.value, data["type"])
        self.assertEqual(mount_real.location.ewkt, data["location"])
        self.assertEqual(
            mount_real.installation_date.strftime("%Y-%m-%d"),
            data["installation_date"],
        )
        self.assertEqual(mount_real.lifecycle.value, data["lifecycle"])

    def test_update_mount_real(self):
        """
        Ensure we can update existing mount real object.
        """
        mount_real = self.__create_test_mount_real()
        data = {
            "type": self.test_type_2.value,
            "location": self.test_point.ewkt,
            "installation_date": "2020-01-03",
            "lifecycle": self.test_lifecycle_2.value,
            "owner": self.test_owner,
        }
        response = self.client.put(
            reverse("v1:mountreal-detail", kwargs={"pk": mount_real.id}),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(MountReal.objects.count(), 1)
        mount_real = MountReal.objects.first()
        self.assertEqual(mount_real.type.value, data["type"])
        self.assertEqual(mount_real.location.ewkt, data["location"])
        self.assertEqual(
            mount_real.installation_date.strftime("%Y-%m-%d"),
            data["installation_date"],
        )
        self.assertEqual(mount_real.lifecycle.value, data["lifecycle"])

    def test_delete_mount_real_detail(self):
        """
        Ensure we can soft-delete one mount real object.
        """
        mount_real = self.__create_test_mount_real()
        response = self.client.delete(
            reverse("v1:mountreal-detail", kwargs={"pk": mount_real.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(MountReal.objects.count(), 1)
        deleted_mount_real = MountReal.objects.get(id=str(mount_real.id))
        self.assertEqual(deleted_mount_real.id, mount_real.id)
        self.assertFalse(deleted_mount_real.is_active)
        self.assertEqual(deleted_mount_real.deleted_by, self.user)
        self.assertTrue(deleted_mount_real.deleted_at)

    def test_get_deleted_mount_real_returns_not_found(self):
        mount_real = self.__create_test_mount_real()
        response = self.client.delete(
            reverse("v1:mountreal-detail", kwargs={"pk": mount_real.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get(
            reverse("v1:mountreal-detail", kwargs={"pk": mount_real.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def __create_test_mount_real(self):
        mount_plan = MountPlan.objects.create(
            type=self.test_type,
            location=self.test_point,
            decision_date=datetime.datetime.strptime("01012020", "%d%m%Y").date(),
            lifecycle=self.test_lifecycle,
            created_by=self.user,
            updated_by=self.user,
        )
        return MountReal.objects.create(
            mount_plan=mount_plan,
            type=self.test_type,
            location=self.test_point,
            installation_date=datetime.datetime.strptime("01012020", "%d%m%Y").date(),
            lifecycle=self.test_lifecycle,
            created_by=self.user,
            updated_by=self.user,
        )

import datetime
import io

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework_gis.fields import GeoJsonDict

from traffic_control.models import TrafficSignPlan, TrafficSignReal

from .factories import get_api_client, get_traffic_sign_plan, get_traffic_sign_real
from .test_base_api import (
    point_location_error_test_data,
    point_location_test_data,
    TrafficControlAPIBaseTestCase,
)


@pytest.mark.django_db
@pytest.mark.parametrize("location,location_query,expected", point_location_test_data)
def test_filter_traffic_sign_plans_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    traffic_sign_plan = get_traffic_sign_plan(location)
    response = api_client.get(
        reverse("api:trafficsignplan-list"), {"location": location_query.ewkt}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == expected

    if expected == 1:
        data = response.data.get("results")[0]
        assert str(traffic_sign_plan.id) == data.get("id")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected", point_location_error_test_data,
)
def test_filter_error_traffic_sign_plans_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    get_traffic_sign_plan(location)
    response = api_client.get(
        reverse("api:trafficsignplan-list"), {"location": location_query}
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data.get("location")[0] == expected


class TrafficSignPlanTests(TrafficControlAPIBaseTestCase):
    def test_get_all_traffic_sign_plans(self):
        """
        Ensure we can get all traffic sign plan objects.
        """
        count = 3
        for i in range(count):
            self.__create_test_traffic_sign_plan()
        response = self.client.get(reverse("api:trafficsignplan-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

        results = response.data.get("results")
        for result in results:
            traffic_sign_plan = TrafficSignPlan.objects.get(id=result.get("id"))
            self.assertEqual(result.get("location"), traffic_sign_plan.location.ewkt)

    def test_get_all_traffic_sign_plans__geojson(self):
        """
        Ensure we can get all traffic sign plan objects with GeoJSON location.
        """
        count = 3
        for i in range(count):
            self.__create_test_traffic_sign_plan()
        response = self.client.get(
            reverse("api:trafficsignplan-list"), data={"geo_format": "geojson"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

        results = response.data.get("results")
        for result in results:
            traffic_sign_plan = TrafficSignPlan.objects.get(id=result.get("id"))
            self.assertEqual(
                result.get("location"), GeoJsonDict(traffic_sign_plan.location.json)
            )

    def test_get_traffic_sign_plan_detail(self):
        """
        Ensure we can get one traffic sign plan object.
        """
        traffic_sign_plan = self.__create_test_traffic_sign_plan()
        response = self.client.get(
            reverse("api:trafficsignplan-detail", kwargs={"pk": traffic_sign_plan.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(traffic_sign_plan.id))
        self.assertEqual(traffic_sign_plan.location.ewkt, response.data.get("location"))

    def test_get_traffic_sign_plan_detail__geojson(self):
        """
        Ensure we can get one traffic sign plan object with GeoJSON location.
        """
        traffic_sign_plan = self.__create_test_traffic_sign_plan()
        response = self.client.get(
            reverse("api:trafficsignplan-detail", kwargs={"pk": traffic_sign_plan.id}),
            data={"geo_format": "geojson"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(traffic_sign_plan.id))
        traffic_sign_plan_geojson = GeoJsonDict(traffic_sign_plan.location.json)
        self.assertEqual(traffic_sign_plan_geojson, response.data.get("location"))

    def test_create_traffic_sign_plan(self):
        """
        Ensure we can create a new traffic sign plan object.
        """
        data = {
            "code": self.test_code.id,
            "location": self.test_point.ewkt,
            "decision_date": "2020-01-02",
            "lifecycle": self.test_lifecycle.value,
            "owner": self.test_owner,
        }
        response = self.client.post(
            reverse("api:trafficsignplan-list"), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TrafficSignPlan.objects.count(), 1)
        self.assertEqual(response.data.get("location"), data["location"])
        traffic_sign_plan = TrafficSignPlan.objects.first()
        self.assertEqual(traffic_sign_plan.code.id, data["code"])
        self.assertEqual(traffic_sign_plan.location.ewkt, data["location"])
        self.assertEqual(
            traffic_sign_plan.decision_date.strftime("%Y-%m-%d"), data["decision_date"]
        )
        self.assertEqual(traffic_sign_plan.lifecycle.value, data["lifecycle"])

    def test_update_traffic_sign_plan(self):
        """
        Ensure we can update existing traffic sign plan object.
        """
        traffic_sign_plan = self.__create_test_traffic_sign_plan()
        data = {
            "code": self.test_code_2.id,
            "location": self.test_point.ewkt,
            "decision_date": "2020-01-03",
            "lifecycle": self.test_lifecycle_2.value,
            "owner": self.test_owner,
        }
        response = self.client.put(
            reverse("api:trafficsignplan-detail", kwargs={"pk": traffic_sign_plan.id}),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TrafficSignPlan.objects.count(), 1)
        traffic_sign_plan = TrafficSignPlan.objects.first()
        self.assertEqual(traffic_sign_plan.code.id, data["code"])
        self.assertEqual(traffic_sign_plan.location.ewkt, data["location"])
        self.assertEqual(
            traffic_sign_plan.decision_date.strftime("%Y-%m-%d"), data["decision_date"]
        )
        self.assertEqual(traffic_sign_plan.lifecycle.value, data["lifecycle"])

    def test_delete_traffic_sign_plan_detail(self):
        """
        Ensure we can soft-delete one traffic sign plan object.
        """
        traffic_sign_plan = self.__create_test_traffic_sign_plan()
        response = self.client.delete(
            reverse("api:trafficsignplan-detail", kwargs={"pk": traffic_sign_plan.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TrafficSignPlan.objects.count(), 1)
        deleted_traffic_sign_plan = TrafficSignPlan.objects.get(
            id=str(traffic_sign_plan.id)
        )
        self.assertEqual(deleted_traffic_sign_plan.id, traffic_sign_plan.id)
        self.assertEqual(deleted_traffic_sign_plan.deleted_by, self.user)
        self.assertTrue(deleted_traffic_sign_plan.deleted_at)

    def test_upload_traffic_sign_plan_document(self):
        """
        Ensure that traffic sign plan document can be uploaded to system.
        """
        traffic_sign_plan = self.__create_test_traffic_sign_plan()

        data = {"plan_document": io.BytesIO(b"File contents")}

        response = self.client.put(
            reverse(
                "api:trafficsignplan-upload-plan", kwargs={"pk": traffic_sign_plan.id}
            ),
            data=data,
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TrafficSignPlan.objects.count(), 1)
        changed_traffic_sign_plan = TrafficSignPlan.objects.get(
            id=str(traffic_sign_plan.id)
        )
        self.assertTrue(changed_traffic_sign_plan.plan_document)
        self.assertEqual(changed_traffic_sign_plan.updated_by, self.user)
        self.assertTrue(changed_traffic_sign_plan.updated_at)

    def __create_test_traffic_sign_plan(self):
        return TrafficSignPlan.objects.create(
            code=self.test_code,
            location=self.test_point,
            decision_date=datetime.datetime.strptime("01012020", "%d%m%Y").date(),
            lifecycle=self.test_lifecycle,
            created_by=self.user,
            updated_by=self.user,
        )


@pytest.mark.django_db
@pytest.mark.parametrize("location,location_query,expected", point_location_test_data)
def test_filter_traffic_sign_reals_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    traffic_sign_real = get_traffic_sign_real(location)
    response = api_client.get(
        reverse("api:trafficsignreal-list"), {"location": location_query.ewkt}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == expected

    if expected == 1:
        data = response.data.get("results")[0]
        assert str(traffic_sign_real.id) == data.get("id")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected", point_location_error_test_data,
)
def test_filter_error_traffic_sign_reals_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    get_traffic_sign_real(location)
    response = api_client.get(
        reverse("api:trafficsignreal-list"), {"location": location_query}
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data.get("location")[0] == expected


class TrafficSignRealTests(TrafficControlAPIBaseTestCase):
    def test_get_all_traffic_sign_reals(self):
        """
        Ensure we can get all traffic sign real objects.
        """
        count = 3
        for i in range(count):
            self.__create_test_traffic_sign_real()
        response = self.client.get(reverse("api:trafficsignreal-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

        results = response.data.get("results")
        for result in results:
            traffic_sign_real = TrafficSignReal.objects.get(id=result.get("id"))
            self.assertEqual(result.get("location"), traffic_sign_real.location.ewkt)

    def test_get_all_traffic_sign_reals__geojson(self):
        """
        Ensure we can get all traffic sign real objects with GeoJSON location.
        """
        count = 3
        for i in range(count):
            self.__create_test_traffic_sign_real()
        response = self.client.get(
            reverse("api:trafficsignreal-list"), data={"geo_format": "geojson"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

        results = response.data.get("results")
        for result in results:
            traffic_sign_real = TrafficSignReal.objects.get(id=result.get("id"))
            self.assertEqual(
                result.get("location"), GeoJsonDict(traffic_sign_real.location.json)
            )

    def test_get_traffic_sign_real_detail(self):
        """
        Ensure we can get one traffic sign real object.
        """
        traffic_sign_real = self.__create_test_traffic_sign_real()
        response = self.client.get(
            reverse("api:trafficsignreal-detail", kwargs={"pk": traffic_sign_real.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(traffic_sign_real.id))
        self.assertEqual(traffic_sign_real.location.ewkt, response.data.get("location"))

    def test_get_traffic_sign_real_detail__geojson(self):
        """
        Ensure we can get one traffic sign real object with GeoJSON location.
        """
        traffic_sign_real = self.__create_test_traffic_sign_real()
        response = self.client.get(
            reverse("api:trafficsignreal-detail", kwargs={"pk": traffic_sign_real.id}),
            data={"geo_format": "geojson"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(traffic_sign_real.id))
        traffic_sign_real_geojson = GeoJsonDict(traffic_sign_real.location.json)
        self.assertEqual(traffic_sign_real_geojson, response.data.get("location"))

    def test_create_traffic_sign_plan(self):
        """
        Ensure we can create a new traffic sign real object.
        """
        data = {
            "code": self.test_code.id,
            "location": self.test_point.ewkt,
            "installation_date": "2020-01-02",
            "lifecycle": self.test_lifecycle.value,
            "installation_id": 123,
            "allu_decision_id": 456,
            "owner": self.test_owner,
        }
        response = self.client.post(
            reverse("api:trafficsignreal-list"), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TrafficSignReal.objects.count(), 1)
        self.assertEqual(response.data.get("location"), data["location"])
        traffic_sign_real = TrafficSignReal.objects.first()
        self.assertEqual(traffic_sign_real.code.id, data["code"])
        self.assertEqual(traffic_sign_real.location.ewkt, data["location"])
        self.assertEqual(
            traffic_sign_real.installation_date.strftime("%Y-%m-%d"),
            data["installation_date"],
        )
        self.assertEqual(traffic_sign_real.lifecycle.value, data["lifecycle"])

    def test_update_traffic_sign_real(self):
        """
        Ensure we can update existing traffic sign real object.
        """
        traffic_sign_real = self.__create_test_traffic_sign_real()
        data = {
            "code": self.test_code_2.id,
            "location": self.test_point.ewkt,
            "installation_date": "2020-01-03",
            "lifecycle": self.test_lifecycle_2.value,
            "installation_id": 123,
            "allu_decision_id": 456,
            "owner": self.test_owner,
        }
        response = self.client.put(
            reverse("api:trafficsignreal-detail", kwargs={"pk": traffic_sign_real.id}),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TrafficSignReal.objects.count(), 1)
        traffic_sign_real = TrafficSignReal.objects.first()
        self.assertEqual(traffic_sign_real.code.id, data["code"])
        self.assertEqual(traffic_sign_real.location.ewkt, data["location"])
        self.assertEqual(
            traffic_sign_real.installation_date.strftime("%Y-%m-%d"),
            data["installation_date"],
        )
        self.assertEqual(traffic_sign_real.lifecycle.value, data["lifecycle"])

    def test_delete_traffic_sign_real_detail(self):
        """
        Ensure we can soft-delete one traffic sign real object.
        """
        traffic_sign_real = self.__create_test_traffic_sign_real()
        response = self.client.delete(
            reverse("api:trafficsignreal-detail", kwargs={"pk": traffic_sign_real.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TrafficSignReal.objects.count(), 1)
        deleted_traffic_sign_real = TrafficSignReal.objects.get(
            id=str(traffic_sign_real.id)
        )
        self.assertEqual(deleted_traffic_sign_real.id, traffic_sign_real.id)
        self.assertEqual(deleted_traffic_sign_real.deleted_by, self.user)
        self.assertTrue(deleted_traffic_sign_real.deleted_at)

    def __create_test_traffic_sign_real(self):
        traffic_sign_plan = TrafficSignPlan.objects.create(
            code=self.test_code,
            location=self.test_point,
            decision_date=datetime.datetime.strptime("01012020", "%d%m%Y").date(),
            lifecycle=self.test_lifecycle,
            created_by=self.user,
            updated_by=self.user,
        )
        return TrafficSignReal.objects.create(
            traffic_sign_plan=traffic_sign_plan,
            code=self.test_code,
            location=self.test_point,
            installation_date=datetime.datetime.strptime("01012020", "%d%m%Y").date(),
            lifecycle=self.test_lifecycle,
            created_by=self.user,
            updated_by=self.user,
        )

import datetime

import pytest
from django.urls import reverse
from rest_framework import status

from traffic_control.models import TrafficSignPlan, TrafficSignReal

from .factories import get_api_client, get_traffic_sign
from .test_base_api import point_location_test_data, TrafficControlAPIBaseTestCase


@pytest.mark.django_db
@pytest.mark.parametrize(
    "sign_location,query_location,expected", point_location_test_data
)
def test_filter_traffic_sign_plans_location(sign_location, query_location, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    get_traffic_sign(sign_location)
    response = api_client.get(
        reverse("api:trafficsignplan-list"), {"location": query_location.ewkt}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == expected


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

    def __create_test_traffic_sign_plan(self):
        return TrafficSignPlan.objects.create(
            code=self.test_code,
            location=self.test_point,
            decision_date=datetime.datetime.strptime("01012020", "%d%m%Y").date(),
            lifecycle=self.test_lifecycle,
            created_by=self.user,
            updated_by=self.user,
        )


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

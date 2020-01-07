import datetime

from django.conf import settings
from django.contrib.gis.geos import Point
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from traffic_control.models import Lifecycle, TrafficSignCode, TrafficSignPlan
from users.models import User


class TrafficSignPlanTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpw")
        self.client.login(username="testuser", password="testpw")
        self.test_lifecycle = Lifecycle.objects.create(
            status="ACTIVE", description="Active"
        )
        self.test_lifecycle_2 = Lifecycle.objects.create(
            status="INACTIVE", description="Inactive"
        )
        self.test_code = TrafficSignCode.objects.create(
            code="A11", description="Speed limit"
        )
        self.test_code_2 = TrafficSignCode.objects.create(
            code="A12", description="Weight limit"
        )
        self.test_point = Point(
            25496366.48055263, 6675573.680776692, srid=settings.SRID
        )

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
            "%s%s/" % (reverse("api:trafficsignplan-list"), str(traffic_sign_plan.id))
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(traffic_sign_plan.id))

    def test_create_traffic_sign_plan(self):
        """
        Ensure we can create a new traffic sign plan object.
        """
        data = {
            "code": self.test_code.id,
            "location_xy": self.test_point.ewkt,
            "decision_date": "2020-01-02",
            "lifecycle": self.test_lifecycle.id,
        }
        response = self.client.post(
            reverse("api:trafficsignplan-list"), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TrafficSignPlan.objects.count(), 1)
        traffic_sign_plan = TrafficSignPlan.objects.first()
        self.assertEqual(traffic_sign_plan.code.id, data["code"])
        self.assertEqual(traffic_sign_plan.location_xy.ewkt, data["location_xy"])
        self.assertEqual(
            traffic_sign_plan.decision_date.strftime("%Y-%m-%d"), data["decision_date"]
        )
        self.assertEqual(traffic_sign_plan.lifecycle.id, data["lifecycle"])

    def test_update_traffic_sign_plan(self):
        """
        Ensure we can update existing traffic sign plan object.
        """
        traffic_sign_plan = self.__create_test_traffic_sign_plan()
        data = {
            "code": self.test_code_2.id,
            "location_xy": self.test_point.ewkt,
            "decision_date": "2020-01-03",
            "lifecycle": self.test_lifecycle_2.id,
        }
        response = self.client.put(
            "%s%s/" % (reverse("api:trafficsignplan-list"), str(traffic_sign_plan.id)),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TrafficSignPlan.objects.count(), 1)
        traffic_sign_plan = TrafficSignPlan.objects.first()
        self.assertEqual(traffic_sign_plan.code.id, data["code"])
        self.assertEqual(traffic_sign_plan.location_xy.ewkt, data["location_xy"])
        self.assertEqual(
            traffic_sign_plan.decision_date.strftime("%Y-%m-%d"), data["decision_date"]
        )
        self.assertEqual(traffic_sign_plan.lifecycle.id, data["lifecycle"])

    def test_delete_traffic_sign_plan_detail(self):
        """
        Ensure we can soft-delete one traffic sign plan object.
        """
        traffic_sign_plan = self.__create_test_traffic_sign_plan()
        response = self.client.delete(
            "%s%s/" % (reverse("api:trafficsignplan-list"), str(traffic_sign_plan.id))
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
            location_xy=self.test_point,
            decision_date=datetime.datetime.strptime("01012020", "%d%m%Y").date(),
            lifecycle=self.test_lifecycle,
            created_by=self.user,
            updated_by=self.user,
        )

import datetime

from django.contrib.gis.geos import Point
from django.urls import include, path, reverse
from rest_framework import status
from rest_framework.test import APITestCase, URLPatternsTestCase

from traffic_control.models import Lifecycle, TrafficSignCode, TrafficSignPlan
from users.models import User


class TrafficSignPlanTests(APITestCase, URLPatternsTestCase):
    urlpatterns = [
        path("", include("city-infrastructure-platform.urls")),
    ]

    def test_get_all_traffic_sign_plans(self):
        """
        Ensure we can get all traffic sign plan objects.
        """
        self.user = User.objects.create_user(username="testuser", password="12345")
        lifecycle = Lifecycle.objects.create(status="ACTIVE", description="Active")
        code = TrafficSignCode.objects.create(code="A11", description="Tietyo")
        TrafficSignPlan.objects.create(
            code=code,
            location_xy=Point(25496366.48055263, 6675573.680776692, srid=3879),
            decision_date=datetime.datetime.strptime("01012020", "%d%m%Y").date(),
            lifecycle=lifecycle,
            created_by=self.user,
            updated_by=self.user,
        )
        TrafficSignPlan.objects.create(
            code=code,
            location_xy=Point(25496367.48055263, 6675574.680776692, srid=3879),
            decision_date=datetime.datetime.strptime("02012020", "%d%m%Y").date(),
            lifecycle=lifecycle,
            created_by=self.user,
            updated_by=self.user,
        )
        url = reverse("api:trafficsignplan-list")
        self.client.login(username="testuser", password="12345")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), 2)

    def test_create_traffic_sign_plan(self):
        """
        Ensure we can create a new traffic sign plan object.
        """
        self.user = User.objects.create_user(username="testuser", password="12345")
        lifecycle = Lifecycle.objects.create(status="ACTIVE", description="Active")
        code = TrafficSignCode.objects.create(code="A11", description="Tietyo")
        url = reverse("api:trafficsignplan-list")
        data = {
            "code": code.id,
            "location_xy": "SRID=3879;POINT (25496366.48055263 6675573.680776692)",
            "decision_date": "2020-01-02",
            "lifecycle": lifecycle.id,
        }
        self.client.login(username="testuser", password="12345")
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TrafficSignPlan.objects.count(), 1)
        self.assertTrue(response.data.get("id"))
        self.assertEqual(response.data.get("code"), data["code"])
        self.assertEqual(response.data.get("location_xy"), data["location_xy"])
        self.assertEqual(response.data.get("decision_date"), data["decision_date"])
        self.assertEqual(response.data.get("lifecycle"), data["lifecycle"])

    def test_get_traffic_sign_plan_detail(self):
        """
        Ensure we can get one traffic sign plan object.
        """
        self.user = User.objects.create_user(username="testuser", password="12345")
        lifecycle = Lifecycle.objects.create(status="ACTIVE", description="Active")
        code = TrafficSignCode.objects.create(code="A11", description="Tietyo")
        trafficsignplan = TrafficSignPlan.objects.create(
            code=code,
            location_xy=Point(25496366.48055263, 6675573.680776692, srid=3879),
            decision_date=datetime.datetime.strptime("01012020", "%d%m%Y").date(),
            lifecycle=lifecycle,
            created_by=self.user,
            updated_by=self.user,
        )
        url = reverse("api:trafficsignplan-list") + str(trafficsignplan.id) + "/"
        self.client.login(username="testuser", password="12345")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(trafficsignplan.id))

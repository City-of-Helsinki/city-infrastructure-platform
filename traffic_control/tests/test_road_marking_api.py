import datetime

from django.urls import reverse
from rest_framework import status

from traffic_control.models import RoadMarkingColor, RoadMarkingPlan, RoadMarkingReal

from .test_base_api import TrafficControlAPIBaseTestCase


class RoadMarkingPlanTests(TrafficControlAPIBaseTestCase):
    def test_get_all_road_markings(self):
        """
        Ensure we can get all road marking plan objects.
        """
        count = 3
        for i in range(count):
            self.__create_test_road_marking_plan()
        response = self.client.get(reverse("api:roadmarkingplan-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

    def test_get_road_marking_detail(self):
        """
        Ensure we can get one road marking plan object.
        """
        road_marking = self.__create_test_road_marking_plan()
        response = self.client.get(
            reverse("api:roadmarkingplan-detail", kwargs={"pk": road_marking.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(road_marking.id))

    def test_create_road_marking(self):
        """
        Ensure we can create a new road marking plan object.
        """
        data = {
            "code": self.test_code.id,
            "location": self.test_point.ewkt,
            "decision_date": "2020-01-02",
            "lifecycle": self.test_lifecycle.value,
            "owner": self.test_owner,
        }
        response = self.client.post(
            reverse("api:roadmarkingplan-list"), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RoadMarkingPlan.objects.count(), 1)
        road_marking = RoadMarkingPlan.objects.first()
        self.assertEqual(road_marking.code.id, data["code"])
        self.assertEqual(road_marking.location.ewkt, data["location"])
        self.assertEqual(
            road_marking.decision_date.strftime("%Y-%m-%d"), data["decision_date"]
        )
        self.assertEqual(road_marking.lifecycle.value, data["lifecycle"])

    def test_update_road_marking(self):
        """
        Ensure we can update existing road marking plan object.
        """
        road_marking = self.__create_test_road_marking_plan()
        data = {
            "code": self.test_code_2.id,
            "location": self.test_point.ewkt,
            "decision_date": "2020-01-02",
            "lifecycle": self.test_lifecycle_2.value,
            "owner": self.test_owner,
        }
        response = self.client.put(
            reverse("api:roadmarkingplan-detail", kwargs={"pk": road_marking.id}),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(RoadMarkingPlan.objects.count(), 1)
        road_marking = RoadMarkingPlan.objects.first()
        self.assertEqual(road_marking.code.id, data["code"])
        self.assertEqual(road_marking.location.ewkt, data["location"])
        self.assertEqual(
            road_marking.decision_date.strftime("%Y-%m-%d"), data["decision_date"]
        )
        self.assertEqual(road_marking.lifecycle.value, data["lifecycle"])

    def test_delete_road_marking_detail(self):
        """
        Ensure we can soft-delete one road marking plan object.
        """
        road_marking = self.__create_test_road_marking_plan()
        response = self.client.delete(
            reverse("api:roadmarkingplan-detail", kwargs={"pk": road_marking.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(RoadMarkingPlan.objects.count(), 1)
        deleted_road_marking = RoadMarkingPlan.objects.get(id=str(road_marking.id))
        self.assertEqual(deleted_road_marking.id, road_marking.id)
        self.assertEqual(deleted_road_marking.deleted_by, self.user)
        self.assertTrue(deleted_road_marking.deleted_at)

    def __create_test_road_marking_plan(self):
        return RoadMarkingPlan.objects.create(
            code=self.test_code,
            value="30",
            color=RoadMarkingColor.WHITE,
            location=self.test_point,
            decision_date=datetime.datetime.strptime("01012020", "%d%m%Y").date(),
            lifecycle=self.test_lifecycle,
            material="Maali",
            is_grinded=True,
            is_raised=False,
            has_rumble_strips=True,
            road_name="Testingroad",
            created_by=self.user,
            updated_by=self.user,
        )


class RoadMarkingRealTests(TrafficControlAPIBaseTestCase):
    def test_get_all_road_marking_reals(self):
        """
        Ensure we can get all real road marking objects.
        """
        count = 3
        for i in range(count):
            self.__create_test_road_marking_real()
        response = self.client.get(reverse("api:roadmarkingreal-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

    def test_get_road_marking_real_detail(self):
        """
        Ensure we can get one real road marking object.
        """
        road_marking_real = self.__create_test_road_marking_real()
        response = self.client.get(
            reverse("api:roadmarkingreal-detail", kwargs={"pk": road_marking_real.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(road_marking_real.id))

    def test_create_road_marking_real(self):
        """
        Ensure we can create a new real road marking object.
        """
        data = {
            "code": self.test_code.id,
            "location": self.test_point.ewkt,
            "installation_date": "2020-01-02",
            "lifecycle": self.test_lifecycle.value,
            "owner": self.test_owner,
        }
        response = self.client.post(
            reverse("api:roadmarkingreal-list"), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RoadMarkingReal.objects.count(), 1)
        road_marking_real = RoadMarkingReal.objects.first()
        self.assertEqual(road_marking_real.code.id, data["code"])
        self.assertEqual(road_marking_real.location.ewkt, data["location"])
        self.assertEqual(
            road_marking_real.installation_date.strftime("%Y-%m-%d"),
            data["installation_date"],
        )
        self.assertEqual(road_marking_real.lifecycle.value, data["lifecycle"])

    def test_update_road_marking_real(self):
        """
        Ensure we can update existing real road marking object.
        """
        road_marking_real = self.__create_test_road_marking_real()
        data = {
            "code": self.test_code_2.id,
            "location": self.test_point.ewkt,
            "installation_date": "2020-01-21",
            "lifecycle": self.test_lifecycle_2.value,
            "owner": self.test_owner,
        }
        response = self.client.put(
            reverse("api:roadmarkingreal-detail", kwargs={"pk": road_marking_real.id}),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(RoadMarkingReal.objects.count(), 1)
        road_marking_real = RoadMarkingReal.objects.first()
        self.assertEqual(road_marking_real.code.id, data["code"])
        self.assertEqual(road_marking_real.location.ewkt, data["location"])
        self.assertEqual(
            road_marking_real.installation_date.strftime("%Y-%m-%d"),
            data["installation_date"],
        )
        self.assertEqual(road_marking_real.lifecycle.value, data["lifecycle"])

    def test_delete_road_marking_real_detail(self):
        """
        Ensure we can soft-delete one real road marking object.
        """
        road_marking_real = self.__create_test_road_marking_real()
        response = self.client.delete(
            reverse("api:roadmarkingreal-detail", kwargs={"pk": road_marking_real.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(RoadMarkingReal.objects.count(), 1)
        deleted_road_marking_real = RoadMarkingReal.objects.get(
            id=str(road_marking_real.id)
        )
        self.assertEqual(deleted_road_marking_real.id, road_marking_real.id)
        self.assertEqual(deleted_road_marking_real.deleted_by, self.user)
        self.assertTrue(deleted_road_marking_real.deleted_at)

    def __create_test_road_marking_real(self):
        road_marking_plan = RoadMarkingPlan.objects.create(
            code=self.test_code,
            value="30",
            color=RoadMarkingColor.WHITE,
            location=self.test_point,
            decision_date=datetime.datetime.strptime("01012020", "%d%m%Y").date(),
            lifecycle=self.test_lifecycle,
            material="Maali",
            is_grinded=True,
            is_raised=False,
            has_rumble_strips=True,
            road_name="Testingroad",
            created_by=self.user,
            updated_by=self.user,
        )

        return RoadMarkingReal.objects.create(
            code=self.test_code,
            road_marking_plan=road_marking_plan,
            value="30",
            color=RoadMarkingColor.WHITE,
            location=self.test_point,
            installation_date=datetime.datetime.strptime("01012020", "%d%m%Y").date(),
            lifecycle=self.test_lifecycle,
            material="Maali",
            is_grinded=True,
            is_raised=False,
            has_rumble_strips=True,
            road_name="Testingroad",
            created_by=self.user,
            updated_by=self.user,
        )

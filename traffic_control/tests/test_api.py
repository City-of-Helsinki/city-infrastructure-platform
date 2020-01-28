import datetime

from django.conf import settings
from django.contrib.gis.geos import Point
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from traffic_control.models import (
    BarrierPlan,
    BarrierReal,
    BarrierType,
    ConnectionType,
    Lifecycle,
    MountPlan,
    MountReal,
    MountType,
    Reflective,
    RoadMarkingColor,
    RoadMarkingPlan,
    RoadMarkingReal,
    SignpostPlan,
    SignpostReal,
    TrafficLightPlan,
    TrafficLightReal,
    TrafficLightSoundBeaconValue,
    TrafficLightType,
    TrafficSignCode,
    TrafficSignPlan,
    TrafficSignReal,
)
from users.models import User


class TrafficControlAPIBaseTestCase(APITestCase):
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
        self.test_type = MountType.PORTAL
        self.test_type_2 = MountType.WALL
        self.test_point = Point(
            25496366.48055263, 6675573.680776692, srid=settings.SRID
        )


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
            "lifecycle": self.test_lifecycle.id,
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
        self.assertEqual(traffic_light.lifecycle.id, data["lifecycle"])

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
            "lifecycle": self.test_lifecycle_2.id,
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
        self.assertEqual(traffic_light.lifecycle.id, data["lifecycle"])

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
            "lifecycle": self.test_lifecycle.id,
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
        self.assertEqual(traffic_light_real.lifecycle.id, data["lifecycle"])

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
            "lifecycle": self.test_lifecycle_2.id,
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
        self.assertEqual(traffic_light_real.lifecycle.id, data["lifecycle"])

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
            "lifecycle": self.test_lifecycle.id,
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
        self.assertEqual(road_marking.lifecycle.id, data["lifecycle"])

    def test_update_road_marking(self):
        """
        Ensure we can update existing road marking plan object.
        """
        road_marking = self.__create_test_road_marking_plan()
        data = {
            "code": self.test_code_2.id,
            "location": self.test_point.ewkt,
            "decision_date": "2020-01-02",
            "lifecycle": self.test_lifecycle_2.id,
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
        self.assertEqual(road_marking.lifecycle.id, data["lifecycle"])

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
            "lifecycle": self.test_lifecycle.id,
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
        self.assertEqual(road_marking_real.lifecycle.id, data["lifecycle"])

    def test_update_road_marking_real(self):
        """
        Ensure we can update existing real road marking object.
        """
        road_marking_real = self.__create_test_road_marking_real()
        data = {
            "code": self.test_code_2.id,
            "location": self.test_point.ewkt,
            "installation_date": "2020-01-21",
            "lifecycle": self.test_lifecycle_2.id,
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
        self.assertEqual(road_marking_real.lifecycle.id, data["lifecycle"])

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


class BarrierPlanTests(TrafficControlAPIBaseTestCase):
    def test_get_all_barrier_plans(self):
        """
        Ensure we can get all barrier plan objects.
        """
        count = 3
        for i in range(count):
            self.__create_test_barrier_plan()
        response = self.client.get(reverse("api:barrierplan-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

    def test_get_barrier_plan_detail(self):
        """
        Ensure we can get one barrier plan object.
        """
        barrier_plan = self.__create_test_barrier_plan()
        response = self.client.get(
            reverse("api:barrierplan-detail", kwargs={"pk": barrier_plan.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(barrier_plan.id))

    def test_create_barrier_plan(self):
        """
        Ensure we can create a new barrier plan object.
        """
        data = {
            "type": BarrierType.FENCE.value,
            "location": self.test_point.ewkt,
            "decision_date": "2020-01-02",
            "lifecycle": self.test_lifecycle.id,
        }
        response = self.client.post(
            reverse("api:barrierplan-list"), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BarrierPlan.objects.count(), 1)
        barrier_plan = BarrierPlan.objects.first()
        self.assertEqual(barrier_plan.type.value, data["type"])
        self.assertEqual(barrier_plan.location.ewkt, data["location"])
        self.assertEqual(
            barrier_plan.decision_date.strftime("%Y-%m-%d"), data["decision_date"]
        )
        self.assertEqual(barrier_plan.lifecycle.id, data["lifecycle"])

    def test_update_barrier_plan(self):
        """
        Ensure we can update existing barrier plan object.
        """
        barrier_plan = self.__create_test_barrier_plan()
        data = {
            "type": BarrierType.CONE.value,
            "location": self.test_point.ewkt,
            "decision_date": "2020-01-02",
            "lifecycle": self.test_lifecycle_2.id,
        }
        response = self.client.put(
            reverse("api:barrierplan-detail", kwargs={"pk": barrier_plan.id}),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(BarrierPlan.objects.count(), 1)
        barrier_plan = BarrierPlan.objects.first()
        self.assertEqual(barrier_plan.type.value, data["type"])
        self.assertEqual(barrier_plan.location.ewkt, data["location"])
        self.assertEqual(
            barrier_plan.decision_date.strftime("%Y-%m-%d"), data["decision_date"]
        )
        self.assertEqual(barrier_plan.lifecycle.id, data["lifecycle"])

    def test_delete_barrier_plan_detail(self):
        """
        Ensure we can soft-delete one barrier plan object.
        """
        barrier_plan = self.__create_test_barrier_plan()
        response = self.client.delete(
            reverse("api:barrierplan-detail", kwargs={"pk": barrier_plan.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(BarrierPlan.objects.count(), 1)
        deleted_barrier_plan = BarrierPlan.objects.get(id=str(barrier_plan.id))
        self.assertEqual(deleted_barrier_plan.id, barrier_plan.id)
        self.assertEqual(deleted_barrier_plan.deleted_by, self.user)
        self.assertTrue(deleted_barrier_plan.deleted_at)

    def __create_test_barrier_plan(self):
        return BarrierPlan.objects.create(
            type=BarrierType.BOOM,
            location=self.test_point,
            decision_date=datetime.datetime.strptime("01012020", "%d%m%Y").date(),
            lifecycle=self.test_lifecycle,
            material="Betoni",
            reflective=Reflective.YES,
            connection_type=ConnectionType.OPEN_OUT,
            road_name="Testingroad",
            created_by=self.user,
            updated_by=self.user,
        )


class BarrierRealTests(TrafficControlAPIBaseTestCase):
    def test_get_all_barrier_reals(self):
        """
        Ensure we can get all real barrier objects.
        """
        count = 3
        for i in range(count):
            self.__create_test_barrier_real()
        response = self.client.get(reverse("api:barrierreal-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

    def test_get_barrier_real_detail(self):
        """
        Ensure we can get one real barrier object.
        """
        barrier_real = self.__create_test_barrier_real()
        response = self.client.get(
            reverse("api:barrierreal-detail", kwargs={"pk": barrier_real.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(barrier_real.id))

    def test_create_barrier_real(self):
        """
        Ensure we can create a new real barrier object.
        """
        data = {
            "type": BarrierType.FENCE.value,
            "location": self.test_point.ewkt,
            "installation_date": "2020-01-02",
            "lifecycle": self.test_lifecycle.id,
        }
        response = self.client.post(
            reverse("api:barrierreal-list"), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BarrierReal.objects.count(), 1)
        barrier_real = BarrierReal.objects.first()
        self.assertEqual(barrier_real.type.value, data["type"])
        self.assertEqual(barrier_real.location.ewkt, data["location"])
        self.assertEqual(
            barrier_real.installation_date.strftime("%Y-%m-%d"),
            data["installation_date"],
        )
        self.assertEqual(barrier_real.lifecycle.id, data["lifecycle"])

    def test_update_barrier_real(self):
        """
        Ensure we can update existing real barrier object.
        """
        barrier_real = self.__create_test_barrier_real()
        data = {
            "type": BarrierType.CONE.value,
            "location": self.test_point.ewkt,
            "installation_date": "2020-01-21",
            "lifecycle": self.test_lifecycle_2.id,
        }
        response = self.client.put(
            reverse("api:barrierreal-detail", kwargs={"pk": barrier_real.id}),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(BarrierReal.objects.count(), 1)
        barrier_real = BarrierReal.objects.first()
        self.assertEqual(barrier_real.type.value, data["type"])
        self.assertEqual(barrier_real.location.ewkt, data["location"])
        self.assertEqual(
            barrier_real.installation_date.strftime("%Y-%m-%d"),
            data["installation_date"],
        )
        self.assertEqual(barrier_real.lifecycle.id, data["lifecycle"])

    def test_delete_barrier_real_detail(self):
        """
        Ensure we can soft-delete one real barrier object.
        """
        barrier_real = self.__create_test_barrier_real()
        response = self.client.delete(
            reverse("api:barrierreal-detail", kwargs={"pk": barrier_real.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(BarrierPlan.objects.count(), 1)
        deleted_barrier_real = BarrierReal.objects.get(id=str(barrier_real.id))
        self.assertEqual(deleted_barrier_real.id, barrier_real.id)
        self.assertEqual(deleted_barrier_real.deleted_by, self.user)
        self.assertTrue(deleted_barrier_real.deleted_at)

    def __create_test_barrier_real(self):
        barrier_plan = BarrierPlan.objects.create(
            type=BarrierType.BOOM,
            location=self.test_point,
            decision_date=datetime.datetime.strptime("01012020", "%d%m%Y").date(),
            lifecycle=self.test_lifecycle,
            material="Betoni",
            reflective=Reflective.YES,
            connection_type=ConnectionType.OPEN_OUT,
            road_name="Testingroad",
            created_by=self.user,
            updated_by=self.user,
        )

        return BarrierReal.objects.create(
            type=BarrierType.BOOM,
            barrier_plan=barrier_plan,
            location=self.test_point,
            installation_date=datetime.datetime.strptime("20012020", "%d%m%Y").date(),
            lifecycle=self.test_lifecycle,
            material="Betoni",
            reflective=Reflective.YES,
            connection_type=ConnectionType.OPEN_OUT,
            road_name="Testingroad",
            created_by=self.user,
            updated_by=self.user,
        )


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
            "location": self.test_point.ewkt,
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
        self.assertEqual(traffic_sign_plan.location.ewkt, data["location"])
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
            "location": self.test_point.ewkt,
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
        self.assertEqual(traffic_sign_plan.location.ewkt, data["location"])
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
            "%s%s/" % (reverse("api:trafficsignreal-list"), str(traffic_sign_real.id))
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
            "lifecycle": self.test_lifecycle.id,
            "installation_id": 123,
            "allu_decision_id": 456,
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
        self.assertEqual(traffic_sign_real.lifecycle.id, data["lifecycle"])

    def test_update_traffic_sign_real(self):
        """
        Ensure we can update existing traffic sign real object.
        """
        traffic_sign_real = self.__create_test_traffic_sign_real()
        data = {
            "code": self.test_code_2.id,
            "location": self.test_point.ewkt,
            "installation_date": "2020-01-03",
            "lifecycle": self.test_lifecycle_2.id,
            "installation_id": 123,
            "allu_decision_id": 456,
        }
        response = self.client.put(
            "%s%s/" % (reverse("api:trafficsignreal-list"), str(traffic_sign_real.id)),
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
        self.assertEqual(traffic_sign_real.lifecycle.id, data["lifecycle"])

    def test_delete_traffic_sign_real_detail(self):
        """
        Ensure we can soft-delete one traffic sign real object.
        """
        traffic_sign_real = self.__create_test_traffic_sign_real()
        response = self.client.delete(
            "%s%s/" % (reverse("api:trafficsignreal-list"), str(traffic_sign_real.id))
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


class MountPlanTests(TrafficControlAPIBaseTestCase):
    def test_get_all_mount_plans(self):
        """
        Ensure we can get all mount plan objects.
        """
        count = 3
        for i in range(count):
            self.__create_test_mount_plan()
        response = self.client.get(reverse("api:mountplan-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

    def test_get_mount_plan_detail(self):
        """
        Ensure we can get one mount plan object.
        """
        mount_plan = self.__create_test_mount_plan()
        response = self.client.get(
            "%s%s/" % (reverse("api:mountplan-list"), str(mount_plan.id))
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(mount_plan.id))

    def test_create_mount_plan(self):
        """
        Ensure we can create a new mount plan object.
        """
        data = {
            "type": self.test_type.value,
            "location": self.test_point.ewkt,
            "decision_date": "2020-01-02",
            "lifecycle": self.test_lifecycle.id,
        }
        response = self.client.post(reverse("api:mountplan-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MountPlan.objects.count(), 1)
        mount_plan = MountPlan.objects.first()
        self.assertEqual(mount_plan.type.value, data["type"])
        self.assertEqual(mount_plan.location.ewkt, data["location"])
        self.assertEqual(
            mount_plan.decision_date.strftime("%Y-%m-%d"), data["decision_date"]
        )
        self.assertEqual(mount_plan.lifecycle.id, data["lifecycle"])

    def test_update_mount_plan(self):
        """
        Ensure we can update existing mount plan object.
        """
        mount_plan = self.__create_test_mount_plan()
        data = {
            "type": self.test_type_2.value,
            "location": self.test_point.ewkt,
            "decision_date": "2020-01-03",
            "lifecycle": self.test_lifecycle_2.id,
        }
        response = self.client.put(
            "%s%s/" % (reverse("api:mountplan-list"), str(mount_plan.id)),
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
        self.assertEqual(mount_plan.lifecycle.id, data["lifecycle"])

    def test_delete_mount_plan_detail(self):
        """
        Ensure we can soft-delete one mount plan object.
        """
        mount_plan = self.__create_test_mount_plan()
        response = self.client.delete(
            "%s%s/" % (reverse("api:mountplan-list"), str(mount_plan.id))
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(MountPlan.objects.count(), 1)
        deleted_mount_plan = MountPlan.objects.get(id=str(mount_plan.id))
        self.assertEqual(deleted_mount_plan.id, mount_plan.id)
        self.assertEqual(deleted_mount_plan.deleted_by, self.user)
        self.assertTrue(deleted_mount_plan.deleted_at)

    def __create_test_mount_plan(self):
        return MountPlan.objects.create(
            type=self.test_type,
            location=self.test_point,
            decision_date=datetime.datetime.strptime("01012020", "%d%m%Y").date(),
            lifecycle=self.test_lifecycle,
            created_by=self.user,
            updated_by=self.user,
        )


class MountRealTests(TrafficControlAPIBaseTestCase):
    def test_get_all_mount_reals(self):
        """
        Ensure we can get all mount real objects.
        """
        count = 3
        for i in range(count):
            self.__create_test_mount_real()
        response = self.client.get(reverse("api:mountreal-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

    def test_get_mount_real_detail(self):
        """
        Ensure we can get one mount real object.
        """
        mount_real = self.__create_test_mount_real()
        response = self.client.get(
            "%s%s/" % (reverse("api:mountreal-list"), str(mount_real.id))
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(mount_real.id))

    def test_create_mount_plan(self):
        """
        Ensure we can create a new mount real object.
        """
        data = {
            "type": self.test_type.value,
            "location": self.test_point.ewkt,
            "installation_date": "2020-01-02",
            "lifecycle": self.test_lifecycle.id,
        }
        response = self.client.post(reverse("api:mountreal-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MountReal.objects.count(), 1)
        mount_real = MountReal.objects.first()
        self.assertEqual(mount_real.type.value, data["type"])
        self.assertEqual(mount_real.location.ewkt, data["location"])
        self.assertEqual(
            mount_real.installation_date.strftime("%Y-%m-%d"),
            data["installation_date"],
        )
        self.assertEqual(mount_real.lifecycle.id, data["lifecycle"])

    def test_update_mount_real(self):
        """
        Ensure we can update existing mount real object.
        """
        mount_real = self.__create_test_mount_real()
        data = {
            "type": self.test_type_2.value,
            "location": self.test_point.ewkt,
            "installation_date": "2020-01-03",
            "lifecycle": self.test_lifecycle_2.id,
        }
        response = self.client.put(
            "%s%s/" % (reverse("api:mountreal-list"), str(mount_real.id)),
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
        self.assertEqual(mount_real.lifecycle.id, data["lifecycle"])

    def test_delete_mount_real_detail(self):
        """
        Ensure we can soft-delete one mount real object.
        """
        mount_real = self.__create_test_mount_real()
        response = self.client.delete(
            "%s%s/" % (reverse("api:mountreal-list"), str(mount_real.id))
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(MountReal.objects.count(), 1)
        deleted_mount_real = MountReal.objects.get(id=str(mount_real.id))
        self.assertEqual(deleted_mount_real.id, mount_real.id)
        self.assertEqual(deleted_mount_real.deleted_by, self.user)
        self.assertTrue(deleted_mount_real.deleted_at)

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


class SignpostPlanTests(TrafficControlAPIBaseTestCase):
    def test_get_all_signpost_plans(self):
        """
        Ensure we can get all signpost plan objects.
        """
        count = 3
        for i in range(count):
            self.__create_test_signpost_plan()
        response = self.client.get(reverse("api:signpostplan-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

    def test_get_signpost_plan_detail(self):
        """
        Ensure we can get one signpost plan object.
        """
        signpost_plan = self.__create_test_signpost_plan()
        response = self.client.get(
            "%s%s/" % (reverse("api:signpostplan-list"), str(signpost_plan.id))
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(signpost_plan.id))

    def test_create_signpost_plan(self):
        """
        Ensure we can create a new signpost plan object.
        """
        data = {
            "code": self.test_code.id,
            "location": self.test_point.ewkt,
            "decision_date": "2020-01-02",
            "lifecycle": self.test_lifecycle.id,
        }
        response = self.client.post(
            reverse("api:signpostplan-list"), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SignpostPlan.objects.count(), 1)
        signpost_plan = SignpostPlan.objects.first()
        self.assertEqual(signpost_plan.code.id, data["code"])
        self.assertEqual(signpost_plan.location.ewkt, data["location"])
        self.assertEqual(
            signpost_plan.decision_date.strftime("%Y-%m-%d"), data["decision_date"]
        )
        self.assertEqual(signpost_plan.lifecycle.id, data["lifecycle"])

    def test_update_signpost_plan(self):
        """
        Ensure we can update existing signpost plan object.
        """
        signpost_plan = self.__create_test_signpost_plan()
        data = {
            "code": self.test_code_2.id,
            "location": self.test_point.ewkt,
            "decision_date": "2020-01-03",
            "lifecycle": self.test_lifecycle_2.id,
        }
        response = self.client.put(
            "%s%s/" % (reverse("api:signpostplan-list"), str(signpost_plan.id)),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(SignpostPlan.objects.count(), 1)
        signpost_plan = SignpostPlan.objects.first()
        self.assertEqual(signpost_plan.code.id, data["code"])
        self.assertEqual(signpost_plan.location.ewkt, data["location"])
        self.assertEqual(
            signpost_plan.decision_date.strftime("%Y-%m-%d"), data["decision_date"]
        )
        self.assertEqual(signpost_plan.lifecycle.id, data["lifecycle"])

    def test_delete_signpost_plan_detail(self):
        """
        Ensure we can soft-delete one signpost plan object.
        """
        signpost_plan = self.__create_test_signpost_plan()
        response = self.client.delete(
            "%s%s/" % (reverse("api:signpostplan-list"), str(signpost_plan.id))
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(SignpostPlan.objects.count(), 1)
        deleted_signpost_plan = SignpostPlan.objects.get(id=str(signpost_plan.id))
        self.assertEqual(deleted_signpost_plan.id, signpost_plan.id)
        self.assertEqual(deleted_signpost_plan.deleted_by, self.user)
        self.assertTrue(deleted_signpost_plan.deleted_at)

    def __create_test_signpost_plan(self):
        return SignpostPlan.objects.create(
            code=self.test_code,
            location=self.test_point,
            decision_date=datetime.datetime.strptime("01012020", "%d%m%Y").date(),
            lifecycle=self.test_lifecycle,
            created_by=self.user,
            updated_by=self.user,
        )


class SignPostRealTests(TrafficControlAPIBaseTestCase):
    def test_get_all_signpost_reals(self):
        """
        Ensure we can get all sign post real objects.
        """
        count = 3
        for i in range(count):
            self.__create_test_signpost_real()
        response = self.client.get(reverse("api:signpostreal-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

    def test_get_signpost_real_detail(self):
        """
        Ensure we can get one signpost real object.
        """
        signpost_real = self.__create_test_signpost_real()
        response = self.client.get(
            "%s%s/" % (reverse("api:signpostreal-list"), str(signpost_real.id))
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(signpost_real.id))

    def test_create_signpost_plan(self):
        """
        Ensure we can create a new signpost real object.
        """
        data = {
            "code": self.test_code.id,
            "location": self.test_point.ewkt,
            "installation_date": "2020-01-02",
            "lifecycle": self.test_lifecycle.id,
        }
        response = self.client.post(
            reverse("api:signpostreal-list"), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SignpostReal.objects.count(), 1)
        signpost_real = SignpostReal.objects.first()
        self.assertEqual(signpost_real.code.id, data["code"])
        self.assertEqual(signpost_real.location.ewkt, data["location"])
        self.assertEqual(
            signpost_real.installation_date.strftime("%Y-%m-%d"),
            data["installation_date"],
        )
        self.assertEqual(signpost_real.lifecycle.id, data["lifecycle"])

    def test_update_signpost_real(self):
        """
        Ensure we can update existing signpost real object.
        """
        signpost_real = self.__create_test_signpost_real()
        data = {
            "code": self.test_code_2.id,
            "location": self.test_point.ewkt,
            "installation_date": "2020-01-03",
            "lifecycle": self.test_lifecycle_2.id,
        }
        response = self.client.put(
            "%s%s/" % (reverse("api:signpostreal-list"), str(signpost_real.id)),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(SignpostReal.objects.count(), 1)
        signpost_real = SignpostReal.objects.first()
        self.assertEqual(signpost_real.code.id, data["code"])
        self.assertEqual(signpost_real.location.ewkt, data["location"])
        self.assertEqual(
            signpost_real.installation_date.strftime("%Y-%m-%d"),
            data["installation_date"],
        )
        self.assertEqual(signpost_real.lifecycle.id, data["lifecycle"])

    def test_delete_signpost_real_detail(self):
        """
        Ensure we can soft-delete one signpost real object.
        """
        signpost_real = self.__create_test_signpost_real()
        response = self.client.delete(
            "%s%s/" % (reverse("api:signpostreal-list"), str(signpost_real.id))
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(SignpostReal.objects.count(), 1)
        deleted_signpost_real = SignpostReal.objects.get(id=str(signpost_real.id))
        self.assertEqual(deleted_signpost_real.id, signpost_real.id)
        self.assertEqual(deleted_signpost_real.deleted_by, self.user)
        self.assertTrue(deleted_signpost_real.deleted_at)

    def __create_test_signpost_real(self):
        signpost_plan = SignpostPlan.objects.create(
            code=self.test_code,
            location=self.test_point,
            decision_date=datetime.datetime.strptime("01012020", "%d%m%Y").date(),
            lifecycle=self.test_lifecycle,
            created_by=self.user,
            updated_by=self.user,
        )
        return SignpostReal.objects.create(
            signpost_plan=signpost_plan,
            code=self.test_code,
            location=self.test_point,
            installation_date=datetime.datetime.strptime("01012020", "%d%m%Y").date(),
            lifecycle=self.test_lifecycle,
            created_by=self.user,
            updated_by=self.user,
        )

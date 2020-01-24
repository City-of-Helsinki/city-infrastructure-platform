import datetime

from django.conf import settings
from django.contrib.gis.geos import Point
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from traffic_control.models import (
    Lifecycle,
    MountPlan,
    MountReal,
    MountType,
    SignpostPlan,
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

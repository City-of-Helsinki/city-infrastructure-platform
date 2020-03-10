import datetime
import io

import pytest
from django.urls import reverse
from rest_framework import status

from traffic_control.models import BarrierPlan, BarrierReal, ConnectionType, Reflective

from .factories import get_api_client, get_barrier_plan, get_barrier_real
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
def test_filter_barrier_plans_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    barrier_plan = get_barrier_plan(location)
    response = api_client.get(
        reverse("api:barrierplan-list"), {"location": location_query.ewkt}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == expected
    if expected == 1:
        data = response.data.get("results")[0]
        assert str(barrier_plan.id) == data.get("id")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    [*point_location_error_test_data, *line_location_error_test_data],
)
def test_filter_error_barrier_plans_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    get_barrier_plan(location)
    response = api_client.get(
        reverse("api:barrierplan-list"), {"location": location_query}
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data.get("location")[0] == expected


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
            "type": self.test_code.id,
            "location": self.test_point.ewkt,
            "decision_date": "2020-01-02",
            "lifecycle": self.test_lifecycle.value,
            "owner": self.test_owner,
            "road_name": "Test street 1",
        }
        response = self.client.post(
            reverse("api:barrierplan-list"), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BarrierPlan.objects.count(), 1)
        barrier_plan = BarrierPlan.objects.first()
        self.assertEqual(barrier_plan.type.id, data["type"])
        self.assertEqual(barrier_plan.location.ewkt, data["location"])
        self.assertEqual(
            barrier_plan.decision_date.strftime("%Y-%m-%d"), data["decision_date"]
        )
        self.assertEqual(barrier_plan.lifecycle.value, data["lifecycle"])

    def test_update_barrier_plan(self):
        """
        Ensure we can update existing barrier plan object.
        """
        barrier_plan = self.__create_test_barrier_plan()
        data = {
            "type": self.test_code.id,
            "location": self.test_point.ewkt,
            "decision_date": "2020-01-02",
            "lifecycle": self.test_lifecycle_2.value,
            "owner": self.test_owner,
            "road_name": "Test street 1",
        }
        response = self.client.put(
            reverse("api:barrierplan-detail", kwargs={"pk": barrier_plan.id}),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(BarrierPlan.objects.count(), 1)
        barrier_plan = BarrierPlan.objects.first()
        self.assertEqual(barrier_plan.type.id, data["type"])
        self.assertEqual(barrier_plan.location.ewkt, data["location"])
        self.assertEqual(
            barrier_plan.decision_date.strftime("%Y-%m-%d"), data["decision_date"]
        )
        self.assertEqual(barrier_plan.lifecycle.value, data["lifecycle"])

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

    def test_upload_barrier_plan_document(self):
        """
        Ensure that barrier plan document can be uploaded to system.
        """
        barrier_plan = self.__create_test_barrier_plan()

        data = {"plan_document": io.BytesIO(b"File contents")}

        response = self.client.put(
            reverse("api:barrierplan-upload-plan", kwargs={"pk": barrier_plan.id}),
            data=data,
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(BarrierPlan.objects.count(), 1)
        changed_barrier_plan = BarrierPlan.objects.get(id=str(barrier_plan.id))
        self.assertTrue(changed_barrier_plan.plan_document)
        self.assertEqual(changed_barrier_plan.updated_by, self.user)
        self.assertTrue(changed_barrier_plan.updated_at)

    def __create_test_barrier_plan(self):
        return BarrierPlan.objects.create(
            type=self.test_code,
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


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    [*point_location_test_data, *line_location_test_data],
)
def test_filter_barrier_reals_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    barrier_real = get_barrier_real(location)
    response = api_client.get(
        reverse("api:barrierreal-list"), {"location": location_query.ewkt}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == expected

    if expected == 1:
        data = response.data.get("results")[0]
        assert str(barrier_real.id) == data.get("id")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    [*point_location_error_test_data, *line_location_error_test_data],
)
def test_filter_error_barrier_reals_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    get_barrier_plan(location)
    response = api_client.get(
        reverse("api:barrierreal-list"), {"location": location_query}
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data.get("location")[0] == expected


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
            "type": self.test_code.id,
            "location": self.test_point.ewkt,
            "installation_date": "2020-01-02",
            "lifecycle": self.test_lifecycle.value,
            "owner": self.test_owner,
            "road_name": "Test street 1",
        }
        response = self.client.post(
            reverse("api:barrierreal-list"), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BarrierReal.objects.count(), 1)
        barrier_real = BarrierReal.objects.first()
        self.assertEqual(barrier_real.type.id, data["type"])
        self.assertEqual(barrier_real.location.ewkt, data["location"])
        self.assertEqual(
            barrier_real.installation_date.strftime("%Y-%m-%d"),
            data["installation_date"],
        )
        self.assertEqual(barrier_real.lifecycle.value, data["lifecycle"])

    def test_update_barrier_real(self):
        """
        Ensure we can update existing real barrier object.
        """
        barrier_real = self.__create_test_barrier_real()
        data = {
            "type": self.test_code.id,
            "location": self.test_point.ewkt,
            "installation_date": "2020-01-21",
            "lifecycle": self.test_lifecycle_2.value,
            "owner": self.test_owner,
            "road_name": "Test street 1",
        }
        response = self.client.put(
            reverse("api:barrierreal-detail", kwargs={"pk": barrier_real.id}),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(BarrierReal.objects.count(), 1)
        barrier_real = BarrierReal.objects.first()
        self.assertEqual(barrier_real.type.id, data["type"])
        self.assertEqual(barrier_real.location.ewkt, data["location"])
        self.assertEqual(
            barrier_real.installation_date.strftime("%Y-%m-%d"),
            data["installation_date"],
        )
        self.assertEqual(barrier_real.lifecycle.value, data["lifecycle"])

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
            type=self.test_code,
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
            type=self.test_code,
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

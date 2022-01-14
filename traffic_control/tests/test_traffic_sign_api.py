import datetime
from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework_gis.fields import GeoJsonDict

from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.models import TrafficSignPlan, TrafficSignReal
from traffic_control.tests.factories import (
    add_traffic_sign_real_operation,
    get_api_client,
    get_traffic_control_device_type,
    get_traffic_sign_plan,
    get_traffic_sign_real,
    get_user,
)
from traffic_control.tests.test_base_api_3d import (
    point_location_error_test_data_3d,
    point_location_test_data_3d,
    TrafficControlAPIBaseTestCase3D,
)


@pytest.mark.django_db
@pytest.mark.parametrize("location,location_query,expected", point_location_test_data_3d)
def test_filter_traffic_sign_plans_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    traffic_sign_plan = get_traffic_sign_plan(location)
    response = api_client.get(reverse("v1:trafficsignplan-list"), {"location": location_query.ewkt})

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == expected

    if expected == 1:
        data = response.data.get("results")[0]
        assert str(traffic_sign_plan.id) == data.get("id")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    point_location_error_test_data_3d,
)
def test_filter_error_traffic_sign_plans_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    get_traffic_sign_plan(location)
    response = api_client.get(reverse("v1:trafficsignplan-list"), {"location": location_query})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data.get("location")[0] == expected


@pytest.mark.django_db
@pytest.mark.parametrize("target_model", (None, DeviceTypeTargetModel.TRAFFIC_SIGN))
def test__traffic_sign_plan__valid_device_type(target_model):
    """
    Ensure that device types with supported target_model value are allowed.
    """
    client = get_api_client(user=get_user(admin=True))
    traffic_sign_plan = get_traffic_sign_plan()
    device_type = get_traffic_control_device_type(
        code="123", description="test", target_model=target_model, value="12.5"
    )
    data = {"device_type": device_type.id}

    response = client.patch(
        reverse("v1:trafficsignplan-detail", kwargs={"pk": traffic_sign_plan.pk}),
        data,
        format="json",
    )

    traffic_sign_plan.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert traffic_sign_plan.device_type == device_type
    assert traffic_sign_plan.value == Decimal("12.5")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "target_model",
    (
        DeviceTypeTargetModel.BARRIER,
        DeviceTypeTargetModel.ROAD_MARKING,
        DeviceTypeTargetModel.SIGNPOST,
        DeviceTypeTargetModel.TRAFFIC_LIGHT,
    ),
)
def test__traffic_sign_plan__invalid_device_type(target_model):
    """
    Ensure that device types with unsupported target_model value are not allowed.
    """
    client = get_api_client(user=get_user(admin=True))
    traffic_sign_plan = get_traffic_sign_plan()
    device_type = get_traffic_control_device_type(code="123", description="test", target_model=target_model)
    data = {"device_type": device_type.id}

    response = client.patch(
        reverse("v1:trafficsignplan-detail", kwargs={"pk": traffic_sign_plan.pk}),
        data,
        format="json",
    )

    traffic_sign_plan.refresh_from_db()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert traffic_sign_plan.device_type != device_type


class TrafficSignPlanTests(TrafficControlAPIBaseTestCase3D):
    def test_get_all_traffic_sign_plans(self):
        """
        Ensure we can get all traffic sign plan objects.
        """
        count = 3
        for i in range(count):
            self.__create_test_traffic_sign_plan()
        response = self.client.get(reverse("v1:trafficsignplan-list"))
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
        response = self.client.get(reverse("v1:trafficsignplan-list"), data={"geo_format": "geojson"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

        results = response.data.get("results")
        for result in results:
            traffic_sign_plan = TrafficSignPlan.objects.get(id=result.get("id"))
            self.assertEqual(result.get("location"), GeoJsonDict(traffic_sign_plan.location.json))

    def test_get_traffic_sign_plan_detail(self):
        """
        Ensure we can get one traffic sign plan object.
        """
        traffic_sign_plan = self.__create_test_traffic_sign_plan()
        response = self.client.get(reverse("v1:trafficsignplan-detail", kwargs={"pk": traffic_sign_plan.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(traffic_sign_plan.id))
        self.assertEqual(traffic_sign_plan.location.ewkt, response.data.get("location"))

    def test_get_traffic_sign_plan_detail__geojson(self):
        """
        Ensure we can get one traffic sign plan object with GeoJSON location.
        """
        traffic_sign_plan = self.__create_test_traffic_sign_plan()
        response = self.client.get(
            reverse("v1:trafficsignplan-detail", kwargs={"pk": traffic_sign_plan.id}),
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
            "device_type": self.test_device_type.id,
            "location": self.test_point.ewkt,
            "lifecycle": self.test_lifecycle.value,
            "owner": self.test_owner.pk,
        }
        response = self.client.post(reverse("v1:trafficsignplan-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TrafficSignPlan.objects.count(), 1)
        self.assertEqual(response.data.get("location"), data["location"])
        traffic_sign_plan = TrafficSignPlan.objects.first()
        self.assertEqual(traffic_sign_plan.device_type.id, data["device_type"])
        self.assertEqual(traffic_sign_plan.location.ewkt, data["location"])
        self.assertEqual(traffic_sign_plan.lifecycle.value, data["lifecycle"])

    def test_update_traffic_sign_plan(self):
        """
        Ensure we can update existing traffic sign plan object.
        """
        traffic_sign_plan = self.__create_test_traffic_sign_plan()
        data = {
            "device_type": self.test_device_type_2.id,
            "location": self.test_point.ewkt,
            "lifecycle": self.test_lifecycle_2.value,
            "owner": self.test_owner.pk,
        }
        response = self.client.put(
            reverse("v1:trafficsignplan-detail", kwargs={"pk": traffic_sign_plan.id}),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TrafficSignPlan.objects.count(), 1)
        traffic_sign_plan = TrafficSignPlan.objects.first()
        self.assertEqual(traffic_sign_plan.device_type.id, data["device_type"])
        self.assertEqual(traffic_sign_plan.location.ewkt, data["location"])
        self.assertEqual(traffic_sign_plan.lifecycle.value, data["lifecycle"])

    def test_delete_traffic_sign_plan_detail(self):
        """
        Ensure we can soft-delete one traffic sign plan object.
        """
        traffic_sign_plan = self.__create_test_traffic_sign_plan()
        response = self.client.delete(
            reverse("v1:trafficsignplan-detail", kwargs={"pk": traffic_sign_plan.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TrafficSignPlan.objects.count(), 1)
        deleted_traffic_sign_plan = TrafficSignPlan.objects.get(id=str(traffic_sign_plan.id))
        self.assertEqual(deleted_traffic_sign_plan.id, traffic_sign_plan.id)
        self.assertFalse(deleted_traffic_sign_plan.is_active)
        self.assertEqual(deleted_traffic_sign_plan.deleted_by, self.user)
        self.assertTrue(deleted_traffic_sign_plan.deleted_at)

    def test_get_deleted_traffic_sign_plan_returns_not_found(self):
        traffic_sign_plan = self.__create_test_traffic_sign_plan()
        response = self.client.delete(
            reverse("v1:trafficsignplan-detail", kwargs={"pk": traffic_sign_plan.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get(
            reverse("v1:trafficsignplan-detail", kwargs={"pk": traffic_sign_plan.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def __create_test_traffic_sign_plan(self):
        return TrafficSignPlan.objects.create(
            device_type=self.test_device_type,
            location=self.test_point,
            lifecycle=self.test_lifecycle,
            owner=self.test_owner,
            created_by=self.user,
            updated_by=self.user,
        )


@pytest.mark.django_db
@pytest.mark.parametrize("location,location_query,expected", point_location_test_data_3d)
def test_filter_traffic_sign_reals_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    traffic_sign_real = get_traffic_sign_real(location)
    response = api_client.get(reverse("v1:trafficsignreal-list"), {"location": location_query.ewkt})

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == expected

    if expected == 1:
        data = response.data.get("results")[0]
        assert str(traffic_sign_real.id) == data.get("id")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    point_location_error_test_data_3d,
)
def test_filter_error_traffic_sign_reals_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    get_traffic_sign_real(location)
    response = api_client.get(reverse("v1:trafficsignreal-list"), {"location": location_query})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data.get("location")[0] == expected


@pytest.mark.django_db
@pytest.mark.parametrize("target_model", (None, DeviceTypeTargetModel.TRAFFIC_SIGN))
def test__traffic_sign_real__valid_device_type(target_model):
    """
    Ensure that device types with supported target_model value are allowed.
    """
    client = get_api_client(user=get_user(admin=True))
    traffic_sign_real = get_traffic_sign_real()
    device_type = get_traffic_control_device_type(
        code="123", description="test", target_model=target_model, value="12.5"
    )
    data = {"device_type": device_type.id}

    response = client.patch(
        reverse("v1:trafficsignreal-detail", kwargs={"pk": traffic_sign_real.pk}),
        data,
        format="json",
    )

    traffic_sign_real.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert traffic_sign_real.device_type == device_type
    assert traffic_sign_real.value == Decimal("12.5")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "target_model",
    (
        DeviceTypeTargetModel.BARRIER,
        DeviceTypeTargetModel.ROAD_MARKING,
        DeviceTypeTargetModel.SIGNPOST,
        DeviceTypeTargetModel.TRAFFIC_LIGHT,
    ),
)
def test__traffic_sign_real__invalid_device_type(target_model):
    """
    Ensure that device types with unsupported target_model value are not allowed.
    """
    client = get_api_client(user=get_user(admin=True))
    traffic_sign_real = get_traffic_sign_real()
    device_type = get_traffic_control_device_type(code="123", description="test", target_model=target_model)
    data = {"device_type": device_type.id}

    response = client.patch(
        reverse("v1:trafficsignreal-detail", kwargs={"pk": traffic_sign_real.pk}),
        data,
        format="json",
    )

    traffic_sign_real.refresh_from_db()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert traffic_sign_real.device_type != device_type


class TrafficSignRealTests(TrafficControlAPIBaseTestCase3D):
    def test_get_all_traffic_sign_reals(self):
        """
        Ensure we can get all traffic sign real objects.
        """
        count = 3
        for i in range(count):
            self.__create_test_traffic_sign_real()
        response = self.client.get(reverse("v1:trafficsignreal-list"))
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
        response = self.client.get(reverse("v1:trafficsignreal-list"), data={"geo_format": "geojson"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

        results = response.data.get("results")
        for result in results:
            traffic_sign_real = TrafficSignReal.objects.get(id=result.get("id"))
            self.assertEqual(result.get("location"), GeoJsonDict(traffic_sign_real.location.json))

    def test_get_traffic_sign_real_detail(self):
        """
        Ensure we can get one traffic sign real object.
        """
        traffic_sign_real = self.__create_test_traffic_sign_real()
        operation_1 = add_traffic_sign_real_operation(traffic_sign_real, operation_date=datetime.date(2020, 11, 5))
        operation_2 = add_traffic_sign_real_operation(traffic_sign_real, operation_date=datetime.date(2020, 11, 15))
        operation_3 = add_traffic_sign_real_operation(traffic_sign_real, operation_date=datetime.date(2020, 11, 10))
        response = self.client.get(reverse("v1:trafficsignreal-detail", kwargs={"pk": traffic_sign_real.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(traffic_sign_real.id))
        self.assertEqual(traffic_sign_real.location.ewkt, response.data.get("location"))
        # verify operations are ordered by operation_date
        operation_ids = [operation["id"] for operation in response.data["operations"]]
        self.assertEqual(operation_ids, [operation_1.id, operation_3.id, operation_2.id])

    def test_get_traffic_sign_real_detail__geojson(self):
        """
        Ensure we can get one traffic sign real object with GeoJSON location.
        """
        traffic_sign_real = self.__create_test_traffic_sign_real()
        response = self.client.get(
            reverse("v1:trafficsignreal-detail", kwargs={"pk": traffic_sign_real.id}),
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
            "device_type": self.test_device_type.id,
            "location": self.test_point.ewkt,
            "installation_date": "2020-01-02",
            "lifecycle": self.test_lifecycle.value,
            "installation_id": 123,
            "permit_decision_id": 456,
            "owner": self.test_owner.pk,
        }
        response = self.client.post(reverse("v1:trafficsignreal-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TrafficSignReal.objects.count(), 1)
        self.assertEqual(response.data.get("location"), data["location"])
        traffic_sign_real = TrafficSignReal.objects.first()
        self.assertEqual(traffic_sign_real.device_type.id, data["device_type"])
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
            "device_type": self.test_device_type_2.id,
            "location": self.test_point.ewkt,
            "installation_date": "2020-01-03",
            "lifecycle": self.test_lifecycle_2.value,
            "installation_id": 123,
            "permit_decision_id": 456,
            "owner": self.test_owner.pk,
        }
        response = self.client.put(
            reverse("v1:trafficsignreal-detail", kwargs={"pk": traffic_sign_real.id}),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TrafficSignReal.objects.count(), 1)
        traffic_sign_real = TrafficSignReal.objects.first()
        self.assertEqual(traffic_sign_real.device_type.id, data["device_type"])
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
            reverse("v1:trafficsignreal-detail", kwargs={"pk": traffic_sign_real.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TrafficSignReal.objects.count(), 1)
        deleted_traffic_sign_real = TrafficSignReal.objects.get(id=str(traffic_sign_real.id))
        self.assertEqual(deleted_traffic_sign_real.id, traffic_sign_real.id)
        self.assertFalse(deleted_traffic_sign_real.is_active)
        self.assertEqual(deleted_traffic_sign_real.deleted_by, self.user)
        self.assertTrue(deleted_traffic_sign_real.deleted_at)

    def test_get_deleted_traffic_sign_real_returns_not_found(self):
        traffic_sign_real = self.__create_test_traffic_sign_real()
        response = self.client.delete(
            reverse("v1:trafficsignreal-detail", kwargs={"pk": traffic_sign_real.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get(
            reverse("v1:trafficsignreal-detail", kwargs={"pk": traffic_sign_real.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def __create_test_traffic_sign_real(self):
        traffic_sign_plan = TrafficSignPlan.objects.create(
            device_type=self.test_device_type,
            location=self.test_point,
            lifecycle=self.test_lifecycle,
            owner=self.test_owner,
            created_by=self.user,
            updated_by=self.user,
        )
        return TrafficSignReal.objects.create(
            traffic_sign_plan=traffic_sign_plan,
            device_type=self.test_device_type,
            location=self.test_point,
            installation_date=datetime.datetime.strptime("01012020", "%d%m%Y").date(),
            lifecycle=self.test_lifecycle,
            owner=self.test_owner,
            created_by=self.user,
            updated_by=self.user,
        )

import datetime
import json

import pytest
from auditlog.models import LogEntry
from django.urls import reverse
from rest_framework import status
from rest_framework_gis.fields import GeoJsonDict

from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.models import TrafficLightPlan, TrafficLightReal, TrafficLightSoundBeaconValue, TrafficLightType
from traffic_control.tests.factories import (
    add_traffic_light_real_operation,
    get_api_client,
    get_mount_type,
    get_operation_type,
    get_owner,
    get_traffic_control_device_type,
    get_traffic_light_plan,
    get_traffic_light_real,
    get_user,
    PlanFactory,
)
from traffic_control.tests.test_base_api import (
    point_location_error_test_data,
    point_location_test_data,
    TrafficControlAPIBaseTestCase,
)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    point_location_test_data,
)
def test_filter_traffic_light_plans_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    traffic_light_plan = get_traffic_light_plan(location)
    response = api_client.get(reverse("v1:trafficlightplan-list"), {"location": location_query.ewkt})

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == expected

    if expected == 1:
        data = response.data.get("results")[0]
        assert str(traffic_light_plan.id) == data.get("id")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    point_location_error_test_data,
)
def test_filter_error_traffic_light_plans_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    get_traffic_light_plan(location)
    response = api_client.get(reverse("v1:trafficlightplan-list"), {"location": location_query})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data.get("location")[0] == expected


@pytest.mark.django_db
@pytest.mark.parametrize("target_model", (None, DeviceTypeTargetModel.TRAFFIC_LIGHT))
def test__traffic_light_plan__valid_device_type(target_model):
    """
    Ensure that device types with supported target_model value are allowed.
    """
    user = get_user(admin=True)
    client = get_api_client(user=user, use_token_auth=True)
    traffic_light_plan = get_traffic_light_plan()
    device_type = get_traffic_control_device_type(code="123", description="test", target_model=target_model)
    data = {"device_type": device_type.id}

    response = client.patch(
        reverse("v1:trafficlightplan-detail", kwargs={"pk": traffic_light_plan.pk}),
        data,
        format="json",
    )

    traffic_light_plan.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert traffic_light_plan.device_type == device_type

    # Just a quick one test modified for checking auditlog actor setting
    # There is a separate ticket for testing auditlog writing
    log_entries = LogEntry.objects.get_for_object(traffic_light_plan)
    # one create and one update entry
    assert log_entries.count() == 2
    create_entry = log_entries.get(action=LogEntry.Action.CREATE)
    # created directly to database -> no actor
    assert create_entry.actor is None
    update_entry = log_entries.get(action=LogEntry.Action.UPDATE)
    # created via API -> actor should be set
    assert update_entry.actor == user


@pytest.mark.django_db
@pytest.mark.parametrize(
    "target_model",
    (
        DeviceTypeTargetModel.BARRIER,
        DeviceTypeTargetModel.ROAD_MARKING,
        DeviceTypeTargetModel.SIGNPOST,
        DeviceTypeTargetModel.TRAFFIC_SIGN,
    ),
)
def test__traffic_light_plan__invalid_device_type(target_model):
    """
    Ensure that device types with unsupported target_model value are not allowed.
    """
    client = get_api_client(user=get_user(admin=True))
    traffic_light_plan = get_traffic_light_plan()
    device_type = get_traffic_control_device_type(code="123", description="test", target_model=target_model)
    data = {"device_type": device_type.id}

    response = client.patch(
        reverse("v1:trafficlightplan-detail", kwargs={"pk": traffic_light_plan.pk}),
        data,
        format="json",
    )

    traffic_light_plan.refresh_from_db()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert traffic_light_plan.device_type != device_type


class TrafficLightPlanTests(TrafficControlAPIBaseTestCase):
    def test_get_all_traffic_light_plans(self):
        """
        Ensure we can get all traffic light plan objects.
        """
        count = 3
        for i in range(count):
            self.__create_test_traffic_light_plan()
        response = self.client.get(reverse("v1:trafficlightplan-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

        results = response.data.get("results")
        for result in results:
            traffic_light_plan = TrafficLightPlan.objects.get(id=result.get("id"))
            self.assertEqual(result.get("location"), traffic_light_plan.location.ewkt)

    def test_get_all_traffic_light_plans__geojson(self):
        """
        Ensure we can get all traffic light plan objects with GeoJSON location.
        """
        count = 3
        for i in range(count):
            self.__create_test_traffic_light_plan()
        response = self.client.get(reverse("v1:trafficlightplan-list"), data={"geo_format": "geojson"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

        results = response.data.get("results")
        for result in results:
            traffic_light_plan = TrafficLightPlan.objects.get(id=result.get("id"))
            self.assertEqual(result.get("location"), GeoJsonDict(traffic_light_plan.location.json))

    def test_get_traffic_light_detail(self):
        """
        Ensure we can get one traffic light plan object.
        """
        traffic_light = self.__create_test_traffic_light_plan()
        response = self.client.get(reverse("v1:trafficlightplan-detail", kwargs={"pk": traffic_light.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(traffic_light.id))
        self.assertEqual(traffic_light.location.ewkt, response.data.get("location"))

    def test_get_traffic_light_detail__geojson(self):
        """
        Ensure we can get one traffic light plan object with GeoJSON location.
        """
        traffic_light = self.__create_test_traffic_light_plan()
        response = self.client.get(
            reverse("v1:trafficlightplan-detail", kwargs={"pk": traffic_light.id}),
            data={"geo_format": "geojson"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(traffic_light.id))
        traffic_light_geojson = GeoJsonDict(traffic_light.location.json)
        self.assertEqual(traffic_light_geojson, response.data.get("location"))

    def test_create_traffic_light_plan(self):
        """
        Ensure we can create a new traffic light plan object.
        """
        data = {
            "device_type": self.test_device_type.id,
            "type": TrafficLightType.SIGNAL.value,
            "location": self.test_point.ewkt,
            "lifecycle": self.test_lifecycle.value,
            "owner": self.test_owner.pk,
        }
        response = self.client.post(reverse("v1:trafficlightplan-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TrafficLightPlan.objects.count(), 1)
        self.assertEqual(response.data.get("location"), data["location"])
        traffic_light = TrafficLightPlan.objects.first()
        self.assertEqual(traffic_light.device_type.id, data["device_type"])
        self.assertEqual(traffic_light.type.value, data["type"])
        self.assertEqual(traffic_light.location.ewkt, data["location"])
        self.assertEqual(traffic_light.lifecycle.value, data["lifecycle"])

    def test_update_traffic_light_plan(self):
        """
        Ensure we can update existing traffic light plan object.
        """
        traffic_light = self.__create_test_traffic_light_plan()
        data = {
            "device_type": self.test_device_type.id,
            "type": TrafficLightType.ARROW_RIGHT.value,
            "location": self.test_point.ewkt,
            "lifecycle": self.test_lifecycle_2.value,
            "owner": self.test_owner.pk,
        }
        response = self.client.put(
            reverse("v1:trafficlightplan-detail", kwargs={"pk": traffic_light.id}),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TrafficLightPlan.objects.count(), 1)
        traffic_light = TrafficLightPlan.objects.first()
        self.assertEqual(traffic_light.device_type.id, data["device_type"])
        self.assertEqual(traffic_light.type.value, data["type"])
        self.assertEqual(traffic_light.location.ewkt, data["location"])
        self.assertEqual(traffic_light.lifecycle.value, data["lifecycle"])

    def test_delete_traffic_light_plan_detail(self):
        """
        Ensure we can soft-delete one traffic light plan object.
        """
        traffic_light = self.__create_test_traffic_light_plan()
        response = self.client.delete(
            reverse("v1:trafficlightplan-detail", kwargs={"pk": traffic_light.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TrafficLightPlan.objects.count(), 1)
        deleted_traffic_light = TrafficLightPlan.objects.get(id=str(traffic_light.id))
        self.assertEqual(deleted_traffic_light.id, traffic_light.id)
        self.assertFalse(deleted_traffic_light.is_active)
        self.assertEqual(deleted_traffic_light.deleted_by, self.user)
        self.assertTrue(deleted_traffic_light.deleted_at)

    def test_get_deleted_traffic_light_plan_return_not_found(self):
        traffic_light = self.__create_test_traffic_light_plan()
        response = self.client.delete(
            reverse("v1:trafficlightplan-detail", kwargs={"pk": traffic_light.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get(
            reverse("v1:trafficlightplan-detail", kwargs={"pk": traffic_light.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def __create_test_traffic_light_plan(self):
        return TrafficLightPlan.objects.create(
            device_type=self.test_device_type,
            location=self.test_point,
            type=TrafficLightType.SIGNAL,
            lifecycle=self.test_lifecycle,
            mount_type=get_mount_type(),
            road_name="Testingroad",
            sound_beacon=TrafficLightSoundBeaconValue.YES,
            owner=self.test_owner,
            created_by=self.user,
            updated_by=self.user,
        )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    point_location_test_data,
)
def test_filter_traffic_light_reals_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    traffic_light_real = get_traffic_light_real(location)
    response = api_client.get(reverse("v1:trafficlightreal-list"), {"location": location_query.ewkt})

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == expected

    if expected == 1:
        data = response.data.get("results")[0]
        assert str(traffic_light_real.id) == data.get("id")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    point_location_error_test_data,
)
def test_filter_error_traffic_light_reals_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    get_traffic_light_real(location)
    response = api_client.get(reverse("v1:trafficlightreal-list"), {"location": location_query})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data.get("location")[0] == expected


@pytest.mark.django_db
@pytest.mark.parametrize("target_model", (None, DeviceTypeTargetModel.TRAFFIC_LIGHT))
def test__traffic_light_real__valid_device_type(target_model):
    """
    Ensure that device types with supported target_model value are allowed.
    """
    client = get_api_client(user=get_user(admin=True))
    traffic_light_real = get_traffic_light_real()
    device_type = get_traffic_control_device_type(code="123", description="test", target_model=target_model)
    data = {"device_type": device_type.id}

    response = client.patch(
        reverse("v1:trafficlightreal-detail", kwargs={"pk": traffic_light_real.pk}),
        data,
        format="json",
    )

    traffic_light_real.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert traffic_light_real.device_type == device_type


@pytest.mark.django_db
@pytest.mark.parametrize(
    "target_model",
    (
        DeviceTypeTargetModel.BARRIER,
        DeviceTypeTargetModel.ROAD_MARKING,
        DeviceTypeTargetModel.SIGNPOST,
        DeviceTypeTargetModel.TRAFFIC_SIGN,
    ),
)
def test__traffic_light_real__invalid_device_type(target_model):
    """
    Ensure that device types with unsupported target_model value are not allowed.
    """
    client = get_api_client(user=get_user(admin=True))
    traffic_light_real = get_traffic_light_real()
    device_type = get_traffic_control_device_type(code="123", description="test", target_model=target_model)
    data = {"device_type": device_type.id}

    response = client.patch(
        reverse("v1:trafficlightreal-detail", kwargs={"pk": traffic_light_real.pk}),
        data,
        format="json",
    )

    traffic_light_real.refresh_from_db()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert traffic_light_real.device_type != device_type


class TrafficLightRealTests(TrafficControlAPIBaseTestCase):
    def test_get_all_traffic_light_reals(self):
        """
        Ensure we can get all real traffic light objects.
        """
        plan = PlanFactory.create(decision_id="TEST-DECISION-ID")
        tlp = get_traffic_light_plan(plan=plan)

        count = 3
        for i in range(count):
            self.__create_test_traffic_light_real(traffic_light_plan=tlp)
        response = self.client.get(reverse("v1:trafficlightreal-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

        results = response.data.get("results")
        for result in results:
            traffic_light_real = TrafficLightReal.objects.get(id=result.get("id"))
            self.assertEqual(result.get("location"), traffic_light_real.location.ewkt)
            self.assertEqual(result.get("plan_decision_id"), "TEST-DECISION-ID")

    def test_get_all_traffic_light_reals__geojson(self):
        """
        Ensure we can get all real traffic light objects with GeoJSON location.
        """
        plan = PlanFactory.create(decision_id="TEST-DECISION-ID")
        tlp = get_traffic_light_plan(plan=plan)

        count = 3
        for i in range(count):
            self.__create_test_traffic_light_real(traffic_light_plan=tlp)
        response = self.client.get(reverse("v1:trafficlightreal-list"), data={"geo_format": "geojson"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

        results = response.data.get("results")
        for result in results:
            traffic_light_real = TrafficLightReal.objects.get(id=result.get("id"))
            self.assertEqual(result.get("location"), GeoJsonDict(traffic_light_real.location.json))
            self.assertEqual(result.get("plan_decision_id"), "TEST-DECISION-ID")

    def test_get_traffic_light_real_detail(self):
        """
        Ensure we can get one real traffic light object.
        """
        plan = PlanFactory.create(decision_id="TEST-DECISION-ID")
        tlp = get_traffic_light_plan(plan=plan)
        traffic_light_real = self.__create_test_traffic_light_real(traffic_light_plan=tlp)
        operation_1 = add_traffic_light_real_operation(traffic_light_real, operation_date=datetime.date(2020, 11, 5))
        operation_2 = add_traffic_light_real_operation(traffic_light_real, operation_date=datetime.date(2020, 11, 15))
        operation_3 = add_traffic_light_real_operation(traffic_light_real, operation_date=datetime.date(2020, 11, 10))
        response = self.client.get(reverse("v1:trafficlightreal-detail", kwargs={"pk": traffic_light_real.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(traffic_light_real.id))
        self.assertEqual(traffic_light_real.location.ewkt, response.data.get("location"))
        self.assertEqual(response.data.get("plan_decision_id"), "TEST-DECISION-ID")
        # verify operations are ordered by operation_date
        operation_ids = [operation["id"] for operation in response.data["operations"]]
        self.assertEqual(operation_ids, [operation_1.id, operation_3.id, operation_2.id])

    def test_get_traffic_light_real_detail__geojson(self):
        """
        Ensure we can get one real traffic light object with GeoJSON location.
        """
        plan = PlanFactory.create(decision_id="TEST-DECISION-ID")
        tlp = get_traffic_light_plan(plan=plan)
        traffic_light_real = self.__create_test_traffic_light_real(traffic_light_plan=tlp)
        response = self.client.get(
            reverse("v1:trafficlightreal-detail", kwargs={"pk": traffic_light_real.id}),
            data={"geo_format": "geojson"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(traffic_light_real.id))
        self.assertEqual(response.data.get("plan_decision_id"), "TEST-DECISION-ID")
        traffic_light_real_geojson = GeoJsonDict(traffic_light_real.location.json)
        self.assertEqual(traffic_light_real_geojson, response.data.get("location"))

    def test_create_traffic_light_real(self):
        """
        Ensure we can create a new real traffic light object.
        """
        data = {
            "device_type": self.test_device_type.id,
            "type": TrafficLightType.SIGNAL.value,
            "location": self.test_point.ewkt,
            "installation_date": "2020-01-02",
            "lifecycle": self.test_lifecycle.value,
            "owner": self.test_owner.pk,
        }
        response = self.client.post(reverse("v1:trafficlightreal-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TrafficLightReal.objects.count(), 1)
        self.assertEqual(response.data.get("location"), data["location"])
        traffic_light_real = TrafficLightReal.objects.first()
        self.assertEqual(traffic_light_real.device_type.id, data["device_type"])
        self.assertEqual(traffic_light_real.type.value, data["type"])
        self.assertEqual(traffic_light_real.location.ewkt, data["location"])
        self.assertEqual(
            traffic_light_real.installation_date.strftime("%Y-%m-%d"),
            data["installation_date"],
        )
        self.assertEqual(traffic_light_real.lifecycle.value, data["lifecycle"])

    def test_update_traffic_light_real(self):
        """
        Ensure we can update existing real traffic light object.
        """
        traffic_light_real = self.__create_test_traffic_light_real()
        data = {
            "device_type": self.test_device_type_2.id,
            "type": TrafficLightType.PEDESTRIAN.value,
            "location": self.test_point.ewkt,
            "installation_date": "2020-01-21",
            "lifecycle": self.test_lifecycle_2.value,
            "owner": self.test_owner.pk,
        }
        response = self.client.put(
            reverse("v1:trafficlightreal-detail", kwargs={"pk": traffic_light_real.id}),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TrafficLightReal.objects.count(), 1)
        traffic_light_real = TrafficLightReal.objects.first()
        self.assertEqual(traffic_light_real.device_type.id, data["device_type"])
        self.assertEqual(traffic_light_real.type.value, data["type"])
        self.assertEqual(traffic_light_real.location.ewkt, data["location"])
        self.assertEqual(
            traffic_light_real.installation_date.strftime("%Y-%m-%d"),
            data["installation_date"],
        )
        self.assertEqual(traffic_light_real.lifecycle.value, data["lifecycle"])

    def test_delete_traffic_light_real_detail(self):
        """
        Ensure we can soft-delete one real traffic light object.
        """
        traffic_light_real = self.__create_test_traffic_light_real()
        response = self.client.delete(
            reverse("v1:trafficlightreal-detail", kwargs={"pk": traffic_light_real.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TrafficLightReal.objects.count(), 1)
        deleted_traffic_light_real = TrafficLightReal.objects.get(id=str(traffic_light_real.id))
        self.assertEqual(deleted_traffic_light_real.id, traffic_light_real.id)
        self.assertFalse(deleted_traffic_light_real.is_active)
        self.assertEqual(deleted_traffic_light_real.deleted_by, self.user)
        self.assertTrue(deleted_traffic_light_real.deleted_at)

    def test_get_deleted_traffic_light_real_returns_not_found(self):
        traffic_light_real = self.__create_test_traffic_light_real()
        response = self.client.delete(
            reverse("v1:trafficlightreal-detail", kwargs={"pk": traffic_light_real.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get(
            reverse("v1:trafficlightreal-detail", kwargs={"pk": traffic_light_real.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_operation_traffic_light_real(self):
        traffic_light_real = self.__create_test_traffic_light_real()
        operation_type = get_operation_type()
        data = {
            "operation_date": "2020-01-01",
            "operation_type_id": operation_type.pk,
        }
        url = reverse("traffic-light-real-operations-list", kwargs={"traffic_light_real_pk": traffic_light_real.pk})
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(traffic_light_real.operations.all().count(), 1)

    def test_update_operation_traffic_light_real(self):
        traffic_light_real = self.__create_test_traffic_light_real()
        operation_type = get_operation_type()
        operation = add_traffic_light_real_operation(
            traffic_light_real=traffic_light_real,
            operation_type=operation_type,
            operation_date=datetime.date(2020, 1, 1),
        )
        data = {
            "operation_date": "2020-02-01",
            "operation_type_id": operation_type.pk,
        }
        url = reverse(
            "traffic-light-real-operations-detail",
            kwargs={"traffic_light_real_pk": traffic_light_real.pk, "pk": operation.pk},
        )
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(traffic_light_real.operations.all().count(), 1)
        self.assertEqual(traffic_light_real.operations.all().first().operation_date, datetime.date(2020, 2, 1))

    def __create_test_traffic_light_real(self, traffic_light_plan=None):
        traffic_light_plan = (
            TrafficLightPlan.objects.create(
                device_type=self.test_device_type,
                location=self.test_point,
                type=TrafficLightType.SIGNAL,
                lifecycle=self.test_lifecycle,
                mount_type=get_mount_type(),
                road_name="Testingroad",
                sound_beacon=TrafficLightSoundBeaconValue.YES,
                owner=self.test_owner,
                created_by=self.user,
                updated_by=self.user,
            )
            if not traffic_light_plan
            else traffic_light_plan
        )

        return TrafficLightReal.objects.create(
            device_type=self.test_device_type,
            traffic_light_plan=traffic_light_plan,
            location=self.test_point,
            type=TrafficLightType.SIGNAL,
            installation_date=datetime.datetime.strptime("01012020", "%d%m%Y").date(),
            lifecycle=self.test_lifecycle,
            mount_type=get_mount_type(),
            road_name="Testingroad",
            sound_beacon=TrafficLightSoundBeaconValue.YES,
            owner=self.test_owner,
            created_by=self.user,
            updated_by=self.user,
        )


@pytest.mark.parametrize(
    "method, expected_status",
    (
        ("GET", status.HTTP_200_OK),
        ("HEAD", status.HTTP_200_OK),
        ("OPTIONS", status.HTTP_200_OK),
        ("POST", status.HTTP_401_UNAUTHORIZED),
        ("PUT", status.HTTP_401_UNAUTHORIZED),
        ("PATCH", status.HTTP_401_UNAUTHORIZED),
        ("DELETE", status.HTTP_401_UNAUTHORIZED),
    ),
)
@pytest.mark.parametrize("view_type", ("detail", "list"))
@pytest.mark.django_db
def test__traffic_light_plan__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    traffic_light = get_traffic_light_plan(location="SRID=3879;POINT Z (0 0 0)")
    kwargs = {"pk": traffic_light.pk} if view_type == "detail" else None
    resource_path = reverse(f"v1:trafficlightplan-{view_type}", kwargs=kwargs)
    data = {
        "location": "SRID=3879;POINT Z (1 1 1)",
        "device_type": str(get_traffic_control_device_type().id),
        "owner": str(get_owner().id),
    }

    response = client.generic(method, resource_path, json.dumps(data), content_type="application/json")

    assert TrafficLightPlan.objects.count() == 1
    assert TrafficLightPlan.objects.first().is_active
    assert TrafficLightPlan.objects.first().location == "SRID=3879;POINT Z (0 0 0)"
    assert response.status_code == expected_status


@pytest.mark.parametrize(
    "method, expected_status",
    (
        ("GET", status.HTTP_200_OK),
        ("HEAD", status.HTTP_200_OK),
        ("OPTIONS", status.HTTP_200_OK),
        ("POST", status.HTTP_401_UNAUTHORIZED),
        ("PUT", status.HTTP_401_UNAUTHORIZED),
        ("PATCH", status.HTTP_401_UNAUTHORIZED),
        ("DELETE", status.HTTP_401_UNAUTHORIZED),
    ),
)
@pytest.mark.parametrize("view_type", ("detail", "list"))
@pytest.mark.django_db
def test__traffic_light_real__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    traffic_light = get_traffic_light_real(location="SRID=3879;POINT Z (0 0 0)")
    kwargs = {"pk": traffic_light.pk} if view_type == "detail" else None
    resource_path = reverse(f"v1:trafficlightreal-{view_type}", kwargs=kwargs)
    data = {
        "location": "SRID=3879;POINT Z (1 1 1)",
        "device_type": str(get_traffic_control_device_type().id),
        "owner": str(get_owner().id),
    }

    response = client.generic(method, resource_path, json.dumps(data), content_type="application/json")

    assert TrafficLightReal.objects.count() == 1
    assert TrafficLightReal.objects.first().is_active
    assert TrafficLightReal.objects.first().location == "SRID=3879;POINT Z (0 0 0)"
    assert response.status_code == expected_status


@pytest.mark.parametrize(
    "method, expected_status",
    (
        ("GET", status.HTTP_200_OK),
        ("HEAD", status.HTTP_200_OK),
        ("OPTIONS", status.HTTP_200_OK),
        ("POST", status.HTTP_401_UNAUTHORIZED),
        ("PUT", status.HTTP_401_UNAUTHORIZED),
        ("PATCH", status.HTTP_401_UNAUTHORIZED),
        ("DELETE", status.HTTP_401_UNAUTHORIZED),
    ),
)
@pytest.mark.parametrize("view_type", ("detail", "list"))
@pytest.mark.django_db
def test__traffic_light_real_operation__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    traffic_light = get_traffic_light_real()
    operation_type = get_operation_type()
    operation = add_traffic_light_real_operation(
        traffic_light_real=traffic_light,
        operation_type=operation_type,
        operation_date=datetime.date(2020, 1, 1),
    )

    data = {"operation_date": "2020-02-01", "operation_type_id": operation_type.pk}

    kwargs = {"traffic_light_real_pk": traffic_light.pk}
    if view_type == "detail":
        kwargs["pk"] = operation.pk

    resource_path = reverse(f"traffic-light-real-operations-{view_type}", kwargs=kwargs)

    response = client.generic(method, resource_path, data)

    assert traffic_light.operations.all().count() == 1
    assert traffic_light.operations.all().first().operation_date == datetime.date(2020, 1, 1)
    assert response.status_code == expected_status

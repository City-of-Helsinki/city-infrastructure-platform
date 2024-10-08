import datetime
import json

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework_gis.fields import GeoJsonDict

from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.models import RoadMarkingColor, RoadMarkingPlan, RoadMarkingReal
from traffic_control.tests.factories import (
    add_road_marking_real_operation,
    get_api_client,
    get_operation_type,
    get_owner,
    get_road_marking_plan,
    get_road_marking_real,
    get_traffic_control_device_type,
    get_user,
    PlanFactory,
    RoadMarkingPlanFactory,
    RoadMarkingRealFactory,
)
from traffic_control.tests.test_base_api import (
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
def test_filter_road_markings_plans_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    road_marking_plan = get_road_marking_plan(location)
    response = api_client.get(reverse("v1:roadmarkingplan-list"), {"location": location_query.ewkt})

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == expected

    if expected == 1:
        data = response.data.get("results")[0]
        assert str(road_marking_plan.id) == data.get("id")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    [*point_location_error_test_data, *line_location_error_test_data],
)
def test_filter_error_road_markings_plans_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    get_road_marking_plan(location)
    response = api_client.get(reverse("v1:roadmarkingplan-list"), {"location": location_query})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data.get("location")[0] == expected


@pytest.mark.django_db
@pytest.mark.parametrize("target_model", (None, DeviceTypeTargetModel.ROAD_MARKING))
def test__road_marking_plan__valid_device_type(target_model):
    """
    Ensure that device types with supported target_model value are allowed.
    """
    client = get_api_client(user=get_user(admin=True))
    road_marking_plan = get_road_marking_plan()
    device_type = get_traffic_control_device_type(code="123", description="test", target_model=target_model)
    data = {"device_type": device_type.id}

    response = client.patch(
        reverse("v1:roadmarkingplan-detail", kwargs={"pk": road_marking_plan.pk}),
        data,
        format="json",
    )

    road_marking_plan.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert road_marking_plan.device_type == device_type


@pytest.mark.django_db
@pytest.mark.parametrize(
    "target_model",
    (
        DeviceTypeTargetModel.BARRIER,
        DeviceTypeTargetModel.SIGNPOST,
        DeviceTypeTargetModel.TRAFFIC_LIGHT,
        DeviceTypeTargetModel.TRAFFIC_SIGN,
    ),
)
def test__road_marking_plan__invalid_device_type(target_model):
    """
    Ensure that device types with unsupported target_model value are not allowed.
    """
    client = get_api_client(user=get_user(admin=True))
    road_marking_plan = get_road_marking_plan()
    device_type = get_traffic_control_device_type(code="123", description="test", target_model=target_model)
    data = {"device_type": device_type.id}

    response = client.patch(
        reverse("v1:roadmarkingplan-detail", kwargs={"pk": road_marking_plan.pk}),
        data,
        format="json",
    )

    road_marking_plan.refresh_from_db()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert road_marking_plan.device_type != device_type


class RoadMarkingPlanTests(TrafficControlAPIBaseTestCase):
    def test_get_all_road_markings(self):
        """
        Ensure we can get all road marking plan objects.
        """
        count = 3
        for i in range(count):
            self.__create_test_road_marking_plan()
        response = self.client.get(reverse("v1:roadmarkingplan-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

        results = response.data.get("results")
        for result in results:
            road_marking_plan = RoadMarkingPlan.objects.get(id=result.get("id"))
            self.assertEqual(result.get("location"), road_marking_plan.location.ewkt)

    def test_get_all_road_markings__geojson(self):
        """
        Ensure we can get all road marking plan objects with GeoJSON location.
        """
        count = 3
        for i in range(count):
            self.__create_test_road_marking_plan()
        response = self.client.get(reverse("v1:roadmarkingplan-list"), data={"geo_format": "geojson"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

        results = response.data.get("results")
        for result in results:
            road_marking_plan = RoadMarkingPlan.objects.get(id=result.get("id"))
            self.assertEqual(result.get("location"), GeoJsonDict(road_marking_plan.location.json))

    def test_get_road_marking_detail(self):
        """
        Ensure we can get one road marking plan object.
        """
        road_marking = self.__create_test_road_marking_plan()
        response = self.client.get(reverse("v1:roadmarkingplan-detail", kwargs={"pk": road_marking.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(road_marking.id))
        self.assertEqual(road_marking.location.ewkt, response.data.get("location"))

    def test_get_road_marking_detail__geojson(self):
        """
        Ensure we can get one road marking plan object with GeoJSON location.
        """
        road_marking = self.__create_test_road_marking_plan()
        response = self.client.get(
            reverse("v1:roadmarkingplan-detail", kwargs={"pk": road_marking.id}),
            data={"geo_format": "geojson"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(road_marking.id))
        road_marking_geojson = GeoJsonDict(road_marking.location.json)
        self.assertEqual(road_marking_geojson, response.data.get("location"))

    def test_create_road_marking(self):
        """
        Ensure we can create a new road marking plan object.
        """
        data = {
            "device_type": self.test_device_type.id,
            "location": self.test_point.ewkt,
            "lifecycle": self.test_lifecycle.value,
            "owner": self.test_owner.pk,
            "source_name": "test-source",
            "source_id": 1,
        }
        response = self.client.post(reverse("v1:roadmarkingplan-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RoadMarkingPlan.objects.count(), 1)
        self.assertEqual(response.data.get("location"), data["location"])
        road_marking = RoadMarkingPlan.objects.first()
        self.assertEqual(road_marking.device_type.id, data["device_type"])
        self.assertEqual(road_marking.location.ewkt, data["location"])
        self.assertEqual(road_marking.lifecycle.value, data["lifecycle"])

    def test_update_road_marking(self):
        """
        Ensure we can update existing road marking plan object.
        """
        road_marking = self.__create_test_road_marking_plan()
        data = {
            "device_type": self.test_device_type_2.id,
            "location": self.test_point.ewkt,
            "lifecycle": self.test_lifecycle_2.value,
            "owner": self.test_owner.pk,
            "source_name": "test-source",
            "source_id": 1,
        }
        response = self.client.put(
            reverse("v1:roadmarkingplan-detail", kwargs={"pk": road_marking.id}),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(RoadMarkingPlan.objects.count(), 1)
        road_marking = RoadMarkingPlan.objects.first()
        self.assertEqual(road_marking.device_type.id, data["device_type"])
        self.assertEqual(road_marking.location.ewkt, data["location"])
        self.assertEqual(road_marking.lifecycle.value, data["lifecycle"])

    def test_delete_road_marking_detail(self):
        """
        Ensure we can soft-delete one road marking plan object.
        """
        road_marking = self.__create_test_road_marking_plan()
        response = self.client.delete(
            reverse("v1:roadmarkingplan-detail", kwargs={"pk": road_marking.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(RoadMarkingPlan.objects.count(), 1)
        deleted_road_marking = RoadMarkingPlan.objects.get(id=str(road_marking.id))
        self.assertEqual(deleted_road_marking.id, road_marking.id)
        self.assertFalse(deleted_road_marking.is_active)
        self.assertEqual(deleted_road_marking.deleted_by, self.user)
        self.assertTrue(deleted_road_marking.deleted_at)

    def test_get_deleted_road_marking_return_not_found(self):
        road_marking = self.__create_test_road_marking_plan()
        response = self.client.delete(
            reverse("v1:roadmarkingplan-detail", kwargs={"pk": road_marking.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get(
            reverse("v1:roadmarkingplan-detail", kwargs={"pk": road_marking.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def __create_test_road_marking_plan(self):
        return RoadMarkingPlan.objects.create(
            device_type=self.test_device_type,
            value="30",
            color=RoadMarkingColor.WHITE,
            location=self.test_point,
            lifecycle=self.test_lifecycle,
            material="Maali",
            is_grinded=True,
            is_raised=False,
            road_name="Testingroad",
            owner=self.test_owner,
            created_by=self.user,
            updated_by=self.user,
        )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    [*point_location_test_data, *line_location_test_data],
)
def test_filter_road_markings_reals_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    road_marking_real = get_road_marking_real(location)
    response = api_client.get(reverse("v1:roadmarkingreal-list"), {"location": location_query.ewkt})

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == expected

    if expected == 1:
        data = response.data.get("results")[0]
        assert str(road_marking_real.id) == data.get("id")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    [*point_location_error_test_data, *line_location_error_test_data],
)
def test_filter_error_road_markings_reals_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    get_road_marking_real(location)
    response = api_client.get(reverse("v1:roadmarkingreal-list"), {"location": location_query})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data.get("location")[0] == expected


@pytest.mark.django_db
@pytest.mark.parametrize("target_model", (None, DeviceTypeTargetModel.ROAD_MARKING))
def test__road_marking_real__valid_device_type(target_model):
    """
    Ensure that device types with supported target_model value are allowed.
    """
    client = get_api_client(user=get_user(admin=True))
    road_marking_real = get_road_marking_real()
    device_type = get_traffic_control_device_type(code="123", description="test", target_model=target_model)
    data = {"device_type": device_type.id}

    response = client.patch(
        reverse("v1:roadmarkingreal-detail", kwargs={"pk": road_marking_real.pk}),
        data,
        format="json",
    )

    road_marking_real.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert road_marking_real.device_type == device_type


@pytest.mark.django_db
@pytest.mark.parametrize(
    "target_model",
    (
        DeviceTypeTargetModel.BARRIER,
        DeviceTypeTargetModel.SIGNPOST,
        DeviceTypeTargetModel.TRAFFIC_LIGHT,
        DeviceTypeTargetModel.TRAFFIC_SIGN,
    ),
)
def test__road_marking_real__invalid_device_type(target_model):
    """
    Ensure that device types with unsupported target_model value are not allowed.
    """
    client = get_api_client(user=get_user(admin=True))
    road_marking_real = get_road_marking_real()
    device_type = get_traffic_control_device_type(code="123", description="test", target_model=target_model)
    data = {"device_type": device_type.id}

    response = client.patch(
        reverse("v1:roadmarkingreal-detail", kwargs={"pk": road_marking_real.pk}),
        data,
        format="json",
    )

    road_marking_real.refresh_from_db()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert road_marking_real.device_type != device_type


class RoadMarkingRealTests(TrafficControlAPIBaseTestCase):
    def test_get_all_road_marking_reals(self):
        """
        Ensure we can get all real road marking objects.
        """
        plan = PlanFactory.create(decision_id="TEST-DECISION-ID")

        count = 3
        for i in range(count):
            rmp = RoadMarkingPlanFactory(plan=plan)
            self.__create_test_road_marking_real(road_marking_plan=rmp)
        response = self.client.get(reverse("v1:roadmarkingreal-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

        results = response.data.get("results")
        for result in results:
            road_marking_plan = RoadMarkingReal.objects.get(id=result.get("id"))
            self.assertEqual(result.get("location"), road_marking_plan.location.ewkt)
            self.assertEqual(result.get("plan_decision_id"), "TEST-DECISION-ID")

    def test_get_all_road_marking_reals__geojson(self):
        """
        Ensure we can get all real road marking objects with GeoJSON location.
        """
        plan = PlanFactory.create(decision_id="TEST-DECISION-ID")

        count = 3
        for i in range(count):
            rmp = RoadMarkingPlanFactory(plan=plan)
            self.__create_test_road_marking_real(road_marking_plan=rmp)
        response = self.client.get(reverse("v1:roadmarkingreal-list"), data={"geo_format": "geojson"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

        results = response.data.get("results")
        for result in results:
            road_marking_plan = RoadMarkingReal.objects.get(id=result.get("id"))
            self.assertEqual(result.get("location"), GeoJsonDict(road_marking_plan.location.json))
            self.assertEqual(result.get("plan_decision_id"), "TEST-DECISION-ID")

    def test_get_road_marking_real_detail(self):
        """
        Ensure we can get one real road marking object.
        """
        plan = PlanFactory.create(decision_id="TEST-DECISION-ID")
        rmp = get_road_marking_plan(plan=plan)
        road_marking_real = self.__create_test_road_marking_real(road_marking_plan=rmp)
        operation_1 = add_road_marking_real_operation(road_marking_real, operation_date=datetime.date(2020, 11, 5))
        operation_2 = add_road_marking_real_operation(road_marking_real, operation_date=datetime.date(2020, 11, 15))
        operation_3 = add_road_marking_real_operation(road_marking_real, operation_date=datetime.date(2020, 11, 10))
        response = self.client.get(reverse("v1:roadmarkingreal-detail", kwargs={"pk": road_marking_real.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(road_marking_real.id))
        self.assertEqual(road_marking_real.location.ewkt, response.data.get("location"))
        self.assertEqual(response.data.get("plan_decision_id"), "TEST-DECISION-ID")
        # verify operations are ordered by operation_date
        operation_ids = [operation["id"] for operation in response.data["operations"]]
        self.assertEqual(operation_ids, [operation_1.id, operation_3.id, operation_2.id])

    def test_get_road_marking_real_detail__geojson(self):
        """
        Ensure we can get one real road marking object with GeoJSON location.
        """
        plan = PlanFactory.create(decision_id="TEST-DECISION-ID")
        rmp = get_road_marking_plan(plan=plan)
        road_marking_real = self.__create_test_road_marking_real(road_marking_plan=rmp)
        response = self.client.get(
            reverse("v1:roadmarkingreal-detail", kwargs={"pk": road_marking_real.id}),
            data={"geo_format": "geojson"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(road_marking_real.id))
        road_marking_real_geojson = GeoJsonDict(road_marking_real.location.json)
        self.assertEqual(road_marking_real_geojson, response.data.get("location"))
        self.assertEqual(response.data.get("plan_decision_id"), "TEST-DECISION-ID")

    def test_create_road_marking_real(self):
        """
        Ensure we can create a new real road marking object.
        """
        data = {
            "device_type": self.test_device_type.id,
            "location": self.test_point.ewkt,
            "installation_date": "2020-01-02",
            "lifecycle": self.test_lifecycle.value,
            "owner": self.test_owner.pk,
            "source_name": "test-source",
            "source_id": 1,
        }
        response = self.client.post(reverse("v1:roadmarkingreal-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RoadMarkingReal.objects.count(), 1)
        self.assertEqual(response.data.get("location"), data["location"])
        road_marking_real = RoadMarkingReal.objects.first()
        self.assertEqual(road_marking_real.device_type.id, data["device_type"])
        self.assertEqual(road_marking_real.location.ewkt, data["location"])
        self.assertEqual(
            road_marking_real.installation_date.strftime("%Y-%m-%d"),
            data["installation_date"],
        )
        self.assertEqual(road_marking_real.lifecycle.value, data["lifecycle"])

    def test_create_road_marking_real_with_existing_plan(self):
        rm_plan = RoadMarkingPlanFactory()
        RoadMarkingRealFactory(road_marking_plan=rm_plan)
        data = {
            "device_type": self.test_device_type_2.id,
            "location": self.test_point.ewkt,
            "installation_date": "2020-01-21",
            "lifecycle": self.test_lifecycle_2.value,
            "owner": self.test_owner.pk,
            "source_name": "test-source",
            "source_id": 1,
            "road_marking_plan": rm_plan.id,
        }
        response = self.client.post(reverse("v1:roadmarkingreal-list"), data, format="json")
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(RoadMarkingReal.objects.count(), 1)
        assert "duplicate key value violates unique constraint" in response_data["detail"]
        assert "traffic_control_roadmarkingreal_unique_road_marking_plan_id" in response_data["detail"]

    def test_update_road_marking_real(self):
        """
        Ensure we can update existing real road marking object.
        """
        road_marking_real = self.__create_test_road_marking_real()
        data = {
            "device_type": self.test_device_type_2.id,
            "location": self.test_point.ewkt,
            "installation_date": "2020-01-21",
            "lifecycle": self.test_lifecycle_2.value,
            "owner": self.test_owner.pk,
            "source_name": "test-source",
            "source_id": 1,
        }
        response = self.client.put(
            reverse("v1:roadmarkingreal-detail", kwargs={"pk": road_marking_real.id}),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(RoadMarkingReal.objects.count(), 1)
        road_marking_real = RoadMarkingReal.objects.first()
        self.assertEqual(road_marking_real.device_type.id, data["device_type"])
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
            reverse("v1:roadmarkingreal-detail", kwargs={"pk": road_marking_real.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(RoadMarkingReal.objects.count(), 1)
        deleted_road_marking_real = RoadMarkingReal.objects.get(id=str(road_marking_real.id))
        self.assertEqual(deleted_road_marking_real.id, road_marking_real.id)
        self.assertFalse(deleted_road_marking_real.is_active)
        self.assertEqual(deleted_road_marking_real.deleted_by, self.user)
        self.assertTrue(deleted_road_marking_real.deleted_at)

    def test_get_deleted_road_marking_real_returns_not_found(self):
        road_marking_real = self.__create_test_road_marking_real()
        response = self.client.delete(
            reverse("v1:roadmarkingreal-detail", kwargs={"pk": road_marking_real.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get(
            reverse("v1:roadmarkingreal-detail", kwargs={"pk": road_marking_real.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_operation_road_marking_real(self):
        road_marking_real = self.__create_test_road_marking_real()
        operation_type = get_operation_type()
        data = {
            "operation_date": "2020-01-01",
            "operation_type_id": operation_type.pk,
        }
        url = reverse("road-marking-real-operations-list", kwargs={"road_marking_real_pk": road_marking_real.pk})
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(road_marking_real.operations.all().count(), 1)

    def test_update_operation_road_marking_real(self):
        road_marking_real = self.__create_test_road_marking_real()
        operation_type = get_operation_type()
        operation = add_road_marking_real_operation(
            road_marking_real=road_marking_real, operation_type=operation_type, operation_date=datetime.date(2020, 1, 1)
        )
        data = {
            "operation_date": "2020-02-01",
            "operation_type_id": operation_type.pk,
        }
        url = reverse(
            "road-marking-real-operations-detail",
            kwargs={"road_marking_real_pk": road_marking_real.pk, "pk": operation.pk},
        )
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(road_marking_real.operations.all().count(), 1)
        self.assertEqual(road_marking_real.operations.all().first().operation_date, datetime.date(2020, 2, 1))

    def __create_test_road_marking_real(self, road_marking_plan=None):
        road_marking_plan = (
            RoadMarkingPlan.objects.create(
                device_type=self.test_device_type,
                value="30",
                color=RoadMarkingColor.WHITE,
                location=self.test_point,
                lifecycle=self.test_lifecycle,
                material="Maali",
                is_grinded=True,
                is_raised=False,
                road_name="Testingroad",
                owner=self.test_owner,
                created_by=self.user,
                updated_by=self.user,
            )
            if not road_marking_plan
            else road_marking_plan
        )

        return RoadMarkingReal.objects.create(
            device_type=self.test_device_type,
            road_marking_plan=road_marking_plan,
            value="30",
            color=RoadMarkingColor.WHITE,
            location=self.test_point,
            installation_date=datetime.datetime.strptime("01012020", "%d%m%Y").date(),
            lifecycle=self.test_lifecycle,
            material="Maali",
            is_grinded=True,
            is_raised=False,
            road_name="Testingroad",
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
def test__road_marking_plan__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    road_marking = get_road_marking_plan(location="SRID=3879;POINT Z (0 0 0)")
    kwargs = {"pk": road_marking.pk} if view_type == "detail" else None
    resource_path = reverse(f"v1:roadmarkingplan-{view_type}", kwargs=kwargs)
    data = {
        "location": "SRID=3879;POINT Z (1 1 1)",
        "device_type": str(get_traffic_control_device_type().id),
        "owner": str(get_owner().id),
    }

    response = client.generic(method, resource_path, json.dumps(data), content_type="application/json")

    assert RoadMarkingPlan.objects.count() == 1
    assert RoadMarkingPlan.objects.first().is_active
    assert RoadMarkingPlan.objects.first().location == "SRID=3879;POINT Z (0 0 0)"
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
def test__road_marking_real__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    road_marking = get_road_marking_real(location="SRID=3879;POINT Z (0 0 0)")
    kwargs = {"pk": road_marking.pk} if view_type == "detail" else None
    resource_path = reverse(f"v1:roadmarkingreal-{view_type}", kwargs=kwargs)
    data = {
        "location": "SRID=3879;POINT Z (1 1 1)",
        "device_type": str(get_traffic_control_device_type().id),
        "owner": str(get_owner().id),
    }

    response = client.generic(method, resource_path, json.dumps(data), content_type="application/json")

    assert RoadMarkingReal.objects.count() == 1
    assert RoadMarkingReal.objects.first().is_active
    assert RoadMarkingReal.objects.first().location == "SRID=3879;POINT Z (0 0 0)"
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
def test__road_marking_real_operation__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    road_marking = get_road_marking_real()
    operation_type = get_operation_type()
    operation = add_road_marking_real_operation(
        road_marking_real=road_marking,
        operation_type=operation_type,
        operation_date=datetime.date(2020, 1, 1),
    )

    data = {"operation_date": "2020-02-01", "operation_type_id": str(operation_type.pk)}

    kwargs = {"road_marking_real_pk": road_marking.pk}
    if view_type == "detail":
        kwargs["pk"] = operation.pk

    resource_path = reverse(f"road-marking-real-operations-{view_type}", kwargs=kwargs)

    response = client.generic(method, resource_path, json.dumps(data), content_type="application/json")

    assert road_marking.operations.all().count() == 1
    assert road_marking.operations.all().first().operation_date == datetime.date(2020, 1, 1)
    assert response.status_code == expected_status

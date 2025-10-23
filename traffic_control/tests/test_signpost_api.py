import datetime
import json
from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework_gis.fields import GeoJsonDict

from traffic_control.enums import (
    Condition,
    DeviceTypeTargetModel,
    InstallationStatus,
    LaneNumber,
    LaneType,
    Lifecycle,
    Reflection,
    Size,
)
from traffic_control.models import SignpostPlan, SignpostReal
from traffic_control.models.traffic_sign import LocationSpecifier
from traffic_control.tests.api_utils import do_filtering_test, do_illegal_geometry_test
from traffic_control.tests.factories import (
    add_signpost_real_operation,
    get_api_client,
    get_operation_type,
    get_owner,
    get_signpost_plan,
    get_signpost_real,
    get_user,
    OwnerFactory,
    PlanFactory,
    SignpostPlanFactory,
    SignpostRealFactory,
    TrafficControlDeviceTypeFactory,
)
from traffic_control.tests.test_base_api import (
    illegal_test_point,
    point_location_error_test_data,
    point_location_test_data,
    TrafficControlAPIBaseTestCase,
)
from traffic_control.tests.utils import MIN_X, MIN_Y


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    point_location_test_data,
)
def test_filter_signpost_plan_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    signpost_plan = get_signpost_plan(location)
    response = api_client.get(reverse("v1:signpostplan-list"), {"location": location_query.ewkt})

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == expected

    if expected == 1:
        data = response.data.get("results")[0]
        assert str(signpost_plan.id) == data.get("id")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    point_location_error_test_data,
)
def test_filter_error_signpost_plans_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    get_signpost_plan(location)
    response = api_client.get(reverse("v1:signpostplan-list"), {"location": location_query})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data.get("location")[0] == expected


@pytest.mark.parametrize(
    "field_name,value,second_value",
    (
        ("lane_number", LaneNumber.ADDITIONAL_LEFT_1, LaneNumber.ADDITIONAL_LEFT_2),
        ("lane_type", LaneType.HEAVY, LaneType.BIKE),
        ("lifecycle", Lifecycle.ACTIVE, Lifecycle.TEMPORARILY_ACTIVE),
        ("location_specifier", LocationSpecifier.ABOVE, LocationSpecifier.VERTICAL),
    ),
)
@pytest.mark.django_db
def test__signpost_plans_filtering__list(field_name, value, second_value):
    do_filtering_test(
        SignpostPlanFactory,
        "v1:signpostplan-list",
        field_name,
        value,
        second_value,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("target_model", (None, DeviceTypeTargetModel.SIGNPOST))
def test__signpost_plan__valid_device_type(target_model):
    """
    Ensure that device types with supported target_model value are allowed.
    """
    client = get_api_client(user=get_user(admin=True))
    signpost_plan = get_signpost_plan()
    device_type = TrafficControlDeviceTypeFactory(code="123", description="test", target_model=target_model, value="15")
    data = {"device_type": device_type.id}

    response = client.patch(
        reverse("v1:signpostplan-detail", kwargs={"pk": signpost_plan.pk}),
        data,
        format="json",
    )

    signpost_plan.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert signpost_plan.device_type == device_type
    assert signpost_plan.value == Decimal("15")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "target_model",
    (
        DeviceTypeTargetModel.BARRIER,
        DeviceTypeTargetModel.ROAD_MARKING,
        DeviceTypeTargetModel.TRAFFIC_LIGHT,
        DeviceTypeTargetModel.TRAFFIC_SIGN,
    ),
)
def test__signpost_plan__invalid_device_type(target_model):
    """
    Ensure that device types with unsupported target_model value are not allowed.
    """
    client = get_api_client(user=get_user(admin=True))
    signpost_plan = get_signpost_plan()
    device_type = TrafficControlDeviceTypeFactory(code="123", description="test", target_model=target_model)
    data = {"device_type": device_type.id}

    response = client.patch(
        reverse("v1:signpostplan-detail", kwargs={"pk": signpost_plan.pk}),
        data,
        format="json",
    )

    signpost_plan.refresh_from_db()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert signpost_plan.device_type != device_type


@pytest.mark.django_db
def test__signpost_plan__create_with_invalid_geometry():
    data = {
        "location": illegal_test_point.ewkt,
        "owner": OwnerFactory().pk,
    }
    do_illegal_geometry_test(
        "v1:signpostplan-list",
        data,
        [f"Geometry for signpostplan {illegal_test_point.ewkt} is not legal"],
    )


class SignpostPlanTests(TrafficControlAPIBaseTestCase):
    def test_get_all_signpost_plans(self):
        """
        Ensure we can get all signpost plan objects.
        """
        count = 3
        for i in range(count):
            self.__create_test_signpost_plan()
        response = self.client.get(reverse("v1:signpostplan-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

        results = response.data.get("results")
        for result in results:
            signpost_plan = SignpostPlan.objects.get(id=result.get("id"))
            self.assertEqual(result.get("location"), signpost_plan.location.ewkt)

    def test_get_all_signpost_plans__geojson(self):
        """
        Ensure we can get all signpost plan objects with GeoJSON location.
        """
        count = 3
        for i in range(count):
            self.__create_test_signpost_plan()
        response = self.client.get(reverse("v1:signpostplan-list"), data={"geo_format": "geojson"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

        results = response.data.get("results")
        for result in results:
            signpost_plan = SignpostPlan.objects.get(id=result.get("id"))
            self.assertEqual(result.get("location"), GeoJsonDict(signpost_plan.location.json))

    def test_get_signpost_plan_detail(self):
        """
        Ensure we can get one signpost plan object.
        """
        signpost_plan = self.__create_test_signpost_plan()
        response = self.client.get(reverse("v1:signpostplan-detail", kwargs={"pk": signpost_plan.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(signpost_plan.id))
        self.assertEqual(signpost_plan.location.ewkt, response.data.get("location"))

    def test_get_signpost_plan_detail__geojson(self):
        """
        Ensure we can get one signpost plan object with GeoJSON location.
        """
        signpost_plan = self.__create_test_signpost_plan()
        response = self.client.get(
            reverse("v1:signpostplan-detail", kwargs={"pk": signpost_plan.id}),
            data={"geo_format": "geojson"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(signpost_plan.id))
        signpost_plan_geojson = GeoJsonDict(signpost_plan.location.json)
        self.assertEqual(signpost_plan_geojson, response.data.get("location"))

    def test_create_signpost_plan(self):
        """
        Ensure we can create a new signpost plan object.
        """
        data = {
            "device_type": self.test_device_type.id,
            "location": self.test_point.ewkt,
            "lifecycle": self.test_lifecycle.value,
            "owner": self.test_owner.pk,
        }
        response = self.client.post(reverse("v1:signpostplan-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SignpostPlan.objects.count(), 1)
        self.assertEqual(response.data.get("location"), data["location"])
        signpost_plan = SignpostPlan.objects.first()
        self.assertEqual(signpost_plan.device_type.id, data["device_type"])
        self.assertEqual(signpost_plan.location.ewkt, data["location"])
        self.assertEqual(signpost_plan.lifecycle.value, data["lifecycle"])

    def test_update_signpost_plan(self):
        """
        Ensure we can update existing signpost plan object.
        """
        signpost_plan = self.__create_test_signpost_plan()
        data = {
            "device_type": self.test_device_type_2.id,
            "location": self.test_point.ewkt,
            "lifecycle": self.test_lifecycle_2.value,
            "owner": self.test_owner.pk,
        }
        response = self.client.put(
            reverse("v1:signpostplan-detail", kwargs={"pk": signpost_plan.id}),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(SignpostPlan.objects.count(), 1)
        signpost_plan = SignpostPlan.objects.first()
        self.assertEqual(signpost_plan.device_type.id, data["device_type"])
        self.assertEqual(signpost_plan.location.ewkt, data["location"])
        self.assertEqual(signpost_plan.lifecycle.value, data["lifecycle"])

    def test_delete_signpost_plan_detail(self):
        """
        Ensure we can soft-delete one signpost plan object.
        """
        signpost_plan = self.__create_test_signpost_plan()
        response = self.client.delete(
            reverse("v1:signpostplan-detail", kwargs={"pk": signpost_plan.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(SignpostPlan.objects.count(), 1)
        deleted_signpost_plan = SignpostPlan.objects.get(id=str(signpost_plan.id))
        self.assertEqual(deleted_signpost_plan.id, signpost_plan.id)
        self.assertFalse(deleted_signpost_plan.is_active)
        self.assertEqual(deleted_signpost_plan.deleted_by, self.user)
        self.assertTrue(deleted_signpost_plan.deleted_at)

    def test_get_deleted_signpost_plan_returns_not_found(self):
        signpost_plan = self.__create_test_signpost_plan()
        response = self.client.delete(
            reverse("v1:signpostplan-detail", kwargs={"pk": signpost_plan.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get(
            reverse("v1:signpostplan-detail", kwargs={"pk": signpost_plan.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def __create_test_signpost_plan(self):
        return SignpostPlan.objects.create(
            device_type=self.test_device_type,
            location=self.test_point,
            lifecycle=self.test_lifecycle,
            owner=self.test_owner,
            created_by=self.user,
            updated_by=self.user,
        )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    point_location_test_data,
)
def test_filter_signpost_reals_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    signpost_real = get_signpost_real(location)
    response = api_client.get(reverse("v1:signpostreal-list"), {"location": location_query.ewkt})

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == expected

    if expected == 1:
        data = response.data.get("results")[0]
        assert str(signpost_real.id) == data.get("id")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    point_location_error_test_data,
)
def test_filter_error_signpost_reals_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    get_signpost_real(location)
    response = api_client.get(reverse("v1:signpostreal-list"), {"location": location_query})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data.get("location")[0] == expected


@pytest.mark.parametrize(
    "field_name,value,second_value",
    (
        ("condition", Condition.VERY_GOOD, Condition.AVERAGE),
        ("installation_status", InstallationStatus.IN_USE, InstallationStatus.COVERED),
        ("lane_number", LaneNumber.ADDITIONAL_LEFT_1, LaneNumber.ADDITIONAL_LEFT_2),
        ("lane_type", LaneType.HEAVY, LaneType.BIKE),
        ("lifecycle", Lifecycle.ACTIVE, Lifecycle.TEMPORARILY_ACTIVE),
        ("location_specifier", LocationSpecifier.ABOVE, LocationSpecifier.VERTICAL),
        ("reflection_class", Reflection.R3, Reflection.R1),
        ("size", Size.LARGE, Size.SMALL),
    ),
)
@pytest.mark.django_db
def test__signpost_reals_filtering__list(field_name, value, second_value):
    do_filtering_test(
        SignpostRealFactory,
        "v1:signpostreal-list",
        field_name,
        value,
        second_value,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("target_model", (None, DeviceTypeTargetModel.SIGNPOST))
def test__signpost_real__valid_device_type(target_model):
    """
    Ensure that device types with supported target_model value are allowed.
    """
    client = get_api_client(user=get_user(admin=True))
    signpost_real = get_signpost_real()
    device_type = TrafficControlDeviceTypeFactory(code="123", description="test", target_model=target_model, value="15")
    data = {"device_type": device_type.id}

    response = client.patch(
        reverse("v1:signpostreal-detail", kwargs={"pk": signpost_real.pk}),
        data,
        format="json",
    )

    signpost_real.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert signpost_real.device_type == device_type
    assert signpost_real.value == Decimal("15")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "target_model",
    (
        DeviceTypeTargetModel.BARRIER,
        DeviceTypeTargetModel.ROAD_MARKING,
        DeviceTypeTargetModel.TRAFFIC_LIGHT,
        DeviceTypeTargetModel.TRAFFIC_SIGN,
    ),
)
def test__signpost_real__invalid_device_type(target_model):
    """
    Ensure that device types with unsupported target_model value are not allowed.
    """
    client = get_api_client(user=get_user(admin=True))
    signpost_real = get_signpost_real()
    device_type = TrafficControlDeviceTypeFactory(code="123", description="test", target_model=target_model)
    data = {"device_type": device_type.id}

    response = client.patch(
        reverse("v1:signpostreal-detail", kwargs={"pk": signpost_real.pk}),
        data,
        format="json",
    )

    signpost_real.refresh_from_db()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert signpost_real.device_type != device_type


@pytest.mark.django_db
def test__signpost_real__create_with_invalid_geometry():
    data = {
        "location": illegal_test_point.ewkt,
        "owner": OwnerFactory().pk,
    }
    do_illegal_geometry_test(
        "v1:signpostreal-list",
        data,
        [f"Geometry for signpostreal {illegal_test_point.ewkt} is not legal"],
    )


class SignPostRealTests(TrafficControlAPIBaseTestCase):
    def test_get_all_signpost_reals(self):
        """
        Ensure we can get all sign post real objects.
        """
        plan = PlanFactory.create(decision_id="TEST-DECISION-ID")

        count = 3
        for i in range(count):
            spp = SignpostPlanFactory(plan=plan)
            self.__create_test_signpost_real(signpost_plan=spp)
        response = self.client.get(reverse("v1:signpostreal-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

        results = response.data.get("results")
        for result in results:
            signpost_real = SignpostReal.objects.get(id=result.get("id"))
            self.assertEqual(result.get("location"), signpost_real.location.ewkt)
            self.assertEqual(result.get("plan_decision_id"), "TEST-DECISION-ID")

    def test_get_all_signpost_reals__geojson(self):
        """
        Ensure we can get all sign post real objects with GeoJSON location.
        """
        plan = PlanFactory.create(decision_id="TEST-DECISION-ID")

        count = 3
        for i in range(count):
            spp = SignpostPlanFactory(plan=plan)
            self.__create_test_signpost_real(signpost_plan=spp)
        response = self.client.get(reverse("v1:signpostreal-list"), data={"geo_format": "geojson"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

        results = response.data.get("results")
        for result in results:
            signpost_real = SignpostReal.objects.get(id=result.get("id"))
            self.assertEqual(result.get("location"), GeoJsonDict(signpost_real.location.json))
            self.assertEqual(result.get("plan_decision_id"), "TEST-DECISION-ID")

    def test_get_signpost_real_detail(self):
        """
        Ensure we can get one signpost real object.
        """
        plan = PlanFactory.create(decision_id="TEST-DECISION-ID")
        spp = get_signpost_plan(plan=plan)
        signpost_real = self.__create_test_signpost_real(signpost_plan=spp)
        operation_1 = add_signpost_real_operation(signpost_real, operation_date=datetime.date(2020, 11, 5))
        operation_2 = add_signpost_real_operation(signpost_real, operation_date=datetime.date(2020, 11, 15))
        operation_3 = add_signpost_real_operation(signpost_real, operation_date=datetime.date(2020, 11, 10))
        response = self.client.get(reverse("v1:signpostreal-detail", kwargs={"pk": signpost_real.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(signpost_real.id))
        self.assertEqual(signpost_real.location.ewkt, response.data.get("location"))
        self.assertEqual(response.data.get("plan_decision_id"), "TEST-DECISION-ID")
        # verify operations are ordered by operation_date
        operation_ids = [operation["id"] for operation in response.data["operations"]]
        self.assertEqual(operation_ids, [operation_1.id, operation_3.id, operation_2.id])

    def test_get_signpost_real_detail__geojson(self):
        """
        Ensure we can get one signpost real object with GeoJSON location.
        """
        plan = PlanFactory.create(decision_id="TEST-DECISION-ID")
        spp = get_signpost_plan(plan=plan)
        signpost_real = self.__create_test_signpost_real(signpost_plan=spp)
        response = self.client.get(
            reverse("v1:signpostreal-detail", kwargs={"pk": signpost_real.id}),
            data={"geo_format": "geojson"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(signpost_real.id))
        signpost_real_geojson = GeoJsonDict(signpost_real.location.json)
        self.assertEqual(signpost_real_geojson, response.data.get("location"))
        self.assertEqual(response.data.get("plan_decision_id"), "TEST-DECISION-ID")

    def test_create_signpost_real(self):
        """
        Ensure we can create a new signpost real object.
        """
        data = {
            "device_type": self.test_device_type.id,
            "location": self.test_point.ewkt,
            "installation_date": "2020-01-02",
            "lifecycle": self.test_lifecycle.value,
            "owner": self.test_owner.pk,
        }
        response = self.client.post(reverse("v1:signpostreal-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SignpostReal.objects.count(), 1)
        self.assertEqual(response.data.get("location"), data["location"])
        signpost_real = SignpostReal.objects.first()
        self.assertEqual(signpost_real.device_type.id, data["device_type"])
        self.assertEqual(signpost_real.location.ewkt, data["location"])
        self.assertEqual(
            signpost_real.installation_date.strftime("%Y-%m-%d"),
            data["installation_date"],
        )
        self.assertEqual(signpost_real.lifecycle.value, data["lifecycle"])

    def test_create_signpost_real_with_existing_plan(self):
        spr_plan = SignpostPlanFactory()
        SignpostRealFactory(signpost_plan=spr_plan)
        data = {
            "device_type": self.test_device_type.id,
            "location": self.test_point.ewkt,
            "installation_date": "2020-01-02",
            "lifecycle": self.test_lifecycle.value,
            "owner": self.test_owner.pk,
            "signpost_plan": spr_plan.id,
        }
        response = self.client.post(reverse("v1:signpostreal-list"), data, format="json")
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(SignpostReal.objects.count(), 1)
        assert "duplicate key value violates unique constraint" in response_data["detail"]
        assert "traffic_control_signpostreal_unique_signpost_plan_id" in response_data["detail"]

    def test_update_signpost_real(self):
        """
        Ensure we can update existing signpost real object.
        """
        signpost_real = self.__create_test_signpost_real()
        data = {
            "device_type": self.test_device_type_2.id,
            "location": self.test_point.ewkt,
            "installation_date": "2020-01-03",
            "lifecycle": self.test_lifecycle_2.value,
            "owner": self.test_owner.pk,
        }
        response = self.client.put(
            reverse("v1:signpostreal-detail", kwargs={"pk": signpost_real.id}),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(SignpostReal.objects.count(), 1)
        signpost_real = SignpostReal.objects.first()
        self.assertEqual(signpost_real.device_type.id, data["device_type"])
        self.assertEqual(signpost_real.location.ewkt, data["location"])
        self.assertEqual(
            signpost_real.installation_date.strftime("%Y-%m-%d"),
            data["installation_date"],
        )
        self.assertEqual(signpost_real.lifecycle.value, data["lifecycle"])

    def test_delete_signpost_real_detail(self):
        """
        Ensure we can soft-delete one signpost real object.
        """
        signpost_real = self.__create_test_signpost_real()
        response = self.client.delete(
            reverse("v1:signpostreal-detail", kwargs={"pk": signpost_real.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(SignpostReal.objects.count(), 1)
        deleted_signpost_real = SignpostReal.objects.get(id=str(signpost_real.id))
        self.assertEqual(deleted_signpost_real.id, signpost_real.id)
        self.assertFalse(deleted_signpost_real.is_active)
        self.assertEqual(deleted_signpost_real.deleted_by, self.user)
        self.assertTrue(deleted_signpost_real.deleted_at)

    def test_get_deleted_signpost_real_returns_not_found(self):
        signpost_real = self.__create_test_signpost_real()
        response = self.client.delete(
            reverse("v1:signpostreal-detail", kwargs={"pk": signpost_real.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get(
            reverse("v1:signpostreal-detail", kwargs={"pk": signpost_real.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_operation_signpost_real(self):
        signpost_real = self.__create_test_signpost_real()
        operation_type = get_operation_type()
        data = {
            "operation_date": "2020-01-01",
            "operation_type_id": operation_type.pk,
        }
        url = reverse("signpost-real-operations-list", kwargs={"signpost_real_pk": signpost_real.pk})
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(signpost_real.operations.all().count(), 1)

    def test_update_operation_signpost_real(self):
        signpost_real = self.__create_test_signpost_real()
        operation_type = get_operation_type()
        operation = add_signpost_real_operation(
            signpost_real=signpost_real, operation_type=operation_type, operation_date=datetime.date(2020, 1, 1)
        )
        data = {
            "operation_date": "2020-02-01",
            "operation_type_id": operation_type.pk,
        }
        url = reverse(
            "signpost-real-operations-detail",
            kwargs={"signpost_real_pk": signpost_real.pk, "pk": operation.pk},
        )
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(signpost_real.operations.all().count(), 1)
        self.assertEqual(signpost_real.operations.all().first().operation_date, datetime.date(2020, 2, 1))

    def __create_test_signpost_real(self, signpost_plan=None):
        signpost_plan = (
            SignpostPlan.objects.create(
                device_type=self.test_device_type,
                location=self.test_point,
                lifecycle=self.test_lifecycle,
                owner=self.test_owner,
                created_by=self.user,
                updated_by=self.user,
            )
            if not signpost_plan
            else signpost_plan
        )
        return SignpostReal.objects.create(
            signpost_plan=signpost_plan,
            device_type=self.test_device_type,
            location=self.test_point,
            installation_date=datetime.datetime.strptime("01012020", "%d%m%Y").date(),
            lifecycle=self.test_lifecycle,
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
def test__signpost_plan__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    signpost = get_signpost_plan(location=f"SRID=3879;POINT Z ({MIN_X+1} {MIN_Y+1} 0)")
    kwargs = {"pk": signpost.pk} if view_type == "detail" else None
    resource_path = reverse(f"v1:signpostplan-{view_type}", kwargs=kwargs)
    data = {
        "location": f"SRID=3879;POINT Z ({MIN_X+2} {MIN_Y+2} 0)",
        "device_type": str(TrafficControlDeviceTypeFactory().id),
        "owner": str(get_owner().id),
    }

    response = client.generic(method, resource_path, json.dumps(data), content_type="application/json")

    assert SignpostPlan.objects.count() == 1
    assert SignpostPlan.objects.first().is_active
    assert SignpostPlan.objects.first().location == f"SRID=3879;POINT Z ({MIN_X+1} {MIN_Y+1} 0)"
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
def test__signpost_real__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    signpost = get_signpost_real(location=f"SRID=3879;POINT Z ({MIN_X+1} {MIN_Y+1} 0)")
    kwargs = {"pk": signpost.pk} if view_type == "detail" else None
    resource_path = reverse(f"v1:signpostreal-{view_type}", kwargs=kwargs)
    data = {
        "location": f"SRID=3879;POINT Z ({MIN_X+2} {MIN_Y+2} 0)",
        "device_type": str(TrafficControlDeviceTypeFactory().id),
        "owner": str(get_owner().id),
    }

    response = client.generic(method, resource_path, json.dumps(data), content_type="application/json")

    assert SignpostReal.objects.count() == 1
    assert SignpostReal.objects.first().is_active
    assert SignpostReal.objects.first().location == f"SRID=3879;POINT Z ({MIN_X+1} {MIN_Y+1} 0)"
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
def test__signpost_real_operation__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    signpost = get_signpost_real()
    operation_type = get_operation_type()
    operation = add_signpost_real_operation(
        signpost_real=signpost,
        operation_type=operation_type,
        operation_date=datetime.date(2020, 1, 1),
    )

    data = {"operation_date": "2020-02-01", "operation_type_id": operation_type.pk}

    kwargs = {"signpost_real_pk": signpost.pk}
    if view_type == "detail":
        kwargs["pk"] = operation.pk

    resource_path = reverse(f"signpost-real-operations-{view_type}", kwargs=kwargs)

    response = client.generic(method, resource_path, data)

    assert signpost.operations.all().count() == 1
    assert signpost.operations.all().first().operation_date == datetime.date(2020, 1, 1)
    assert response.status_code == expected_status

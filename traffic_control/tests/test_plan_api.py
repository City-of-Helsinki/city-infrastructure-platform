import json
from datetime import datetime

import pytest
from django.conf import settings
from django.contrib.gis.geos import MultiPolygon
from django.urls import reverse
from rest_framework import status
from rest_framework_gis.fields import GeoJsonDict

from traffic_control.models import Plan
from traffic_control.tests.factories import get_api_client, get_plan, get_user
from traffic_control.tests.test_base_api import test_multi_polygon, test_polygon, test_polygon_2, test_polygon_3


@pytest.mark.django_db
def test_plan_list():
    api_client = get_api_client()
    count = 3
    p1 = MultiPolygon(test_polygon, srid=settings.SRID)
    p2 = MultiPolygon(test_polygon_2, srid=settings.SRID)
    p3 = test_multi_polygon

    for p in [p1, p2, p3]:
        get_plan(location=p)

    response = api_client.get(reverse("v1:plan-list"))

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == count


@pytest.mark.django_db
def test_plan_detail():
    api_client = get_api_client()
    plan = get_plan()

    response = api_client.get(reverse("v1:plan-detail", kwargs={"pk": plan.pk}))

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("id") == str(plan.pk)
    assert response.data.get("location") == plan.location.ewkt


@pytest.mark.django_db
def test_plan_detail_geojson():
    api_client = get_api_client()
    plan = get_plan()

    response = api_client.get(
        reverse("v1:plan-detail", kwargs={"pk": plan.pk}),
        data={"geo_format": "geojson"},
    )

    plan_geojson = GeoJsonDict(plan.location.json)
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("id") == str(plan.pk)
    assert response.data.get("location") == plan_geojson


@pytest.mark.django_db
def test_plan_create():
    user = get_user(admin=True)
    api_client = get_api_client(user=user)
    location = test_multi_polygon.ewkt

    response = api_client.post(
        reverse("v1:plan-list"),
        data={
            "name": "Test plan",
            "plan_number": "2020_1",
            "location": location,
            "diary_number": "HEL 2023-000001",
            "drawing_numbers": ["1234"],
            "created_by": user.pk,
            "updated_by": user.pk,
        },
        format="json",
    )

    plan = Plan.objects.first()
    assert response.status_code == status.HTTP_201_CREATED
    assert Plan.objects.count() == 1
    assert plan.location.ewkt == location
    assert plan.name == "Test plan"
    assert plan.plan_number == "2020_1"
    assert plan.created_by == user
    assert plan.updated_by == user
    assert plan.diary_number == "HEL 2023-000001"
    assert plan.drawing_numbers == ["1234"]
    assert response.data.get("derive_location") is False


@pytest.mark.django_db
def test_plan_delete():
    user = get_user(admin=True)
    api_client = get_api_client(user=user)
    plan = get_plan()

    response = api_client.delete(reverse("v1:plan-detail", kwargs={"pk": plan.pk}))

    plan.refresh_from_db()
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert Plan.objects.active().count() == 0
    assert not plan.is_active
    assert plan.deleted_by == user
    assert plan.deleted_at
    assert isinstance(plan.deleted_at, datetime)


@pytest.mark.django_db
def test_plan_get_deleted():
    user = get_user(admin=True)
    api_client = get_api_client(user=user)
    plan = get_plan()

    response = api_client.delete(reverse("v1:plan-detail", kwargs={"pk": plan.pk}))
    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = api_client.get(reverse("v1:plan-detail", kwargs={"pk": plan.pk}))
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    (
        (test_multi_polygon, test_polygon, 1),
        (test_multi_polygon, test_polygon_2, 1),
        (test_multi_polygon, test_polygon_3, 0),
        (MultiPolygon(test_polygon, srid=settings.SRID), test_polygon_2, 0),
        (MultiPolygon(test_polygon, srid=settings.SRID), test_polygon_3, 0),
        (MultiPolygon(test_polygon_2, srid=settings.SRID), test_polygon, 0),
        (MultiPolygon(test_polygon_2, srid=settings.SRID), test_polygon_3, 0),
        (MultiPolygon(test_polygon_3, srid=settings.SRID), test_polygon, 0),
        (MultiPolygon(test_polygon_3, srid=settings.SRID), test_polygon_2, 0),
    ),
)
def test_plan_filter_location(location, location_query, expected):
    api_client = get_api_client()
    plan = get_plan(location=location)

    response = api_client.get(reverse("v1:plan-list"), {"location": location_query.ewkt})

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == expected
    if expected == 1:
        data = response.data.get("results")[0]
        assert str(plan.id) == data.get("id")


@pytest.mark.django_db
def test_plan_list_filter_drawing_number():
    api_client = get_api_client()

    p1 = get_plan(name="Plan 1")
    p1.drawing_numbers = ["10"]
    p1.save()

    p2 = get_plan(name="Plan 2")
    p2.drawing_numbers = ["1010", "123"]
    p2.save()

    get_plan(name="Plan 3")

    # Search a plan with one drawing number
    response = api_client.get(reverse("v1:plan-list"), {"drawing_number": "10"})
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == 1
    assert response.data.get("results")[0].get("id") == str(p1.id)

    # Search a plan with multiple drawing numbers
    response = api_client.get(reverse("v1:plan-list"), {"drawing_number": "1010"})
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == 1
    assert response.data.get("results")[0].get("id") == str(p2.id)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("valid", "input_drawing_numbers", "db_drawing_numbers"),
    (
        (True, [], []),
        (True, ["123"], ["123"]),
        (True, ["456", "123"], ["123", "456"]),
        (False, [""], None),
        (False, ["123", ""], None),
        (False, ["123,456"], None),
        (False, ['"123'], None),
    ),
)
def test_plan_create_validate_drawing_number(valid, input_drawing_numbers, db_drawing_numbers):
    user = get_user(admin=True)
    api_client = get_api_client(user=user)
    location = test_multi_polygon.ewkt

    response = api_client.post(
        reverse("v1:plan-list"),
        data={
            "name": "Test plan",
            "plan_number": "2020_1",
            "location": location,
            "drawing_numbers": input_drawing_numbers,
        },
        format="json",
    )

    if valid:
        assert response.status_code == status.HTTP_201_CREATED
        assert Plan.objects.count() == 1
        assert Plan.objects.first().drawing_numbers == db_drawing_numbers
    else:
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Plan.objects.count() == 0


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
def test__plan__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    plan = get_plan(name="Plan 1")
    kwargs = {"pk": plan.pk} if view_type == "detail" else None
    resource_path = reverse(f"v1:plan-{view_type}", kwargs=kwargs)
    data = {"name": "Plan 2", "plan_number": "123"}

    response = client.generic(method, resource_path, json.dumps(data), content_type="application/json")

    assert Plan.objects.count() == 1
    assert Plan.objects.first().is_active
    assert Plan.objects.first().name == "Plan 1"
    assert response.status_code == expected_status

from datetime import datetime

import pytest
from django.conf import settings
from django.contrib.gis.geos import MultiPolygon
from django.urls import reverse
from rest_framework import status
from rest_framework_gis.fields import GeoJsonDict

from ..models import Plan
from .factories import get_api_client, get_plan, get_user
from .test_base_api import test_multi_polygon, test_polygon, test_polygon_2, test_polygon_3


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
            "planner": "Planner",
            "decision_maker": "Decision Maker",
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
    assert plan.planner == "Planner"
    assert plan.decision_maker == "Decision Maker"


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

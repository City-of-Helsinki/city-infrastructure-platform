from unittest.mock import MagicMock

import pytest
from django.conf import settings
from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.test import RequestFactory

from ..models import OperationalArea
from ..permissions import IsAdminUserOrReadOnly, ObjectInsideOperationalAreaOrAnonReadOnly
from .factories import get_barrier_real, get_user
from .test_base_api import test_polygon

mock_view = MagicMock()
mock_user = MagicMock()


@pytest.mark.parametrize(
    "method,is_staff,expected",
    [
        ["get", False, True],
        ["get", True, True],
        ["head", False, True],
        ["head", True, True],
        ["options", False, True],
        ["options", True, True],
        ["post", False, False],
        ["post", True, True],
        ["patch", False, False],
        ["patch", True, True],
        ["put", False, False],
        ["put", True, True],
    ],
)
def test_is_admin_user_or_read_only(method, is_staff, expected):
    request = RequestFactory().generic(method=method, path="/")
    request.user = mock_user
    request.user.is_staff = is_staff
    assert IsAdminUserOrReadOnly().has_permission(request, mock_view) == expected


@pytest.mark.parametrize("method", ["get", "head", "options", "post", "patch", "put"])
@pytest.mark.django_db
def test__operational_area_permission__point_in_area(method):
    user = get_user()
    operational_area = OperationalArea.objects.create(
        name="Test operational area",
        location=MultiPolygon(test_polygon, srid=settings.SRID),
    )
    user.operational_areas.add(operational_area)
    request = RequestFactory().generic(method=method, path="/")
    request.user = user
    barrier_real = get_barrier_real(location=Point(20.0, 20.0, 0, srid=settings.SRID))

    has_permission = ObjectInsideOperationalAreaOrAnonReadOnly().has_object_permission(request, mock_view, barrier_real)

    assert has_permission


@pytest.mark.parametrize(
    "method,expected",
    [
        ["get", True],
        ["head", True],
        ["options", True],
        ["post", False],
        ["patch", False],
        ["put", False],
    ],
)
@pytest.mark.django_db
def test__operational_area_permission__point_not_in_area(method, expected):
    user = get_user()
    operational_area = OperationalArea.objects.create(
        name="Test operational area",
        location=MultiPolygon(test_polygon, srid=settings.SRID),
    )
    user.operational_areas.add(operational_area)
    request = RequestFactory().generic(method=method, path="/")
    request.user = user
    barrier_real = get_barrier_real(location=Point(-20.0, -20.0, 0, srid=settings.SRID))

    has_permission = ObjectInsideOperationalAreaOrAnonReadOnly().has_object_permission(request, mock_view, barrier_real)

    assert has_permission == expected


@pytest.mark.parametrize("method", ["get", "head", "options", "post", "patch", "put"])
@pytest.mark.django_db
def test__operational_area_permission__polygon_in_area(method):
    user = get_user()
    operational_area = OperationalArea.objects.create(
        name="Test operational area",
        location=MultiPolygon(test_polygon, srid=settings.SRID),
    )
    user.operational_areas.add(operational_area)
    request = RequestFactory().generic(method=method, path="/")
    request.user = user
    barrier_real = get_barrier_real(
        location=Polygon(
            (
                (10.0, 10.0, 0),
                (10.0, 20.0, 0),
                (20.0, 20.0, 0),
                (20.0, 10.0, 0),
                (10.0, 10.0, 0),
            ),
            srid=settings.SRID,
        )
    )

    has_permission = ObjectInsideOperationalAreaOrAnonReadOnly().has_object_permission(request, mock_view, barrier_real)

    assert has_permission


@pytest.mark.parametrize(
    "method,expected",
    [
        ["get", True],
        ["head", True],
        ["options", True],
        ["post", False],
        ["patch", False],
        ["put", False],
    ],
)
@pytest.mark.django_db
def test__operational_area_permission__polygon_partially_not_in_area(method, expected):
    user = get_user()
    operational_area = OperationalArea.objects.create(
        name="Test operational area",
        location=MultiPolygon(test_polygon, srid=settings.SRID),
    )
    user.operational_areas.add(operational_area)
    request = RequestFactory().generic(method=method, path="/")
    request.user = user
    barrier_real = get_barrier_real(
        location=Polygon(
            (
                (10.0, 10.0, 0),
                (10.0, -10.0, 0),
                (-10.0, -10.0, 0),
                (-10.0, 10.0, 0),
                (10.0, 10.0, 0),
            ),
            srid=settings.SRID,
        )
    )

    has_permission = ObjectInsideOperationalAreaOrAnonReadOnly().has_object_permission(request, mock_view, barrier_real)

    assert has_permission == expected


@pytest.mark.parametrize(
    "method,expected",
    [
        ["get", True],
        ["head", True],
        ["options", True],
        ["post", False],
        ["patch", False],
        ["put", False],
    ],
)
@pytest.mark.django_db
def test__operational_area_permission__polygon_not_in_area(method, expected):
    user = get_user()
    operational_area = OperationalArea.objects.create(
        name="Test operational area",
        location=MultiPolygon(test_polygon, srid=settings.SRID),
    )
    user.operational_areas.add(operational_area)
    request = RequestFactory().generic(method=method, path="/")
    request.user = user
    barrier_real = get_barrier_real(
        location=Polygon(
            (
                (-10.0, -10.0, 0),
                (-10.0, -20.0, 0),
                (-20.0, -20.0, 0),
                (-20.0, -10.0, 0),
                (-10.0, -10.0, 0),
            ),
            srid=settings.SRID,
        )
    )

    has_permission = ObjectInsideOperationalAreaOrAnonReadOnly().has_object_permission(request, mock_view, barrier_real)

    assert has_permission == expected

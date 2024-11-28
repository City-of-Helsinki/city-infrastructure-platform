from unittest.mock import MagicMock

import pytest
from django.conf import settings
from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.test import RequestFactory

from traffic_control.models import OperationalArea
from traffic_control.permissions import IsAdminUserOrReadOnly, ObjectInsideOperationalAreaOrAnonReadOnly
from traffic_control.tests.factories import get_barrier_real, get_user
from traffic_control.tests.test_base_api import test_polygon
from traffic_control.tests.utils import MIN_X, MIN_Y

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
    barrier_real = get_barrier_real(location=Point(MIN_X + 20, MIN_Y + 20.0, 0, srid=settings.SRID))

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
    barrier_real = get_barrier_real(location=Point(MIN_X + 100, MIN_Y + 100.0, 0, srid=settings.SRID))

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
                (MIN_X + 10, MIN_Y + 10, 0.0),
                (MIN_X + 10, MIN_Y + 20.0, 0.0),
                (MIN_X + 20.0, MIN_Y + 20.0, 0.0),
                (MIN_X + 20.0, MIN_Y + 10, 0.0),
                (MIN_X + 10, MIN_Y + 10, 0.0),
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
                (MIN_X + 10, MIN_Y + 10, 0.0),
                (MIN_X + 10, MIN_Y + 150.0, 0.0),
                (MIN_X + 150.0, MIN_Y + 150.0, 0.0),
                (MIN_X + 150.0, MIN_Y + 10, 0.0),
                (MIN_X + 10, MIN_Y + 10, 0.0),
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
                (MIN_X + 140.0, MIN_Y + 140.0, 0),
                (MIN_X + 140.0, MIN_Y + 130.0, 0),
                (MIN_X + 130.0, MIN_Y + 130.0, 0),
                (MIN_X + 130.0, MIN_Y + 140.0, 0),
                (MIN_X + 140.0, MIN_Y + 140.0, 0),
            ),
            srid=settings.SRID,
        )
    )

    has_permission = ObjectInsideOperationalAreaOrAnonReadOnly().has_object_permission(request, mock_view, barrier_real)

    assert has_permission == expected

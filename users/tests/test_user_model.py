import pytest
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.gis.geos import MultiPolygon, Point, Polygon

from traffic_control.models import GroupOperationalArea
from traffic_control.tests.factories import get_operational_area, get_user
from traffic_control.tests.utils import MIN_X, MIN_Y

polygon = Polygon(
    (
        (MIN_X + 1, MIN_Y + 1, 0),
        (MIN_X + 1, MIN_Y + 50.0, 0),
        (MIN_X + 50.0, MIN_Y + 50, 0),
        (MIN_X + 50.0, MIN_Y + 1, 0),
        (MIN_X + 1, MIN_Y + 1, 0),
    ),
    srid=settings.SRID,
)
area = MultiPolygon(polygon, srid=settings.SRID)
point_inside_area = Point(MIN_X + 10.0, MIN_Y + 10.0, 0.0, srid=settings.SRID)
point_outside_area = Point(MIN_X + 51.0, MIN_Y + 51.0, 0.0, srid=settings.SRID)


@pytest.mark.parametrize("location,expected", ((point_inside_area, True), (point_outside_area, False)))
@pytest.mark.django_db
def test__user_operational_area__contains_location(location, expected):
    user = get_user()
    oa = get_operational_area(area=area)
    user.operational_areas.add(oa)

    in_area = user.location_is_in_operational_area(location)

    assert in_area == expected


@pytest.mark.parametrize("location", (point_inside_area, point_outside_area))
@pytest.mark.django_db
def test__superuser_operational_area(location):
    user = get_user(admin=True)
    oa = get_operational_area(area=area)
    user.operational_areas.add(oa)

    in_area = user.location_is_in_operational_area(location)

    assert in_area


@pytest.mark.parametrize("location", (point_inside_area, point_outside_area))
@pytest.mark.django_db
def test__user_operational_area__bypass_operational_area(location):
    user = get_user(admin=True)
    user.bypass_operational_area = True
    user.save(update_fields=["bypass_operational_area"])
    oa = get_operational_area(area=area)
    user.operational_areas.add(oa)

    in_area = user.location_is_in_operational_area(location)

    assert in_area


@pytest.mark.parametrize("location,expected", ((point_inside_area, True), (point_outside_area, False)))
@pytest.mark.django_db
def test__user_group_operational_area__contains_location(location, expected):
    user = get_user()
    group = Group.objects.create(name="test group")
    user.groups.add(group)
    oa = get_operational_area(area)
    group_oa = GroupOperationalArea.objects.create(group=group)
    group_oa.areas.add(oa)

    in_area = user.location_is_in_operational_area(location)

    assert in_area == expected

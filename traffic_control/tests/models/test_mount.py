import pytest
from django.contrib.gis.geos import Point

from traffic_control.tests.factories import (
    get_mount_type,
    get_owner,
    get_user,
    MountRealFactory,
    TrafficSignRealFactory,
)
from traffic_control.tests.utils import MIN_X, MIN_Y


@pytest.fixture
def user(db):
    yield get_user()


@pytest.fixture
def owner(db):
    yield get_owner()


@pytest.fixture
def mount_type(db):
    yield get_mount_type(code="LIGHTPOLE", description="Lightpole")


@pytest.fixture
def mount_real(db, settings, mount_type, user):
    yield MountRealFactory(
        location=Point(MIN_X + 2, MIN_Y + 1, 0, srid=settings.SRID),
        mount_type=mount_type,
        owner=get_owner(),
        created_by=user,
        updated_by=user,
    )


@pytest.mark.django_db
def test_ordered_traffic_signs_property_return_ordered_traffic_signs(settings, mount_real, mount_type, owner, user):
    traffic_sign_1 = TrafficSignRealFactory(
        location=Point(MIN_X + 1, MIN_Y + 1, 2, srid=settings.SRID),
        legacy_code="100",
        mount_type=mount_type,
        mount_real=mount_real,
        direction=0,
        created_by=user,
        updated_by=user,
        owner=owner,
    )
    traffic_sign_2 = TrafficSignRealFactory(
        location=Point(MIN_X + 1, MIN_Y + 1, 2.5, srid=settings.SRID),
        legacy_code="100",
        mount_type=mount_type,
        mount_real=mount_real,
        direction=0,
        created_by=user,
        updated_by=user,
        owner=owner,
    )
    traffic_sign_3 = TrafficSignRealFactory(
        location=Point(MIN_X + 1, MIN_Y + 1, 1.8, srid=settings.SRID),
        legacy_code="100",
        mount_type=mount_type,
        mount_real=mount_real,
        direction=0,
        created_by=user,
        updated_by=user,
        owner=owner,
    )
    assert list(mount_real.ordered_traffic_signs) == [traffic_sign_2, traffic_sign_1, traffic_sign_3]

import pytest
from auditlog.models import LogEntry
from django.conf import settings
from django.contrib.auth.models import Group, Permission
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
    assert LogEntry.objects.get_for_object(user).filter(action=LogEntry.Action.CREATE).count() == 1

    oa = get_operational_area(area=area)
    user.operational_areas.add(oa)
    assert LogEntry.objects.get_for_object(user).filter(action=LogEntry.Action.UPDATE).count() == 1

    in_area = user.location_is_in_operational_area(location)
    assert in_area == expected


@pytest.mark.parametrize("location", (point_inside_area, point_outside_area))
@pytest.mark.django_db
def test__superuser_operational_area(location):
    user = get_user(admin=True)
    assert LogEntry.objects.get_for_object(user).filter(action=LogEntry.Action.CREATE).count() == 1

    oa = get_operational_area(area=area)
    user.operational_areas.add(oa)
    assert LogEntry.objects.get_for_object(user).filter(action=LogEntry.Action.UPDATE).count() == 1

    in_area = user.location_is_in_operational_area(location)
    assert in_area


@pytest.mark.parametrize("location", (point_inside_area, point_outside_area))
@pytest.mark.django_db
def test__user_operational_area__bypass_operational_area(location):
    user = get_user(admin=True)
    assert LogEntry.objects.get_for_object(user).filter(action=LogEntry.Action.CREATE).count() == 1

    user.bypass_operational_area = True
    user.save(update_fields=["bypass_operational_area"])
    oa = get_operational_area(area=area)
    assert LogEntry.objects.get_for_object(user).filter(action=LogEntry.Action.UPDATE).count() == 1
    user.operational_areas.add(oa)
    assert LogEntry.objects.get_for_object(user).filter(action=LogEntry.Action.UPDATE).count() == 2

    in_area = user.location_is_in_operational_area(location)
    assert in_area


@pytest.mark.parametrize("location,expected", ((point_inside_area, True), (point_outside_area, False)))
@pytest.mark.django_db
def test__user_group_operational_area__contains_location(location, expected):
    user = get_user()
    assert LogEntry.objects.get_for_object(user).filter(action=LogEntry.Action.CREATE).count() == 1

    group = Group.objects.create(name="test group")
    user.groups.add(group)
    assert LogEntry.objects.get_for_object(user).filter(action=LogEntry.Action.UPDATE).count() == 1

    oa = get_operational_area(area)
    group_oa = GroupOperationalArea.objects.create(group=group)
    group_oa.areas.add(oa)

    in_area = user.location_is_in_operational_area(location)
    assert in_area == expected


@pytest.mark.django_db
def test__user_permissions_changed_to_auditlog():
    user = get_user()
    assert LogEntry.objects.get_for_object(user).filter(action=LogEntry.Action.CREATE).count() == 1

    permission = Permission.objects.get(codename="change_user")
    user.user_permissions.add(permission)
    assert LogEntry.objects.get_for_object(user).filter(action=LogEntry.Action.UPDATE).count() == 1


# Authentication type tests


@pytest.mark.django_db
def test__user_is_local_user__with_password():
    """Test that user with usable password is identified as local user."""
    user = get_user()
    user.set_password("SecureP@ssw0rd123")
    user.save()
    assert user.is_local_user() is True


@pytest.mark.django_db
def test__user_is_local_user__without_password():
    """Test that user without usable password is not identified as local user."""
    user = get_user()
    user.set_unusable_password()
    user.save()
    assert user.is_local_user() is False


@pytest.mark.django_db
def test__user_is_oidc_user__with_social_auth():
    """Test that user with Tunnistamo social auth is identified as OIDC user."""
    from social_django.models import UserSocialAuth

    user = get_user()
    UserSocialAuth.objects.create(user=user, provider="tunnistamo", uid="test-uid-123")
    assert user.is_oidc_user() is True


@pytest.mark.django_db
def test__user_is_oidc_user__without_social_auth():
    """Test that user without social auth is not identified as OIDC user."""
    user = get_user()
    assert user.is_oidc_user() is False


@pytest.mark.django_db
def test__user_is_oidc_user__with_different_provider():
    """Test that user with non-Tunnistamo social auth is not identified as OIDC user."""
    from social_django.models import UserSocialAuth

    user = get_user()
    UserSocialAuth.objects.create(user=user, provider="other-provider", uid="test-uid-456")
    assert user.is_oidc_user() is False


@pytest.mark.django_db
def test__user_get_auth_type__password_only():
    """Test get_auth_type returns correct values for password-only user."""
    user = get_user()
    user.set_password("SecureP@ssw0rd123")
    user.save()
    text, color = user.get_auth_type()
    assert text == "Local"
    assert color == "red"


@pytest.mark.django_db
def test__user_get_auth_type__oidc_only():
    """Test get_auth_type returns correct values for OIDC-only user."""
    from social_django.models import UserSocialAuth

    user = get_user()
    user.set_unusable_password()
    user.save()
    UserSocialAuth.objects.create(user=user, provider="tunnistamo", uid="test-uid-789")
    text, color = user.get_auth_type()
    assert text == "Azure AD"
    assert color == "green"


@pytest.mark.django_db
def test__user_get_auth_type__both():
    """Test get_auth_type returns correct values for user with both auth methods."""
    from social_django.models import UserSocialAuth

    user = get_user()
    user.set_password("SecureP@ssw0rd123")
    user.save()
    UserSocialAuth.objects.create(user=user, provider="tunnistamo", uid="test-uid-101112")
    text, color = user.get_auth_type()
    assert text == "Both"
    assert color == "chocolate"


@pytest.mark.django_db
def test__user_get_auth_type__none():
    """Test get_auth_type returns correct values for user with no auth methods."""
    user = get_user()
    user.set_unusable_password()
    user.save()
    text, color = user.get_auth_type()
    assert text == "None"
    assert color is None

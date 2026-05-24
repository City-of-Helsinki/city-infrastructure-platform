"""Tests for create_testdata_reals management command."""
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from traffic_control.enums import DeviceTypeTargetModel, Lifecycle
from traffic_control.management.commands.create_testdata_reals import (
    HELSINKI_CENTER_X,
    HELSINKI_CENTER_Y,
    LOCATION_OFFSET_STEP,
)
from traffic_control.models.additional_sign import AdditionalSignReal
from traffic_control.models.common import Owner, TrafficControlDeviceType
from traffic_control.models.mount import LocationSpecifier as MountLocationSpecifier, MountReal
from traffic_control.models.traffic_sign import LocationSpecifier as SignLocationSpecifier, TrafficSignReal
from traffic_control.tests.factories import MountTypeFactory, TrafficControlDeviceTypeFactory


@pytest.fixture
def sign_device_type(db) -> TrafficControlDeviceType:
    """Create a TrafficControlDeviceType with target_model=TRAFFIC_SIGN.

    Args:
        db: pytest-django database fixture.

    Returns:
        TrafficControlDeviceType: A traffic sign device type instance.
    """
    return TrafficControlDeviceTypeFactory(target_model=DeviceTypeTargetModel.TRAFFIC_SIGN)


@pytest.fixture
def additional_sign_device_type(db) -> TrafficControlDeviceType:
    """Create a TrafficControlDeviceType with target_model=ADDITIONAL_SIGN.

    Args:
        db: pytest-django database fixture.

    Returns:
        TrafficControlDeviceType: An additional sign device type instance.
    """
    return TrafficControlDeviceTypeFactory(target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN)


@pytest.fixture
def mount_type(db):
    """Create a MountType.

    Args:
        db: pytest-django database fixture.

    Returns:
        MountType: A mount type instance.
    """
    return MountTypeFactory()


@pytest.fixture
def prerequisites(mount_type, sign_device_type, additional_sign_device_type):
    """Bundle all DB prerequisites needed to run the command.

    Args:
        mount_type: MountType fixture.
        sign_device_type: Traffic sign device type fixture.
        additional_sign_device_type: Additional sign device type fixture.

    Returns:
        dict: Mapping of prerequisite names to instances.
    """
    return {
        "mount_type": mount_type,
        "sign_device_type": sign_device_type,
        "additional_sign_device_type": additional_sign_device_type,
    }


@pytest.mark.django_db
def test_creates_expected_number_of_triplets(prerequisites):
    """Command creates the correct count of MountReal, TrafficSignReal and AdditionalSignReal objects.

    Args:
        prerequisites: DB prerequisites fixture.
    """
    call_command("create_testdata_reals", source_name="test", count=3)

    assert MountReal.objects.count() == 3
    assert TrafficSignReal.objects.count() == 3
    assert AdditionalSignReal.objects.count() == 3


@pytest.mark.django_db
def test_default_count_is_five(prerequisites):
    """Command creates 5 triplets when --count is not provided.

    Args:
        prerequisites: DB prerequisites fixture.
    """
    call_command("create_testdata_reals", source_name="test")

    assert MountReal.objects.count() == 5
    assert TrafficSignReal.objects.count() == 5
    assert AdditionalSignReal.objects.count() == 5


@pytest.mark.django_db
def test_objects_are_linked_correctly(prerequisites):
    """Each AdditionalSignReal is linked to the correct TrafficSignReal and MountReal.

    Args:
        prerequisites: DB prerequisites fixture.
    """
    call_command("create_testdata_reals", source_name="test", count=2)

    for additional_sign in AdditionalSignReal.objects.all():
        assert additional_sign.mount_real is not None
        assert additional_sign.parent is not None
        assert additional_sign.parent.mount_real == additional_sign.mount_real


@pytest.mark.django_db
def test_source_name_is_set_directly(prerequisites):
    """All objects carry the exact source_name value passed to the command.

    Args:
        prerequisites: DB prerequisites fixture.
    """
    source_name = "my_source"
    call_command("create_testdata_reals", source_name=source_name, count=2)

    assert MountReal.objects.filter(source_name=source_name).count() == 2
    assert TrafficSignReal.objects.filter(source_name=source_name).count() == 2
    assert AdditionalSignReal.objects.filter(source_name=source_name).count() == 2


@pytest.mark.django_db
def test_lifecycles_cycle_across_triplets(prerequisites):
    """Each triplet uses a different lifecycle value, cycling through all Lifecycle values.

    Args:
        prerequisites: DB prerequisites fixture.
    """
    count = len(list(Lifecycle))
    call_command("create_testdata_reals", source_name="test", count=count)

    lifecycles_used = set(MountReal.objects.values_list("lifecycle", flat=True))
    assert lifecycles_used == {lc.value for lc in Lifecycle}


@pytest.mark.django_db
def test_mount_location_specifiers_cycle(prerequisites):
    """MountReal objects use cycling location_specifier values.

    Args:
        prerequisites: DB prerequisites fixture.
    """
    count = len(MountLocationSpecifier)
    call_command("create_testdata_reals", source_name="test", count=count)

    specifiers_used = set(MountReal.objects.values_list("location_specifier", flat=True))
    expected = {s.value for s in MountLocationSpecifier}
    assert specifiers_used == expected


@pytest.mark.django_db
def test_sign_location_specifiers_cycle(prerequisites):
    """TrafficSignReal objects use cycling location_specifier values.

    Args:
        prerequisites: DB prerequisites fixture.
    """
    count = len(SignLocationSpecifier)
    call_command("create_testdata_reals", source_name="test", count=count)

    specifiers_used = set(TrafficSignReal.objects.values_list("location_specifier", flat=True))
    expected = {s.value for s in SignLocationSpecifier}
    assert specifiers_used == expected


@pytest.mark.django_db
def test_owners_are_unique_per_n(prerequisites):
    """Each triplet index gets its own Owner (TestOwner 0, TestOwner 1, ...).

    Args:
        prerequisites: DB prerequisites fixture.
    """
    call_command("create_testdata_reals", source_name="test", count=4)

    owner_names = list(Owner.objects.filter(name_fi__startswith="TestOwner").values_list("name_fi", flat=True))
    assert len(owner_names) == 4
    for n in range(4):
        assert f"TestOwner {n}" in owner_names


@pytest.mark.django_db
def test_repeated_run_reuses_owners(prerequisites):
    """Running the command twice with the same count reuses existing TestOwner objects.

    Args:
        prerequisites: DB prerequisites fixture.
    """
    call_command("create_testdata_reals", source_name="test", count=3)
    first_owner_count = Owner.objects.filter(name_fi__startswith="TestOwner").count()

    call_command("create_testdata_reals", source_name="test", count=3)
    second_owner_count = Owner.objects.filter(name_fi__startswith="TestOwner").count()

    assert first_owner_count == second_owner_count == 3


@pytest.mark.django_db
def test_locations_offset_from_helsinki_centre(prerequisites):
    """Each triplet's location is offset by LOCATION_OFFSET_STEP from the previous one.

    Args:
        prerequisites: DB prerequisites fixture.
    """
    call_command("create_testdata_reals", source_name="test", count=3)

    mounts = list(MountReal.objects.order_by("source_id"))
    # Verify all mounts are distinct and near the Helsinki centre
    locations = [(m.location.x, m.location.y) for m in mounts]
    assert len(set(locations)) == 3

    # Every location must be within count * step of the centre
    for x, y in locations:
        assert abs(x - HELSINKI_CENTER_X) <= 2 * LOCATION_OFFSET_STEP
        assert abs(y - HELSINKI_CENTER_Y) <= 2 * LOCATION_OFFSET_STEP


@pytest.mark.django_db
def test_additional_sign_missing_content_is_true(prerequisites):
    """AdditionalSignReal.missing_content is always True.

    Args:
        prerequisites: DB prerequisites fixture.
    """
    call_command("create_testdata_reals", source_name="test", count=2)

    assert AdditionalSignReal.objects.filter(missing_content=True).count() == 2


@pytest.mark.django_db
def test_correct_device_types_assigned(prerequisites):
    """TrafficSignReal uses the traffic sign device type; AdditionalSignReal uses the additional sign one.

    Args:
        prerequisites: DB prerequisites fixture.
    """
    call_command("create_testdata_reals", source_name="test", count=2)

    for sign in TrafficSignReal.objects.all():
        assert sign.device_type.target_model == DeviceTypeTargetModel.TRAFFIC_SIGN

    for additional_sign in AdditionalSignReal.objects.all():
        assert additional_sign.device_type.target_model == DeviceTypeTargetModel.ADDITIONAL_SIGN


@pytest.mark.django_db
def test_raises_if_no_mount_type(sign_device_type, additional_sign_device_type):
    """Command raises CommandError when no MountType exists in the database.

    Args:
        sign_device_type: Traffic sign device type fixture.
        additional_sign_device_type: Additional sign device type fixture.
    """
    with pytest.raises(CommandError, match="No MountType found"):
        call_command("create_testdata_reals", source_name="test", count=1)


@pytest.mark.django_db
def test_raises_if_no_sign_device_type(mount_type, additional_sign_device_type):
    """Command raises CommandError when no TRAFFIC_SIGN device type exists.

    Args:
        mount_type: MountType fixture.
        additional_sign_device_type: Additional sign device type fixture.
    """
    with pytest.raises(CommandError, match="target_model=TRAFFIC_SIGN"):
        call_command("create_testdata_reals", source_name="test", count=1)


@pytest.mark.django_db
def test_raises_if_no_additional_sign_device_type(mount_type, sign_device_type):
    """Command raises CommandError when no ADDITIONAL_SIGN device type exists.

    Args:
        mount_type: MountType fixture.
        sign_device_type: Traffic sign device type fixture.
    """
    with pytest.raises(CommandError, match="target_model=ADDITIONAL_SIGN"):
        call_command("create_testdata_reals", source_name="test", count=1)


@pytest.mark.django_db
def test_output_contains_created_ids(prerequisites):
    """Command stdout lists the IDs of all created objects.

    Args:
        prerequisites: DB prerequisites fixture.
    """
    out = StringIO()
    call_command("create_testdata_reals", source_name="test", count=2, stdout=out)

    output = out.getvalue()
    for mount in MountReal.objects.all():
        assert str(mount.id) in output
    for sign in TrafficSignReal.objects.all():
        assert str(sign.id) in output
    for additional_sign in AdditionalSignReal.objects.all():
        assert str(additional_sign.id) in output

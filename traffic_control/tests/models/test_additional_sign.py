"""Tests for AdditionalSign model constraints."""
import pytest
from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError

from traffic_control.constants import TICKET_MACHINE_CODES
from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.models import AdditionalSignPlan, AdditionalSignReal
from traffic_control.tests.factories import (
    AdditionalSignPlanFactory,
    AdditionalSignRealFactory,
    get_owner,
    get_user,
    TrafficControlDeviceTypeFactory,
    TrafficSignPlanFactory,
    TrafficSignRealFactory,
)
from traffic_control.tests.utils import MIN_X, MIN_Y


@pytest.fixture
def test_location() -> Point:
    """
    Create a test location point.

    Returns:
        Point: A 3D point for testing.
    """
    return Point(MIN_X + 1, MIN_Y + 1, 10, srid=settings.SRID)


@pytest.fixture
def ticket_machine_device_type(db) -> "TrafficControlDeviceTypeFactory":
    """
    Create a ticket machine device type.

    Args:
        db: pytest-django database fixture.

    Returns:
        TrafficControlDeviceType: A ticket machine device type with code H20.91.
    """
    return TrafficControlDeviceTypeFactory(
        code=TICKET_MACHINE_CODES[0],  # Use H20.91
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
    )


@pytest.fixture
def regular_device_type(db) -> "TrafficControlDeviceTypeFactory":
    """
    Create a regular (non-ticket-machine) additional sign device type.

    Args:
        db: pytest-django database fixture.

    Returns:
        TrafficControlDeviceType: A regular additional sign device type with code H1.
    """
    return TrafficControlDeviceTypeFactory(
        code="H1",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
    )


@pytest.mark.django_db
def test_additional_sign_plan_with_parent_and_regular_device_type_succeeds(
    test_location: Point,
    regular_device_type: "TrafficControlDeviceTypeFactory",
) -> None:
    """
    Test that AdditionalSignPlan with parent and regular device type can be created.

    Args:
        test_location: Test location fixture.
        regular_device_type: Regular device type fixture.
    """
    parent = TrafficSignPlanFactory()
    sign = AdditionalSignPlanFactory(
        parent=parent,
        location=test_location,
        device_type=regular_device_type,
    )
    sign.full_clean()
    assert sign.pk is not None
    assert sign.parent == parent


@pytest.mark.django_db
def test_additional_sign_plan_without_parent_and_ticket_machine_device_type_succeeds(
    test_location: Point,
    ticket_machine_device_type: "TrafficControlDeviceTypeFactory",
) -> None:
    """
    Test that AdditionalSignPlan without parent and ticket machine device type can be created.

    Args:
        test_location: Test location fixture.
        ticket_machine_device_type: Ticket machine device type fixture.
    """
    sign = AdditionalSignPlanFactory(
        parent=None,
        location=test_location,
        device_type=ticket_machine_device_type,
    )
    sign.full_clean()
    assert sign.pk is not None
    assert sign.parent is None


@pytest.mark.django_db
def test_additional_sign_plan_without_parent_and_regular_device_type_fails(
    test_location: Point,
    regular_device_type: "TrafficControlDeviceTypeFactory",
) -> None:
    """
    Test that AdditionalSignPlan without parent and regular device type raises ValidationError.

    Args:
        test_location: Test location fixture.
        regular_device_type: Regular device type fixture.
    """
    sign = AdditionalSignPlan(
        parent=None,
        location=test_location,
        device_type=regular_device_type,
        owner=get_owner(),
        created_by=get_user(),
        updated_by=get_user(),
    )
    with pytest.raises(ValidationError) as exc_info:
        sign.full_clean()

    assert "parent" in exc_info.value.error_dict
    assert exc_info.value.error_dict["parent"][0].code == "parent_required"


@pytest.mark.django_db
def test_additional_sign_real_with_parent_and_regular_device_type_succeeds(
    test_location: Point,
    regular_device_type: "TrafficControlDeviceTypeFactory",
) -> None:
    """
    Test that AdditionalSignReal with parent and regular device type can be created.

    Args:
        test_location: Test location fixture.
        regular_device_type: Regular device type fixture.
    """
    parent = TrafficSignRealFactory()
    sign = AdditionalSignRealFactory(
        parent=parent,
        location=test_location,
        device_type=regular_device_type,
    )
    sign.full_clean()
    assert sign.pk is not None
    assert sign.parent == parent


@pytest.mark.django_db
def test_additional_sign_real_without_parent_and_ticket_machine_device_type_succeeds(
    test_location: Point,
    ticket_machine_device_type: "TrafficControlDeviceTypeFactory",
) -> None:
    """
    Test that AdditionalSignReal without parent and ticket machine device type can be created.

    Args:
        test_location: Test location fixture.
        ticket_machine_device_type: Ticket machine device type fixture.
    """
    sign = AdditionalSignRealFactory(
        parent=None,
        location=test_location,
        device_type=ticket_machine_device_type,
    )
    sign.full_clean()
    assert sign.pk is not None
    assert sign.parent is None


@pytest.mark.django_db
def test_additional_sign_real_without_parent_and_regular_device_type_fails(
    test_location: Point,
    regular_device_type: "TrafficControlDeviceTypeFactory",
) -> None:
    """
    Test that AdditionalSignReal without parent and regular device type raises ValidationError.

    Args:
        test_location: Test location fixture.
        regular_device_type: Regular device type fixture.
    """
    sign = AdditionalSignReal(
        parent=None,
        location=test_location,
        device_type=regular_device_type,
        owner=get_owner(),
        created_by=get_user(),
        updated_by=get_user(),
    )
    with pytest.raises(ValidationError) as exc_info:
        sign.full_clean()

    assert "parent" in exc_info.value.error_dict
    assert exc_info.value.error_dict["parent"][0].code == "parent_required"


@pytest.mark.django_db
def test_all_ticket_machine_codes_allow_null_parent(test_location: Point) -> None:
    """
    Test that all ticket machine codes allow null parent for AdditionalSignPlan.

    Args:
        test_location: Test location fixture.
    """
    for code in TICKET_MACHINE_CODES:
        device_type = TrafficControlDeviceTypeFactory(
            code=code,
            target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        )
        sign = AdditionalSignPlanFactory(
            parent=None,
            location=test_location,
            device_type=device_type,
        )
        sign.full_clean()
        assert sign.pk is not None, f"Failed to create sign with device type {code}"
        assert sign.parent is None

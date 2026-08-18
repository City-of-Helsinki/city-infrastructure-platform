"""Tests for link_additional_sign_parents_by_mount management command."""
from io import StringIO

import pytest
from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.management import call_command

from traffic_control.constants import TICKET_MACHINE_CODES
from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.models import LinkAdditionalSignParentsRunInfo
from traffic_control.tests.factories import (
    AdditionalSignRealFactory,
    MountRealFactory,
    SignpostRealFactory,
    TrafficControlDeviceTypeFactory,
    TrafficSignRealFactory,
)
from traffic_control.tests.utils import MIN_X, MIN_Y


@pytest.fixture
def ticket_machine_device_type(db):
    """Create a ticket machine device type.

    Returns:
        TrafficControlDeviceType: Ticket machine device type with code H20.91
    """
    return TrafficControlDeviceTypeFactory(
        code=TICKET_MACHINE_CODES[0],  # H20.91
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        description="Ticket machine",
    )


@pytest.fixture
def additional_sign_device_type(db):
    """Create an additional sign device type.

    Returns:
        TrafficControlDeviceType: Additional sign device type
    """
    return TrafficControlDeviceTypeFactory(
        code="871",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        description="Additional sign 871",
    )


@pytest.fixture
def traffic_sign_device_type(db):
    """Create a traffic sign device type.

    Returns:
        TrafficControlDeviceType: Traffic sign device type
    """
    return TrafficControlDeviceTypeFactory(
        code="C1",
        target_model=DeviceTypeTargetModel.TRAFFIC_SIGN,
        description="Traffic sign C1",
    )


@pytest.fixture
def signpost_device_type(db):
    """Create a signpost device type.

    Returns:
        TrafficControlDeviceType: Signpost device type
    """
    return TrafficControlDeviceTypeFactory(
        code="F1",
        target_model=DeviceTypeTargetModel.SIGNPOST,
        description="Signpost F1",
    )


@pytest.mark.django_db
class TestLinkAdditionalSignParentsByMountCommand:
    """Tests for the link_additional_sign_parents_by_mount management command."""

    def test_command_dry_run_no_changes(self, additional_sign_device_type, traffic_sign_device_type):
        """Test that dry-run mode doesn't make any changes.

        Args:
            additional_sign_device_type: Additional sign device type fixture
            traffic_sign_device_type: Traffic sign device type fixture
        """
        # Create mount, traffic sign above, and additional sign below
        mount = MountRealFactory()
        TrafficSignRealFactory(
            device_type=traffic_sign_device_type,
            mount_real=mount,
            location=Point(MIN_X + 10.0, MIN_Y + 10.0, 2.0, srid=settings.SRID),
        )
        ads = AdditionalSignRealFactory(
            device_type=additional_sign_device_type,
            mount_real=mount,
            parent=None,
            location=Point(MIN_X + 10.0, MIN_Y + 10.0, 1.0, srid=settings.SRID),
        )

        # Run command in dry-run mode
        out = StringIO()
        call_command("link_additional_sign_parents_by_mount", "--dry-run", stdout=out)

        # Verify no changes were made
        ads.refresh_from_db()
        assert ads.parent is None

        # Verify run info was created and marked as dry-run
        run_info = LinkAdditionalSignParentsRunInfo.objects.latest("started_at")
        assert run_info.dry_run is True
        assert run_info.completed_at is not None
        assert run_info.total_candidates == 1
        assert run_info.successfully_linked == 1

    def test_command_links_additional_sign_to_traffic_sign(self, additional_sign_device_type, traffic_sign_device_type):
        """Test successful linking of additional sign to traffic sign.

        Args:
            additional_sign_device_type: Additional sign device type fixture
            traffic_sign_device_type: Traffic sign device type fixture
        """
        # Create mount, traffic sign above, and additional sign below
        mount = MountRealFactory()
        traffic_sign = TrafficSignRealFactory(
            device_type=traffic_sign_device_type,
            mount_real=mount,
            location=Point(MIN_X + 10.0, MIN_Y + 10.0, 2.0, srid=settings.SRID),
        )
        ads = AdditionalSignRealFactory(
            device_type=additional_sign_device_type,
            mount_real=mount,
            parent=None,
            location=Point(MIN_X + 10.0, MIN_Y + 10.0, 1.0, srid=settings.SRID),
        )

        # Run command
        out = StringIO()
        call_command("link_additional_sign_parents_by_mount", stdout=out)

        # Verify parent was set
        ads.refresh_from_db()
        assert ads.parent == traffic_sign

        # Verify run info was created
        run_info = LinkAdditionalSignParentsRunInfo.objects.latest("started_at")
        assert run_info.dry_run is False
        assert run_info.completed_at is not None
        assert run_info.total_candidates == 1
        assert run_info.successfully_linked == 1
        assert run_info.skipped_no_match == 0
        assert len(run_info.linked_records) == 1
        assert run_info.linked_records[0]["additional_sign_real_id"] == str(ads.id)
        assert run_info.linked_records[0]["traffic_sign_real_id"] == str(traffic_sign.id)

    def test_command_excludes_ticket_machines(self, ticket_machine_device_type, traffic_sign_device_type):
        """Test that ticket machines are excluded from processing.

        Args:
            ticket_machine_device_type: Ticket machine device type fixture
            traffic_sign_device_type: Traffic sign device type fixture
        """
        # Create mount, traffic sign, and ticket machine
        mount = MountRealFactory()
        _traffic_sign = TrafficSignRealFactory(
            device_type=traffic_sign_device_type,
            mount_real=mount,
            location=Point(MIN_X + 10.0, MIN_Y + 10.0, 2.0, srid=settings.SRID),
        )
        ticket_machine = AdditionalSignRealFactory(
            device_type=ticket_machine_device_type,
            mount_real=mount,
            parent=None,
            location=Point(MIN_X + 10.0, MIN_Y + 10.0, 1.0, srid=settings.SRID),
        )

        # Run command
        out = StringIO()
        call_command("link_additional_sign_parents_by_mount", stdout=out)

        # Verify ticket machine parent was NOT set
        ticket_machine.refresh_from_db()
        assert ticket_machine.parent is None

    def test_command_skips_additional_sign_without_mount_real(
        self, additional_sign_device_type, traffic_sign_device_type
    ):
        """Test that additional signs without mount_real are skipped.

        Args:
            additional_sign_device_type: Additional sign device type fixture
            traffic_sign_device_type: Traffic sign device type fixture
        """
        # Create traffic sign with mount
        mount = MountRealFactory()
        TrafficSignRealFactory(
            device_type=traffic_sign_device_type,
            mount_real=mount,
            location=Point(MIN_X + 10.0, MIN_Y + 10.0, 2.0, srid=settings.SRID),
        )

        # Create additional sign without mount_real
        ads = AdditionalSignRealFactory(
            device_type=additional_sign_device_type,
            mount_real=None,
            parent=None,
            location=Point(MIN_X + 10.0, MIN_Y + 10.0, 1.0, srid=settings.SRID),
        )

        # Run command
        out = StringIO()
        call_command("link_additional_sign_parents_by_mount", stdout=out)

        # Verify parent was NOT set
        ads.refresh_from_db()
        assert ads.parent is None

    def test_command_skips_additional_sign_without_matching_traffic_sign(self, additional_sign_device_type):
        """Test handling of additional sign with no matching traffic sign or signpost.

        Args:
            additional_sign_device_type: Additional sign device type fixture
        """
        # Create mount and additional sign, but NO traffic sign or signpost with that mount
        mount = MountRealFactory()
        ads = AdditionalSignRealFactory(
            device_type=additional_sign_device_type,
            mount_real=mount,
            parent=None,
        )

        # Run command
        out = StringIO()
        call_command("link_additional_sign_parents_by_mount", stdout=out)

        # Verify neither parent nor signpost_real was set (no matching devices)
        ads.refresh_from_db()
        assert ads.parent is None
        assert ads.signpost_real is None

        # Verify warning message in output
        output = out.getvalue()
        assert "No TrafficSignReal found" in output or "No active TrafficSignReal" in output
        assert "No SignpostReal found either" in output or "No active SignpostReal" in output

        # Verify run info skipped statistics
        run_info = LinkAdditionalSignParentsRunInfo.objects.latest("started_at")
        assert run_info.successfully_linked == 0
        assert run_info.skipped_no_match == 1
        assert len(run_info.skipped_records) == 1
        assert run_info.skipped_records[0]["reason"] == "no_matching_active_traffic_sign_or_signpost"

    def test_command_handles_multiple_traffic_signs_same_mount(
        self, additional_sign_device_type, traffic_sign_device_type
    ):
        """Test selection when multiple active traffic signs share a mount.

        With z-coordinate logic, the closest one above the additional sign should be selected.

        Args:
            additional_sign_device_type: Additional sign device type fixture
            traffic_sign_device_type: Traffic sign device type fixture
        """

        # Create mount
        mount = MountRealFactory()

        # Create additional sign at z=1.0
        ads = AdditionalSignRealFactory(
            device_type=additional_sign_device_type,
            mount_real=mount,
            parent=None,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 1.0, srid=settings.SRID),
        )

        # Create multiple active traffic signs above the additional sign
        TrafficSignRealFactory(
            device_type=traffic_sign_device_type,
            mount_real=mount,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 5.0, srid=settings.SRID),
        )
        traffic_sign_closest = TrafficSignRealFactory(
            device_type=traffic_sign_device_type,
            mount_real=mount,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 2.0, srid=settings.SRID),
        )

        # Run command
        out = StringIO()
        call_command("link_additional_sign_parents_by_mount", stdout=out)

        # Verify parent was set to the closest one above
        ads.refresh_from_db()
        assert ads.parent == traffic_sign_closest

    def test_command_links_multiple_additional_signs(self, additional_sign_device_type, traffic_sign_device_type):
        """Test linking multiple additional signs in a single run.

        Args:
            additional_sign_device_type: Additional sign device type fixture
            traffic_sign_device_type: Traffic sign device type fixture
        """
        # Create two mounts with traffic signs above additional signs
        mount1 = MountRealFactory()
        mount2 = MountRealFactory()
        traffic_sign_1 = TrafficSignRealFactory(
            device_type=traffic_sign_device_type,
            mount_real=mount1,
            location=Point(MIN_X + 10.0, MIN_Y + 10.0, 2.0, srid=settings.SRID),
        )
        traffic_sign_2 = TrafficSignRealFactory(
            device_type=traffic_sign_device_type,
            mount_real=mount2,
            location=Point(MIN_X + 20.0, MIN_Y + 20.0, 2.0, srid=settings.SRID),
        )

        # Create two additional signs without parents
        ads1 = AdditionalSignRealFactory(
            device_type=additional_sign_device_type,
            mount_real=mount1,
            parent=None,
            location=Point(MIN_X + 10.0, MIN_Y + 10.0, 1.0, srid=settings.SRID),
        )
        ads2 = AdditionalSignRealFactory(
            device_type=additional_sign_device_type,
            mount_real=mount2,
            parent=None,
            location=Point(MIN_X + 20.0, MIN_Y + 20.0, 1.0, srid=settings.SRID),
        )

        # Run command
        out = StringIO()
        call_command("link_additional_sign_parents_by_mount", stdout=out)

        # Verify both parents were set correctly
        ads1.refresh_from_db()
        ads2.refresh_from_db()
        assert ads1.parent == traffic_sign_1
        assert ads2.parent == traffic_sign_2

    def test_command_skips_additional_signs_with_existing_parent(
        self, additional_sign_device_type, traffic_sign_device_type
    ):
        """Test that additional signs with existing parents are skipped.

        Args:
            additional_sign_device_type: Additional sign device type fixture
            traffic_sign_device_type: Traffic sign device type fixture
        """
        # Create mount with traffic signs
        mount = MountRealFactory()
        # the existing parent, z-coord 2 units above the linked additional sign
        traffic_sign_1 = TrafficSignRealFactory(
            device_type=traffic_sign_device_type,
            mount_real=mount,
            location=Point(MIN_X + 10.0, MIN_Y + 10.0, 3.0, srid=settings.SRID),
        )
        # better candidate, zdiff=1, if additional was not already linked
        _traffic_sign_2 = TrafficSignRealFactory(
            device_type=traffic_sign_device_type,
            mount_real=mount,
            location=Point(MIN_X + 10.0, MIN_Y + 10.0, 2.0, srid=settings.SRID),
        )

        # Create additional sign with existing parent
        ads = AdditionalSignRealFactory(
            device_type=additional_sign_device_type,
            mount_real=mount,
            parent=traffic_sign_1,
            location=Point(MIN_X + 10.0, MIN_Y + 10.0, 1.0, srid=settings.SRID),
        )

        # Run command
        out = StringIO()
        call_command("link_additional_sign_parents_by_mount", stdout=out)

        # Verify parent was NOT changed
        ads.refresh_from_db()
        assert ads.parent == traffic_sign_1  # Still the original parent

    def test_command_updates_updated_by_field(self, additional_sign_device_type, traffic_sign_device_type):
        """Test that updated_by field is set to system user.

        Args:
            additional_sign_device_type: Additional sign device type fixture
            traffic_sign_device_type: Traffic sign device type fixture
        """
        # Create mount, traffic sign above, and additional sign
        mount = MountRealFactory()
        traffic_sign = TrafficSignRealFactory(
            device_type=traffic_sign_device_type,
            mount_real=mount,
            location=Point(MIN_X + 10.0, MIN_Y + 10.0, 2.0, srid=settings.SRID),
        )
        ads = AdditionalSignRealFactory(
            device_type=additional_sign_device_type,
            mount_real=mount,
            parent=None,
            location=Point(MIN_X + 10.0, MIN_Y + 10.0, 1.0, srid=settings.SRID),
        )

        # Run command
        out = StringIO()
        call_command("link_additional_sign_parents_by_mount", stdout=out)

        # Verify parent and updated_by were set
        ads.refresh_from_db()
        assert ads.parent == traffic_sign
        assert ads.updated_by is not None
        assert ads.updated_by.username == "system"

    def test_command_falls_back_to_signpost_real(self, additional_sign_device_type, signpost_device_type):
        """Test that a SignpostReal on the same mount is used when no TrafficSignReal exists.

        Args:
            additional_sign_device_type: Additional sign device type fixture
            signpost_device_type: Signpost device type fixture
        """
        # Create mount with only a signpost above, no traffic sign
        mount = MountRealFactory()
        signpost = SignpostRealFactory(
            device_type=signpost_device_type,
            mount_real=mount,
            location=Point(MIN_X + 10.0, MIN_Y + 10.0, 2.0, srid=settings.SRID),
        )
        ads = AdditionalSignRealFactory(
            device_type=additional_sign_device_type,
            mount_real=mount,
            parent=None,
            location=Point(MIN_X + 10.0, MIN_Y + 10.0, 1.0, srid=settings.SRID),
        )

        # Run command
        out = StringIO()
        call_command("link_additional_sign_parents_by_mount", stdout=out)

        # Verify signpost_real was set and parent left untouched
        ads.refresh_from_db()
        assert ads.parent is None
        assert ads.signpost_real == signpost
        assert ads.updated_by.username == "system"

        # Verify run info records the signpost link
        run_info = LinkAdditionalSignParentsRunInfo.objects.latest("started_at")
        assert run_info.total_candidates == 1
        assert run_info.successfully_linked == 1
        assert run_info.skipped_no_match == 0
        assert len(run_info.linked_records) == 1
        assert run_info.linked_records[0]["additional_sign_real_id"] == str(ads.id)
        assert run_info.linked_records[0]["signpost_real_id"] == str(signpost.id)
        assert run_info.linked_records[0]["traffic_sign_real_id"] is None

    def test_command_prefers_traffic_sign_over_signpost(
        self, additional_sign_device_type, traffic_sign_device_type, signpost_device_type
    ):
        """Test that a TrafficSignReal is preferred when both a traffic sign and signpost share the mount.

        Args:
            additional_sign_device_type: Additional sign device type fixture
            traffic_sign_device_type: Traffic sign device type fixture
            signpost_device_type: Signpost device type fixture
        """
        # Create mount that has both a traffic sign and a signpost above
        mount = MountRealFactory()
        traffic_sign = TrafficSignRealFactory(
            device_type=traffic_sign_device_type,
            mount_real=mount,
            location=Point(MIN_X + 10.0, MIN_Y + 10.0, 3.0, srid=settings.SRID),
        )
        SignpostRealFactory(
            device_type=signpost_device_type,
            mount_real=mount,
            location=Point(MIN_X + 10.0, MIN_Y + 10.0, 2.0, srid=settings.SRID),
        )
        ads = AdditionalSignRealFactory(
            device_type=additional_sign_device_type,
            mount_real=mount,
            parent=None,
            location=Point(MIN_X + 10.0, MIN_Y + 10.0, 1.0, srid=settings.SRID),
        )

        # Run command
        out = StringIO()
        call_command("link_additional_sign_parents_by_mount", stdout=out)

        # Verify the traffic sign won and signpost_real was left unset
        ads.refresh_from_db()
        assert ads.parent == traffic_sign
        assert ads.signpost_real is None

    def test_command_handles_multiple_signposts_same_mount(self, additional_sign_device_type, signpost_device_type):
        """Test selection when multiple active signposts share a mount.

        With z-coordinate logic, the closest one above the additional sign should be selected.

        Args:
            additional_sign_device_type: Additional sign device type fixture
            signpost_device_type: Signpost device type fixture
        """

        mount = MountRealFactory()

        # Create additional sign at z=1.0
        ads = AdditionalSignRealFactory(
            device_type=additional_sign_device_type,
            mount_real=mount,
            parent=None,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 1.0, srid=settings.SRID),
        )

        # Create multiple signposts above
        SignpostRealFactory(
            device_type=signpost_device_type,
            mount_real=mount,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 4.0, srid=settings.SRID),
        )
        signpost_closest = SignpostRealFactory(
            device_type=signpost_device_type,
            mount_real=mount,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 2.0, srid=settings.SRID),
        )

        # Run command
        out = StringIO()
        call_command("link_additional_sign_parents_by_mount", stdout=out)

        # Verify signpost_real was set to the closest one above
        ads.refresh_from_db()
        assert ads.signpost_real == signpost_closest

    def test_command_skips_additional_signs_with_existing_signpost_real(
        self, additional_sign_device_type, signpost_device_type
    ):
        """Test that additional signs that already have a signpost_real are skipped.

        Args:
            additional_sign_device_type: Additional sign device type fixture
            signpost_device_type: Signpost device type fixture
        """
        mount = MountRealFactory()
        signpost_1 = SignpostRealFactory(device_type=signpost_device_type, mount_real=mount)
        _signpost_2 = SignpostRealFactory(device_type=signpost_device_type, mount_real=mount)
        ads = AdditionalSignRealFactory(
            device_type=additional_sign_device_type,
            mount_real=mount,
            parent=None,
            signpost_real=signpost_1,
        )

        # Run command
        out = StringIO()
        call_command("link_additional_sign_parents_by_mount", stdout=out)

        # Verify signpost_real was NOT changed and no candidates were processed
        ads.refresh_from_db()
        assert ads.signpost_real == signpost_1
        assert ads.parent is None

        run_info = LinkAdditionalSignParentsRunInfo.objects.latest("started_at")
        assert run_info.total_candidates == 0

    def test_command_dry_run_does_not_set_signpost_real(self, additional_sign_device_type, signpost_device_type):
        """Test that dry-run mode does not set signpost_real on the signpost fallback path.

        Args:
            additional_sign_device_type: Additional sign device type fixture
            signpost_device_type: Signpost device type fixture
        """
        mount = MountRealFactory()
        signpost = SignpostRealFactory(
            device_type=signpost_device_type,
            mount_real=mount,
            location=Point(MIN_X + 10.0, MIN_Y + 10.0, 2.0, srid=settings.SRID),
        )
        ads = AdditionalSignRealFactory(
            device_type=additional_sign_device_type,
            mount_real=mount,
            parent=None,
            location=Point(MIN_X + 10.0, MIN_Y + 10.0, 1.0, srid=settings.SRID),
        )

        # Run command in dry-run mode
        out = StringIO()
        call_command("link_additional_sign_parents_by_mount", "--dry-run", stdout=out)

        # Verify no changes were made
        ads.refresh_from_db()
        assert ads.parent is None
        assert ads.signpost_real is None

        # Verify dry-run output mentions the signpost target
        output = out.getvalue()
        assert f"AdditionalSignReal {ads.id} -> SignpostReal {signpost.id}" in output

        run_info = LinkAdditionalSignParentsRunInfo.objects.latest("started_at")
        assert run_info.dry_run is True
        assert run_info.successfully_linked == 1

    def test_command_links_traffic_sign_and_signpost_in_same_run(
        self, additional_sign_device_type, traffic_sign_device_type, signpost_device_type
    ):
        """Test that both link types are resolved correctly within a single run.

        Args:
            additional_sign_device_type: Additional sign device type fixture
            traffic_sign_device_type: Traffic sign device type fixture
            signpost_device_type: Signpost device type fixture
        """
        mount_with_traffic_sign = MountRealFactory()
        mount_with_signpost = MountRealFactory()
        traffic_sign = TrafficSignRealFactory(
            device_type=traffic_sign_device_type,
            mount_real=mount_with_traffic_sign,
            location=Point(MIN_X + 10.0, MIN_Y + 10.0, 2.0, srid=settings.SRID),
        )
        signpost = SignpostRealFactory(
            device_type=signpost_device_type,
            mount_real=mount_with_signpost,
            location=Point(MIN_X + 20.0, MIN_Y + 20.0, 2.0, srid=settings.SRID),
        )

        ads_traffic_sign = AdditionalSignRealFactory(
            device_type=additional_sign_device_type,
            mount_real=mount_with_traffic_sign,
            parent=None,
            location=Point(MIN_X + 10.0, MIN_Y + 10.0, 1.0, srid=settings.SRID),
        )
        ads_signpost = AdditionalSignRealFactory(
            device_type=additional_sign_device_type,
            mount_real=mount_with_signpost,
            parent=None,
            location=Point(MIN_X + 20.0, MIN_Y + 20.0, 1.0, srid=settings.SRID),
        )

        # Run command
        out = StringIO()
        call_command("link_additional_sign_parents_by_mount", stdout=out)

        ads_traffic_sign.refresh_from_db()
        ads_signpost.refresh_from_db()

        assert ads_traffic_sign.parent == traffic_sign
        assert ads_traffic_sign.signpost_real is None
        assert ads_signpost.parent is None
        assert ads_signpost.signpost_real == signpost

        run_info = LinkAdditionalSignParentsRunInfo.objects.latest("started_at")
        assert run_info.total_candidates == 2
        assert run_info.successfully_linked == 2

    def test_command_prefers_active_traffic_sign_over_newer_soft_deleted(
        self, additional_sign_device_type, traffic_sign_device_type
    ):
        """Test that only active traffic signs are considered (soft-deleted are excluded via .active()).

        Args:
            additional_sign_device_type: Additional sign device type fixture
            traffic_sign_device_type: Traffic sign device type fixture
        """

        mount = MountRealFactory()

        # Create additional sign at z=1.0
        ads = AdditionalSignRealFactory(
            device_type=additional_sign_device_type,
            mount_real=mount,
            parent=None,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 1.0, srid=settings.SRID),
        )

        # Active traffic sign above at z=3.0
        active_traffic_sign = TrafficSignRealFactory(
            device_type=traffic_sign_device_type,
            mount_real=mount,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 3.0, srid=settings.SRID),
        )

        # Soft-deleted traffic sign (closer but should be ignored due to .active() filter)
        TrafficSignRealFactory(
            device_type=traffic_sign_device_type,
            mount_real=mount,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 2.0, srid=settings.SRID),
            is_active=False,
        )

        # Run command
        out = StringIO()
        call_command("link_additional_sign_parents_by_mount", stdout=out)

        # Verify the active one was selected (soft-deleted excluded)
        ads.refresh_from_db()
        assert ads.parent == active_traffic_sign

    # JF TODO thiagon kommentti ??
    def test_command_selects_latest_active_traffic_sign(self, additional_sign_device_type, traffic_sign_device_type):
        """Test selection when several active traffic signs share a mount at different z-coordinates.

        Args:
            additional_sign_device_type: Additional sign device type fixture
            traffic_sign_device_type: Traffic sign device type fixture
        """

        mount = MountRealFactory()

        # Create additional sign at z=1.0
        ads = AdditionalSignRealFactory(
            device_type=additional_sign_device_type,
            mount_real=mount,
            parent=None,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 1.0, srid=settings.SRID),
        )

        # Multiple active signs at same different heights
        TrafficSignRealFactory(
            device_type=traffic_sign_device_type,
            mount_real=mount,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 2.0, srid=settings.SRID),
        )
        latest_active = TrafficSignRealFactory(
            device_type=traffic_sign_device_type,
            mount_real=mount,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 2.0, srid=settings.SRID),
        )
        # Soft-deleted (should be excluded even that is is the closest)
        TrafficSignRealFactory(
            device_type=traffic_sign_device_type,
            mount_real=mount,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 1.5, srid=settings.SRID),
            is_active=False,
        )

        # Run command
        out = StringIO()
        call_command("link_additional_sign_parents_by_mount", stdout=out)

        # Verify closest active was selected
        ads.refresh_from_db()
        assert ads.parent == latest_active

    def test_command_selects_nothing_when_no_active_traffic_signs(
        self, additional_sign_device_type, traffic_sign_device_type
    ):
        """Test that no link is made when only soft-deleted traffic signs exist (due to .active() filter).

        Args:
            additional_sign_device_type: Additional sign device type fixture
            traffic_sign_device_type: Traffic sign device type fixture
        """

        mount = MountRealFactory()

        # Create additional sign at z=1.0
        ads = AdditionalSignRealFactory(
            device_type=additional_sign_device_type,
            mount_real=mount,
            parent=None,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 1.0, srid=settings.SRID),
        )

        # Only soft-deleted traffic signs (should be excluded by .active() filter)
        TrafficSignRealFactory(
            device_type=traffic_sign_device_type,
            mount_real=mount,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 3.0, srid=settings.SRID),
            is_active=False,
        )
        TrafficSignRealFactory(
            device_type=traffic_sign_device_type,
            mount_real=mount,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 2.0, srid=settings.SRID),
            is_active=False,
        )

        # Run command
        out = StringIO()
        call_command("link_additional_sign_parents_by_mount", stdout=out)

        # Verify no link was created (only soft-deleted candidates exist)
        ads.refresh_from_db()
        assert ads.parent is None

        # Verify appropriate skip reason - no active candidates at all
        run_info = LinkAdditionalSignParentsRunInfo.objects.latest("started_at")
        assert run_info.skipped_no_match == 1
        assert len(run_info.skipped_records) == 1
        assert run_info.skipped_records[0]["additional_sign_real_id"] == str(ads.id)
        assert run_info.skipped_records[0]["mount_real_id"] == str(mount.id)
        assert run_info.skipped_records[0]["reason"] == "no_matching_active_traffic_sign_or_signpost"

    def test_command_prefers_active_signpost_over_newer_soft_deleted(
        self, additional_sign_device_type, signpost_device_type
    ):
        """Test that only active signposts are considered on the fallback path.

        Args:
            additional_sign_device_type: Additional sign device type fixture
            signpost_device_type: Signpost device type fixture
        """

        mount = MountRealFactory()

        # Create additional sign at z=1.0
        ads = AdditionalSignRealFactory(
            device_type=additional_sign_device_type,
            mount_real=mount,
            parent=None,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 1.0, srid=settings.SRID),
        )

        # Active signpost above
        active_signpost = SignpostRealFactory(
            device_type=signpost_device_type,
            mount_real=mount,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 3.0, srid=settings.SRID),
        )

        # Soft-deleted signpost (should be excluded)
        SignpostRealFactory(
            device_type=signpost_device_type,
            mount_real=mount,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 2.0, srid=settings.SRID),
            is_active=False,
        )

        # Run command
        out = StringIO()
        call_command("link_additional_sign_parents_by_mount", stdout=out)

        # Verify active signpost was selected
        ads.refresh_from_db()
        assert ads.parent is None
        assert ads.signpost_real == active_signpost

    def test_command_selects_latest_soft_deleted_signpost_when_no_active(
        self, additional_sign_device_type, signpost_device_type
    ):
        """Test that no link is made when only soft-deleted signposts exist.

        Args:
            additional_sign_device_type: Additional sign device type fixture
            signpost_device_type: Signpost device type fixture
        """

        mount = MountRealFactory()

        # Create additional sign at z=1.0
        ads = AdditionalSignRealFactory(
            device_type=additional_sign_device_type,
            mount_real=mount,
            parent=None,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 1.0, srid=settings.SRID),
        )

        # Only soft-deleted signposts (should be excluded)
        SignpostRealFactory(
            device_type=signpost_device_type,
            mount_real=mount,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 3.0, srid=settings.SRID),
            is_active=False,
        )
        SignpostRealFactory(
            device_type=signpost_device_type,
            mount_real=mount,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 2.0, srid=settings.SRID),
            is_active=False,
        )

        # Run command
        out = StringIO()
        call_command("link_additional_sign_parents_by_mount", stdout=out)

        # Verify no link was created
        ads.refresh_from_db()
        assert ads.signpost_real is None

        # Verify appropriate skip reason - no active candidates at all
        run_info = LinkAdditionalSignParentsRunInfo.objects.latest("started_at")
        assert run_info.skipped_no_match == 1
        assert len(run_info.skipped_records) == 1
        assert run_info.skipped_records[0]["additional_sign_real_id"] == str(ads.id)
        assert run_info.skipped_records[0]["mount_real_id"] == str(mount.id)
        assert run_info.skipped_records[0]["reason"] == "no_matching_active_traffic_sign_or_signpost"

    def test_command_excludes_ticket_machines_from_signpost_fallback(
        self, ticket_machine_device_type, signpost_device_type
    ):
        """Test that ticket machines are not linked to signposts either.

        Args:
            ticket_machine_device_type: Ticket machine device type fixture
            signpost_device_type: Signpost device type fixture
        """
        mount = MountRealFactory()
        SignpostRealFactory(
            device_type=signpost_device_type,
            mount_real=mount,
            location=Point(MIN_X + 10.0, MIN_Y + 10.0, 2.0, srid=settings.SRID),
        )
        ticket_machine = AdditionalSignRealFactory(
            device_type=ticket_machine_device_type,
            mount_real=mount,
            parent=None,
            location=Point(MIN_X + 10.0, MIN_Y + 10.0, 1.0, srid=settings.SRID),
        )

        # Run command
        out = StringIO()
        call_command("link_additional_sign_parents_by_mount", stdout=out)

        # Verify ticket machine was not linked
        ticket_machine.refresh_from_db()
        assert ticket_machine.parent is None
        assert ticket_machine.signpost_real is None

    # ===========================
    # Z-coordinate based selection tests
    # ===========================

    def test_command_selects_closest_active_traffic_sign_above(
        self, additional_sign_device_type, traffic_sign_device_type
    ):
        """Test that the closest active traffic sign above the additional sign is selected.

        Args:
            additional_sign_device_type: Additional sign device type fixture
            traffic_sign_device_type: Traffic sign device type fixture
        """

        mount = MountRealFactory()

        # Additional sign at z=1.0
        ads = AdditionalSignRealFactory(
            device_type=additional_sign_device_type,
            mount_real=mount,
            parent=None,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 1.0, srid=settings.SRID),
        )

        # Traffic sign above at z=2.0 (closest)
        ts_close = TrafficSignRealFactory(
            device_type=traffic_sign_device_type,
            mount_real=mount,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 2.0, srid=settings.SRID),
        )

        # Traffic sign above at z=5.0 (farther)
        TrafficSignRealFactory(
            device_type=traffic_sign_device_type,
            mount_real=mount,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 5.0, srid=settings.SRID),
        )

        # Run command
        out = StringIO()
        call_command("link_additional_sign_parents_by_mount", stdout=out)

        # Verify the closest one above was selected
        ads.refresh_from_db()
        assert ads.parent == ts_close

        # Verify output indicates z-coordinate selection
        output = out.getvalue()
        assert "z=2.0" in output or "z=2.00" in output
        assert "z-diff" in output

    def test_command_skips_when_all_active_candidates_below(
        self, additional_sign_device_type, traffic_sign_device_type
    ):
        """Test that additional sign is skipped when all active traffic signs are below it.

        Args:
            additional_sign_device_type: Additional sign device type fixture
            traffic_sign_device_type: Traffic sign device type fixture
        """

        mount = MountRealFactory()

        # Additional sign at z=5.0
        ads = AdditionalSignRealFactory(
            device_type=additional_sign_device_type,
            mount_real=mount,
            parent=None,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 5.0, srid=settings.SRID),
        )

        # Traffic signs below at z=2.0 and z=3.0
        TrafficSignRealFactory(
            device_type=traffic_sign_device_type,
            mount_real=mount,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 2.0, srid=settings.SRID),
        )
        TrafficSignRealFactory(
            device_type=traffic_sign_device_type,
            mount_real=mount,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 3.0, srid=settings.SRID),
        )

        # Run command
        out = StringIO()
        call_command("link_additional_sign_parents_by_mount", stdout=out)

        # Verify no link was created
        ads.refresh_from_db()
        assert ads.parent is None

        # Verify appropriate warning in output
        output = out.getvalue()
        assert "No active TrafficSignReal above" in output or "no active candidates positioned above" in output

        # Verify run info statistics
        run_info = LinkAdditionalSignParentsRunInfo.objects.latest("started_at")
        assert run_info.successfully_linked == 0
        assert run_info.skipped_no_active_above == 1
        assert len(run_info.skipped_records) == 1
        assert run_info.skipped_records[0]["additional_sign_real_id"] == str(ads.id)
        assert run_info.skipped_records[0]["mount_real_id"] == str(mount.id)
        assert run_info.skipped_records[0]["reason"] == "no_active_candidates_above"

    def test_command_selects_closest_active_signpost_above(self, additional_sign_device_type, signpost_device_type):
        """Test that the closest active signpost above the additional sign is selected.

        Args:
            additional_sign_device_type: Additional sign device type fixture
            signpost_device_type: Signpost device type fixture
        """

        mount = MountRealFactory()

        # Additional sign at z=1.5
        ads = AdditionalSignRealFactory(
            device_type=additional_sign_device_type,
            mount_real=mount,
            parent=None,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 1.5, srid=settings.SRID),
        )

        # Signpost above at z=2.5 (closest)
        sp_close = SignpostRealFactory(
            device_type=signpost_device_type,
            mount_real=mount,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 2.5, srid=settings.SRID),
        )

        # Signpost above at z=6.0 (farther)
        SignpostRealFactory(
            device_type=signpost_device_type,
            mount_real=mount,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 6.0, srid=settings.SRID),
        )

        # Run command
        out = StringIO()
        call_command("link_additional_sign_parents_by_mount", stdout=out)

        # Verify the closest signpost above was selected
        ads.refresh_from_db()
        assert ads.signpost_real == sp_close
        assert ads.parent is None

    def test_command_tie_breaking_by_created_at_for_same_z(self, additional_sign_device_type, traffic_sign_device_type):
        """Test that when multiple candidates have the same z-coordinate, the latest created is selected.

        Args:
            additional_sign_device_type: Additional sign device type fixture
            traffic_sign_device_type: Traffic sign device type fixture
        """

        mount = MountRealFactory()

        # Additional sign at z=1.0
        ads = AdditionalSignRealFactory(
            device_type=additional_sign_device_type,
            mount_real=mount,
            parent=None,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 1.0, srid=settings.SRID),
        )

        # Two traffic signs at the same z=3.0
        TrafficSignRealFactory(
            device_type=traffic_sign_device_type,
            mount_real=mount,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 3.0, srid=settings.SRID),
        )
        ts_latest = TrafficSignRealFactory(
            device_type=traffic_sign_device_type,
            mount_real=mount,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 3.0, srid=settings.SRID),
        )

        # Run command
        out = StringIO()
        call_command("link_additional_sign_parents_by_mount", stdout=out)

        # Verify the latest created one was selected
        ads.refresh_from_db()
        assert ads.parent == ts_latest

    def test_command_only_considers_active_candidates_for_z_selection(
        self, additional_sign_device_type, traffic_sign_device_type
    ):
        """Test that soft-deleted candidates are not considered even if positioned above.

        Args:
            additional_sign_device_type: Additional sign device type fixture
            traffic_sign_device_type: Traffic sign device type fixture
        """

        mount = MountRealFactory()

        # Additional sign at z=1.0
        ads = AdditionalSignRealFactory(
            device_type=additional_sign_device_type,
            mount_real=mount,
            parent=None,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 1.0, srid=settings.SRID),
        )

        # Soft-deleted traffic sign above at z=2.0 (should be ignored)
        TrafficSignRealFactory(
            device_type=traffic_sign_device_type,
            mount_real=mount,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 2.0, srid=settings.SRID),
            is_active=False,
        )

        # Active traffic sign below at z=0.5 (should also be ignored - below additional sign)
        TrafficSignRealFactory(
            device_type=traffic_sign_device_type,
            mount_real=mount,
            location=Point(MIN_X + 100.0, MIN_Y + 200.0, 0.5, srid=settings.SRID),
        )

        # Run command
        out = StringIO()
        call_command("link_additional_sign_parents_by_mount", stdout=out)

        # Verify no link was created (soft-deleted ignored, active below ignored)
        ads.refresh_from_db()
        assert ads.parent is None

        # Verify appropriate skip reason
        run_info = LinkAdditionalSignParentsRunInfo.objects.latest("started_at")
        assert run_info.skipped_no_active_above == 1
        assert len(run_info.skipped_records) == 1
        assert run_info.skipped_records[0]["additional_sign_real_id"] == str(ads.id)
        assert run_info.skipped_records[0]["mount_real_id"] == str(mount.id)
        assert run_info.skipped_records[0]["reason"] == "no_active_candidates_above"

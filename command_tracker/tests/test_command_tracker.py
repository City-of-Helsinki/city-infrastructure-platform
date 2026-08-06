from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.urls import reverse
from django.utils import timezone

from command_tracker.management.trackable_command import TrackableCommand
from command_tracker.models import TrackedManagementCommand


# Dummy command classes to return when mocking `load_command_class`
class FakeTrackableCommand(TrackableCommand):
    pass


class FakeUntrackableCommand(BaseCommand):
    pass


@pytest.fixture
def mock_commands_env():
    """
    Fixture that configures `TRACK_COMMAND_USAGE_APPS` and provides a helper
    to dynamically mock `get_commands` and `load_command_class` using standard unittest.mock.
    """
    active_patches = []

    def _setup(commands_dict):
        """
        commands_dict format: {"command_name": {"trackable": bool, "exists": bool}}
        """
        # Clean up any previously started patches if _setup is called multiple times
        for p in active_patches:
            p.stop()
        active_patches.clear()

        # Mock `get_commands` to return only the commands configured as existing
        active_cmds = {command: "track_example_app" for command, v in commands_dict.items() if v["exists"]}
        patch_get = patch("command_tracker.admin.get_commands", return_value=active_cmds)
        patch_get.start()
        active_patches.append(patch_get)

        # Mock `load_command_class` to return the appropriate instance type
        def fake_load(app, cmd):
            if app == "track_example_app" and cmd in commands_dict:
                if commands_dict[cmd]["exists"]:
                    if commands_dict[cmd]["trackable"]:
                        return FakeTrackableCommand()
                    return FakeUntrackableCommand()
            raise Exception(f"Command {cmd} not found")

        patch_load = patch("command_tracker.admin.load_command_class", side_effect=fake_load)
        patch_load.start()
        active_patches.append(patch_load)

    yield _setup

    # Teardown patches after the test completes
    for p in active_patches:
        p.stop()


#######################################
# Conditional section rendering tests #
#######################################


@pytest.mark.django_db
def test_list_view_shows_only_tracked_command_section(admin_client, mock_commands_env):
    mock_commands_env({"tracked_command": {"trackable": True, "exists": True}})
    TrackedManagementCommand.objects.create(
        id="track_example_app-tracked_command",
        app="track_example_app",
        command="tracked_command",
    )

    url = reverse("admin:command_tracker_trackedmanagementcommand_changelist")
    response = admin_client.get(url)

    assert response.status_code == 200
    content = response.content.decode()

    assert "<h2>Tracked commands</h2>" in content
    assert "<h2>Invalid tracking entries" not in content
    assert "<h2>Untracked trackable commands</h2>" not in content
    assert "<h2>Untrackable commands</h2>" not in content

    assert "tracked_command" in content
    assert "formerly_trackable_command" not in content
    assert "untracked_trackable_command" not in content
    assert "untrackable_command" not in content


@pytest.mark.django_db
def test_list_view_shows_only_untracked_trackable_command_section(admin_client, mock_commands_env):
    mock_commands_env({"untracked_trackable_command": {"trackable": True, "exists": True}})

    url = reverse("admin:command_tracker_trackedmanagementcommand_changelist")
    response = admin_client.get(url)

    assert response.status_code == 200
    content = response.content.decode()

    assert "<h2>Tracked commands</h2>" not in content
    assert "<h2>Invalid tracking entries" not in content
    assert "<h2>Untracked trackable commands</h2>" in content
    assert "<h2>Untrackable commands</h2>" not in content

    assert "tracked_command" not in content
    assert "formerly_trackable_command" not in content
    assert "untracked_trackable_command" in content
    assert "untrackable_command" not in content


@pytest.mark.django_db
def test_list_view_shows_only_untrackable_command_section(admin_client, mock_commands_env):
    mock_commands_env({"untrackable_command": {"trackable": False, "exists": True}})

    url = reverse("admin:command_tracker_trackedmanagementcommand_changelist")
    response = admin_client.get(url)

    assert response.status_code == 200
    content = response.content.decode()

    assert "<h2>Tracked commands</h2>" not in content
    assert "<h2>Invalid tracking entries" not in content
    assert "<h2>Untracked trackable commands</h2>" not in content
    assert "<h2>Untrackable commands</h2>" in content

    assert "tracked_command" not in content
    assert "formerly_trackable_command" not in content
    assert "untracked_trackable_command" not in content
    assert "untrackable_command" in content


@pytest.mark.django_db
def test_list_view_shows_only_invalid_formerly_trackable_command_section(admin_client, mock_commands_env):
    mock_commands_env({"formerly_trackable_command": {"trackable": False, "exists": False}})
    TrackedManagementCommand.objects.create(
        id="track_example_app-formerly_trackable_command",
        app="track_example_app",
        command="formerly_trackable_command",
    )

    url = reverse("admin:command_tracker_trackedmanagementcommand_changelist")
    response = admin_client.get(url)

    assert response.status_code == 200
    content = response.content.decode()

    assert "<h2>Tracked commands</h2>" not in content
    assert "<h2>Invalid tracking entries" in content
    assert "<h2>Untracked trackable commands</h2>" not in content
    assert "<h2>Untrackable commands</h2>" not in content

    assert "tracked_command" not in content
    assert "formerly_trackable_command" in content
    assert "untracked_trackable_command" not in content
    assert "untrackable_command" not in content


@pytest.mark.django_db
def test_list_view_shows_all_sections_simultaneously(admin_client, mock_commands_env):
    mock_commands_env(
        {
            "tracked_command": {"trackable": True, "exists": True},
            "untracked_trackable_command": {"trackable": True, "exists": True},
            "untrackable_command": {"trackable": False, "exists": True},
            "formerly_trackable_command": {"trackable": False, "exists": False},
        }
    )

    TrackedManagementCommand.objects.create(
        id="track_example_app-tracked_command",
        app="track_example_app",
        command="tracked_command",
    )
    TrackedManagementCommand.objects.create(
        id="track_example_app-formerly_trackable_command",
        app="track_example_app",
        command="formerly_trackable_command",
    )

    url = reverse("admin:command_tracker_trackedmanagementcommand_changelist")
    response = admin_client.get(url)

    assert response.status_code == 200
    content = response.content.decode()

    assert "<h2>Tracked commands</h2>" in content
    assert "<h2>Invalid tracking entries" in content
    assert "<h2>Untracked trackable commands</h2>" in content
    assert "<h2>Untrackable commands</h2>" in content

    assert "tracked_command" in content
    assert "formerly_trackable_command" in content
    assert "untracked_trackable_command" in content
    assert "untrackable_command" in content


########################
# Admin workflow tests #
########################


@pytest.mark.django_db
def test_action_start_tracking_creates_entry_and_redirects(admin_client, mock_commands_env):
    mock_commands_env({"untracked_trackable_command": {"trackable": True, "exists": True}})

    assert TrackedManagementCommand.objects.count() == 0

    url = reverse(
        "admin:command_tracker_trackedmanagementcommand_start", args=["track_example_app-untracked_trackable_command"]
    )
    response = admin_client.post(url)

    # Check redirect works seamlessly
    assert response.status_code == 302
    assert response.url == reverse("admin:command_tracker_trackedmanagementcommand_changelist")

    # Check that database row was successfully instantiated
    assert TrackedManagementCommand.objects.count() == 1
    tracker_obj = TrackedManagementCommand.objects.first()
    assert tracker_obj.id == "track_example_app-untracked_trackable_command"
    assert tracker_obj.app == "track_example_app"
    assert tracker_obj.command == "untracked_trackable_command"
    assert tracker_obj.tracking_started_at is not None


@pytest.mark.django_db
def test_action_delete_removes_invalid_tracking_entry(admin_client, mock_commands_env):
    mock_commands_env({"formerly_trackable_command": {"trackable": False, "exists": False}})
    TrackedManagementCommand.objects.create(
        id="track_example_app-formerly_trackable_command",
        app="track_example_app",
        command="formerly_trackable_command",
    )

    assert TrackedManagementCommand.objects.count() == 1

    # Delete the entry
    url = reverse(
        "admin:command_tracker_trackedmanagementcommand_delete", args=["track_example_app-formerly_trackable_command"]
    )
    response = admin_client.post(url, data={"post": "yes"})

    # Check redirect works seamlessly
    assert response.status_code == 302
    assert response.url == reverse("admin:command_tracker_trackedmanagementcommand_changelist")

    # Check the entry was actually deleted
    assert TrackedManagementCommand.objects.count() == 0


##################################################
# Tracked command execution usage tracking tests #
##################################################


@pytest.mark.django_db
def test_trackable_command_execution_updates_timestamp():
    # Create a dummy command and spoof its module path so TrackableCommand
    # can successfully parse the app name and command name.
    class DummyTrackableCommand(TrackableCommand):
        __module__ = "track_example_app.management.commands.dummy_trackable_command"

        def handle(self, *args, **options):
            pass

    # Insert the tracking entry into the database with a date 30 days in the past
    past_timestamp = timezone.now() - timedelta(days=30)
    tracker = TrackedManagementCommand.objects.create(
        id="track_example_app-dummy_trackable_command",
        app="track_example_app",
        command="dummy_trackable_command",
        tracking_started_at=past_timestamp,
        latest_executed_at=past_timestamp,
    )
    assert tracker.latest_executed_at == past_timestamp  # sanity check

    # Call the command and verify that its tracking_started_at is basically "now" (with a small error margin)
    call_command(DummyTrackableCommand())
    tracker.refresh_from_db()
    current_timestamp = tracker.latest_executed_at
    time_difference = timezone.now() - tracker.latest_executed_at
    assert current_timestamp > past_timestamp
    assert time_difference.total_seconds() < 5

from django.core.management.base import BaseCommand
from django.utils import timezone

from command_tracker.models import TrackedManagementCommand


class TrackableCommand(BaseCommand):
    """
    Base class for commands that need their execution tracked.

    If the command is getting tracked and gets executed, it will update the tracker's latest_track_at field.
    """

    def execute(self, *args, **options):
        # Resolve the command ID from its location
        module_parts = self.__module__.split(".")
        mgmt_idx = module_parts.index("management")
        app_name = module_parts[mgmt_idx - 1]
        command_name = module_parts[-1]
        cmd_id = f"{app_name}-{command_name}"

        # Update the tracking timestamp
        TrackedManagementCommand.objects.filter(id=cmd_id).update(latest_tracked_at=timezone.now())

        # Execute as usual
        return super().execute(*args, **options)

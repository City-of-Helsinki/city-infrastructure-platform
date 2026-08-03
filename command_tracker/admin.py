from operator import itemgetter

from django import forms
from django.conf import settings
from django.contrib import admin
from django.core.management import get_commands, load_command_class
from django.shortcuts import redirect, render
from django.urls import path
from django.utils import timezone

from command_tracker.management.trackable_command import TrackableCommand
from command_tracker.models import TrackedManagementCommand


class TrackedCommandForm(forms.ModelForm):
    class Meta:
        model = TrackedManagementCommand
        fields = ["comment"]


def is_trackable(app_name: str, cmd_name: str) -> bool:
    try:
        cmd_instance = load_command_class(app_name, cmd_name)
        return isinstance(cmd_instance, TrackableCommand)
    except Exception:
        return False


def get_tracked_apps():
    return getattr(
        settings,
        "TRACK_COMMAND_USAGE_APPS",
        [
            "city_furniture",
            "traffic_control",
            "users",
        ],
    )


@admin.register(TrackedManagementCommand)
class TrackedManagementCommandAdmin(admin.ModelAdmin):
    fields = ("app", "command", "comment", "latest_tracked_at")
    readonly_fields = ("app", "command", "latest_tracked_at")

    def has_add_permission(self, request):
        return False

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        return [
            path("", self.admin_site.admin_view(self.custom_changelist_view), name=f"{info[0]}_{info[1]}_changelist"),
            path(
                "<path:object_id>/change/",
                self.admin_site.admin_view(self.changeform_view),
                name=f"{info[0]}_{info[1]}_change",
            ),
            path(
                "<path:object_id>/start/",
                self.admin_site.admin_view(self.start_tracking_view),
                name=f"{info[0]}_{info[1]}_start",
            ),
            path(
                "<path:object_id>/delete/",
                self.admin_site.admin_view(self.delete_view),
                name=f"{info[0]}_{info[1]}_delete",
            ),
        ]

    def custom_changelist_view(self, request):
        existing_commands = {command: app for command, app in get_commands().items() if app in get_tracked_apps()}
        tracked_command_entries = {obj.id: obj for obj in TrackedManagementCommand.objects.all()}

        tracked_commands_ctx = []  # Trackable commands with track entry
        orphaned_entries_ctx = []  # Untrackable (or non-existing) commands with track entry
        untracked_trackable_ctx = []  # Trackable commands without track entry
        untrackable_ctx = []  # Untrackable commands without track entry

        # Build context information for TrackedManagementCommand entries in the database
        for cmd_id, db_record in tracked_command_entries.items():
            command_exists = existing_commands.get(db_record.command) == db_record.app
            command_is_trackable = is_trackable(db_record.app, db_record.command)

            if command_exists and command_is_trackable:
                tracked_commands_ctx.append(
                    {
                        "id": cmd_id,
                        "app": db_record.app,
                        "command": db_record.command,
                        "latest_tracked_at": db_record.latest_tracked_at,
                        "comment": db_record.comment,
                    }
                )
            else:
                orphaned_entries_ctx.append(
                    {
                        "id": db_record.id,
                        "app": db_record.app,
                        "command": db_record.command,
                    }
                )

        # Build context information for management commands that do not have TrackedManagementCommand entries
        for cmd, app in existing_commands.items():
            cmd_id = f"{app}-{cmd}"
            if cmd_id in tracked_command_entries:
                continue

            item = {"id": cmd_id, "app": app, "command": cmd}
            if is_trackable(app, cmd):
                untracked_trackable_ctx.append(item)
            else:
                untrackable_ctx.append(item)

        # Organize the context data
        tracked_commands_ctx.sort(key=itemgetter("id"))
        orphaned_entries_ctx.sort(key=itemgetter("id"))
        untracked_trackable_ctx.sort(key=itemgetter("id"))
        untrackable_ctx.sort(key=itemgetter("id"))

        context = {
            **self.admin_site.each_context(request),
            "title": "Tracked Management Commands",
            "opts": self.model._meta,
            "tracked_commands": tracked_commands_ctx,
            "orphaned_entries": orphaned_entries_ctx,
            "untracked_trackable": untracked_trackable_ctx,
            "untrackable": untrackable_ctx,
        }
        return render(request, "admin/tracked_command_list.html", context)

    def start_tracking_view(self, request, object_id):
        if request.method == "POST":
            app, command = object_id.split("-", 1)
            TrackedManagementCommand.objects.create(
                id=object_id, app=app, command=command, latest_tracked_at=timezone.now()
            )
        return redirect(f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist")

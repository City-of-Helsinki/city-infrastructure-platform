"""Django admin configuration for StreetScan V2 import run log models."""
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from traffic_control.models.streetscan_import import StreetScanImportRevertFile, StreetScanImportRun


@admin.register(StreetScanImportRevertFile)
class StreetScanImportRevertFileAdmin(admin.ModelAdmin):
    """Admin interface for StreetScan import revert files.

    Adding is allowed so operators can manually attach a revert file to a run.
    Editing existing records is not permitted — replace by adding a new file.
    """

    list_display = ("id", "import_run_link", "file", "is_public")
    list_filter = ("is_public",)
    search_fields = ("file", "import_run__id")
    readonly_fields = ("id", "import_run_link")
    fieldsets = (
        (
            _("File"),
            {"fields": ("id", "file", "is_public")},
        ),
        (
            _("Import run"),
            {"fields": ("import_run", "import_run_link")},
        ),
    )

    def has_change_permission(self, request, obj=None) -> bool:
        """Disable editing existing revert files through admin.

        Args:
            request: The HTTP request.
            obj: The object being changed (unused).

        Returns:
            bool: Always False.
        """
        return False

    @admin.display(description=_("Import run"))
    def import_run_link(self, obj: StreetScanImportRevertFile) -> str:
        """Link back to the parent import run.

        Args:
            obj (StreetScanImportRevertFile): The revert file instance.

        Returns:
            str: HTML anchor to the parent run's change page, or dash if unsaved.
        """
        if not obj.pk or not obj.import_run_id:
            return "-"
        url = reverse("admin:traffic_control_streetscanimportrun_change", args=[obj.import_run_id])
        return format_html('<a href="{}">Run #{}</a>', url, obj.import_run_id)


class StreetScanImportRevertFileInline(admin.TabularInline):
    """Inline for viewing and adding revert files within an import run."""

    model = StreetScanImportRevertFile
    extra = 1
    can_delete = False
    fields = ("file", "is_public")


@admin.register(StreetScanImportRun)
class StreetScanImportRunAdmin(admin.ModelAdmin):
    """Admin interface for StreetScan V2 import run logs.

    All fields are read-only — run logs are created by the management command,
    not through the admin interface.
    """

    list_display = (
        "id",
        "ran_at",
        "is_dry_run",
        "mount_file_short",
        "sign_file_short",
        "mounts_summary",
        "signs_summary",
        "signposts_summary",
        "additional_signs_summary",
        "skipped_count",
        "warning_count",
        "error_count",
    )
    list_filter = ("is_dry_run", "ran_at")
    search_fields = ("id", "mount_file", "sign_file")
    ordering = ("-ran_at",)
    readonly_fields = (
        "id",
        "ran_at",
        "is_dry_run",
        "mount_file",
        "sign_file",
        "preprocessing_duration_s",
        "mounts_created",
        "mounts_updated",
        "signs_created",
        "signs_updated",
        "signs_deactivated",
        "signposts_created",
        "signposts_updated",
        "signposts_deactivated",
        "additional_signs_created",
        "additional_signs_updated",
        "additional_signs_deactivated",
        "skipped_count",
        "warning_count",
        "error_count",
        "processed_mount_source_ids_count",
        "processed_sign_source_ids_count",
        "processed_signpost_source_ids_count",
        "processed_additional_sign_source_ids_count",
        "phase_durations_display",
        "details_display",
    )
    fieldsets = (
        (
            _("Run Information"),
            {
                "fields": (
                    "id",
                    "ran_at",
                    "is_dry_run",
                    "mount_file",
                    "sign_file",
                    "preprocessing_duration_s",
                )
            },
        ),
        (
            _("Mounts"),
            {
                "fields": (
                    "mounts_created",
                    "mounts_updated",
                    "processed_mount_source_ids_count",
                )
            },
        ),
        (
            _("Traffic Signs"),
            {
                "fields": (
                    "signs_created",
                    "signs_updated",
                    "signs_deactivated",
                    "processed_sign_source_ids_count",
                )
            },
        ),
        (
            _("Signposts"),
            {
                "fields": (
                    "signposts_created",
                    "signposts_updated",
                    "signposts_deactivated",
                    "processed_signpost_source_ids_count",
                )
            },
        ),
        (
            _("Additional Signs"),
            {
                "fields": (
                    "additional_signs_created",
                    "additional_signs_updated",
                    "additional_signs_deactivated",
                    "processed_additional_sign_source_ids_count",
                )
            },
        ),
        (
            _("Event Summary"),
            {
                "fields": (
                    "skipped_count",
                    "warning_count",
                    "error_count",
                )
            },
        ),
        (
            _("Event Details"),
            {
                "fields": ("details_display",),
                "classes": ("collapse",),
            },
        ),
        (
            _("Phase Durations"),
            {
                "fields": ("phase_durations_display",),
                "classes": ("collapse",),
            },
        ),
    )
    inlines = [StreetScanImportRevertFileInline]

    def has_add_permission(self, request) -> bool:
        """Disable creating run logs through admin.

        Args:
            request: The HTTP request.

        Returns:
            bool: Always False.
        """
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        """Disable editing run logs through admin.

        Args:
            request: The HTTP request.
            obj: The object being changed (unused).

        Returns:
            bool: Always False.
        """
        return False

    # ------------------------------------------------------------------
    # List display helpers
    # ------------------------------------------------------------------

    @admin.display(description=_("Mount file"))
    def mount_file_short(self, obj: StreetScanImportRun) -> str:
        """Display the basename of the mount file.

        Args:
            obj (StreetScanImportRun): The run log instance.

        Returns:
            str: Basename of the mount file path.
        """
        return obj.mount_file.split("/")[-1] if obj.mount_file else "-"

    @admin.display(description=_("Sign file"))
    def sign_file_short(self, obj: StreetScanImportRun) -> str:
        """Display the basename of the sign file.

        Args:
            obj (StreetScanImportRun): The run log instance.

        Returns:
            str: Basename of the sign file path.
        """
        return obj.sign_file.split("/")[-1] if obj.sign_file else "-"

    @admin.display(description=_("Mounts"))
    def mounts_summary(self, obj: StreetScanImportRun) -> str:
        """Display mount create/update counts.

        Args:
            obj (StreetScanImportRun): The run log instance.

        Returns:
            str: HTML summary of mount counts.
        """
        return format_html(
            '<span title="created">+{}</span> / <span title="updated">↻{}</span>',
            obj.mounts_created,
            obj.mounts_updated,
        )

    @admin.display(description=_("Signs"))
    def signs_summary(self, obj: StreetScanImportRun) -> str:
        """Display traffic sign create/update/deactivate counts.

        Args:
            obj (StreetScanImportRun): The run log instance.

        Returns:
            str: HTML summary of sign counts.
        """
        return format_html(
            '<span title="created">+{}</span> / <span title="updated">↻{}</span>'
            ' / <span title="deactivated" style="color:#dc3545;">✕{}</span>',
            obj.signs_created,
            obj.signs_updated,
            obj.signs_deactivated,
        )

    @admin.display(description=_("Signposts"))
    def signposts_summary(self, obj: StreetScanImportRun) -> str:
        """Display signpost create/update/deactivate counts.

        Args:
            obj (StreetScanImportRun): The run log instance.

        Returns:
            str: HTML summary of signpost counts.
        """
        return format_html(
            '<span title="created">+{}</span> / <span title="updated">↻{}</span>'
            ' / <span title="deactivated" style="color:#dc3545;">✕{}</span>',
            obj.signposts_created,
            obj.signposts_updated,
            obj.signposts_deactivated,
        )

    @admin.display(description=_("Additional signs"))
    def additional_signs_summary(self, obj: StreetScanImportRun) -> str:
        """Display additional sign create/update/deactivate counts.

        Args:
            obj (StreetScanImportRun): The run log instance.

        Returns:
            str: HTML summary of additional sign counts.
        """
        return format_html(
            '<span title="created">+{}</span> / <span title="updated">↻{}</span>'
            ' / <span title="deactivated" style="color:#dc3545;">✕{}</span>',
            obj.additional_signs_created,
            obj.additional_signs_updated,
            obj.additional_signs_deactivated,
        )

    # ------------------------------------------------------------------
    # Detail view helpers
    # ------------------------------------------------------------------

    @admin.display(description=_("Processed mount source IDs (count)"))
    def processed_mount_source_ids_count(self, obj: StreetScanImportRun) -> int:
        """Return the number of processed mount source IDs.

        Args:
            obj (StreetScanImportRun): The run log instance.

        Returns:
            int: Count of processed mount source IDs.
        """
        return len(obj.processed_mount_source_ids or [])

    @admin.display(description=_("Processed sign source IDs (count)"))
    def processed_sign_source_ids_count(self, obj: StreetScanImportRun) -> int:
        """Return the number of processed traffic sign source IDs.

        Args:
            obj (StreetScanImportRun): The run log instance.

        Returns:
            int: Count of processed sign source IDs.
        """
        return len(obj.processed_sign_source_ids or [])

    @admin.display(description=_("Processed signpost source IDs (count)"))
    def processed_signpost_source_ids_count(self, obj: StreetScanImportRun) -> int:
        """Return the number of processed signpost source IDs.

        Args:
            obj (StreetScanImportRun): The run log instance.

        Returns:
            int: Count of processed signpost source IDs.
        """
        return len(obj.processed_signpost_source_ids or [])

    @admin.display(description=_("Processed additional sign source IDs (count)"))
    def processed_additional_sign_source_ids_count(self, obj: StreetScanImportRun) -> int:
        """Return the number of processed additional sign source IDs.

        Args:
            obj (StreetScanImportRun): The run log instance.

        Returns:
            int: Count of processed additional sign source IDs.
        """
        return len(obj.processed_additional_sign_source_ids or [])

    @admin.display(description=_("Phase durations"))
    def phase_durations_display(self, obj: StreetScanImportRun) -> str:
        """Render per-phase timing as an HTML table.

        Args:
            obj (StreetScanImportRun): The run log instance.

        Returns:
            str: Safe HTML table of object-type × phase durations.
        """
        durations: dict = obj.phase_durations or {}
        if not durations:
            return mark_safe('<span style="color:#6c757d;">No timing data recorded.</span>')

        rows = "".join(
            format_html(
                "<tr>"
                '<td style="padding:2px 8px;font-weight:bold;">{obj_type}</td>'
                '<td style="padding:2px 8px;">{phase}</td>'
                '<td style="padding:2px 8px;font-family:monospace;">{duration:.3f}s</td>'
                "</tr>",
                obj_type=obj_type,
                phase=phase,
                duration=duration_s,
            )
            for obj_type, phases in durations.items()
            for phase, duration_s in phases.items()
        )
        return mark_safe(
            '<table style="width:100%;border-collapse:collapse;">'
            "<thead><tr>"
            '<th style="text-align:left;padding:2px 8px;">Object type</th>'
            '<th style="text-align:left;padding:2px 8px;">Phase</th>'
            '<th style="text-align:left;padding:2px 8px;">Duration</th>'
            "</tr></thead>"
            f"<tbody>{rows}</tbody>"
            "</table>"
        )

    @admin.display(description=_("Event details"))
    def details_display(self, obj: StreetScanImportRun) -> str:
        """Render the details list as an HTML table grouped by level.

        Args:
            obj (StreetScanImportRun): The run log instance.

        Returns:
            str: Safe HTML table of event details.
        """
        details: list[dict] = obj.details or []
        if not details:
            return mark_safe('<span style="color:#6c757d;">No events recorded.</span>')

        level_colours = {"skip": "#6c757d", "warning": "#ffc107", "error": "#dc3545"}
        rows = "".join(
            format_html(
                "<tr>"
                '<td style="padding:2px 8px;color:{colour};font-weight:bold;">{level}</td>'
                '<td style="padding:2px 8px;font-family:monospace;">{source_id}</td>'
                '<td style="padding:2px 8px;">{reason}</td>'
                "</tr>",
                colour=level_colours.get(entry.get("level", ""), "#333"),
                level=entry.get("level", ""),
                source_id=entry.get("source_id", ""),
                reason=entry.get("reason", ""),
            )
            for entry in details
        )
        return mark_safe(
            '<table style="width:100%;border-collapse:collapse;">'
            "<thead><tr>"
            '<th style="text-align:left;padding:2px 8px;">Level</th>'
            '<th style="text-align:left;padding:2px 8px;">Source ID</th>'
            '<th style="text-align:left;padding:2px 8px;">Reason</th>'
            "</tr></thead>"
            f"<tbody>{rows}</tbody>"
            "</table>"
        )

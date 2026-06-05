"""Django admin configuration for StreetScan V2 import run log models."""
import csv
import io

from django.contrib import admin
from django.http import Http404, HttpResponse
from django.template.loader import render_to_string
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _

from traffic_control.mixins import UploadsFileProxyMixin
from traffic_control.models.streetscan_import import StreetScanImportRevertFile, StreetScanImportRun


@admin.register(StreetScanImportRevertFile)
class StreetScanImportRevertFileAdmin(admin.ModelAdmin, UploadsFileProxyMixin):
    """Admin interface for StreetScan import revert files.

    Adding and editing records is not permitted through the admin interface.
    Revert files are attached programmatically by the import management command.
    """

    list_display = ("id", "import_run_link", "file_proxy", "is_public")
    list_filter = ("is_public",)
    search_fields = ("file", "import_run__id")
    readonly_fields = ("id", "import_run_link", "file_proxy")
    fieldsets = (
        (
            _("File"),
            {"fields": ("id", "file_proxy", "is_public")},
        ),
        (
            _("Import run"),
            {"fields": ("import_run", "import_run_link")},
        ),
    )

    def has_add_permission(self, request) -> bool:
        """Disable adding revert files through admin.
        https://docs.djangoproject.com/en/5.2/ref/contrib/admin/#django.contrib.admin.ModelAdmin.has_add_permission
        """
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        """Disable editing existing revert files through admin.
        https://docs.djangoproject.com/en/5.2/ref/contrib/admin/#django.contrib.admin.ModelAdmin.has_change_permission
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
        return render_to_string(
            "admin/traffic_control/streetscan_import/import_run_link.html",
            {"url": url, "import_run_id": obj.import_run_id},
        )


class StreetScanImportRevertFileInline(admin.TabularInline, UploadsFileProxyMixin):
    """Inline for viewing revert files within an import run."""

    model = StreetScanImportRevertFile
    extra = 1
    can_delete = False
    fields = ("file_proxy", "is_public")
    readonly_fields = ("file_proxy",)


@admin.register(StreetScanImportRun)
class StreetScanImportRunAdmin(admin.ModelAdmin):
    """Admin interface for StreetScan V2 import run logs.

    All fields are read-only — run logs are created by the management command,
    not through the admin interface.
    """

    list_display = (
        "id",
        "started_at",
        "dry_run",
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
    list_filter = ("dry_run", "started_at")
    search_fields = ("id", "mount_file", "sign_file")
    ordering = ("-started_at",)
    readonly_fields = (
        "id",
        "started_at",
        "completed_at",
        "dry_run",
        "mount_file",
        "sign_file",
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
                    "started_at",
                    "completed_at",
                    "dry_run",
                    "mount_file",
                    "sign_file",
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
        https://docs.djangoproject.com/en/5.2/ref/contrib/admin/#django.contrib.admin.ModelAdmin.has_add_permission
        """
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        """Disable editing run logs through admin.
        https://docs.djangoproject.com/en/5.2/ref/contrib/admin/#django.contrib.admin.ModelAdmin.has_change_permission
        """
        return False

    def get_urls(self):
        """Extend admin URLs with a per-run CSV download endpoint.

        Returns:
            list: Combined list of custom and default admin URLs.
        """
        custom_urls = [
            path(
                "<int:pk>/details-csv/",
                self.admin_site.admin_view(self.details_csv_view),
                name="traffic_control_streetscanimportrun_details_csv",
            ),
        ]
        return custom_urls + super().get_urls()

    def details_csv_view(self, request, pk: int) -> HttpResponse:
        """Stream a CSV file of detail entries for a given object_type and level.

        Query parameters:
            object_type (str): e.g. ``"signs"``
            level (str): e.g. ``"warning"`` or ``"skip"``

        Args:
            request: The HTTP request.
            pk (int): Primary key of the StreetScanImportRun.

        Returns:
            HttpResponse: CSV attachment response.

        Raises:
            Http404: If the run does not exist.
        """
        try:
            run = StreetScanImportRun.objects.get(pk=pk)
        except StreetScanImportRun.DoesNotExist:
            raise Http404

        object_type = request.GET.get("object_type", "")
        level = request.GET.get("level", "")
        details = run.details or []
        filtered = [e for e in details if e.get("object_type") == object_type and e.get("level") == level]

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["source_id", "phase", "reason"])
        for e in filtered:
            writer.writerow([e.get("source_id", ""), e.get("phase", ""), e.get("reason", "")])

        filename = f"run_{pk}_{object_type}_{level}.csv"
        response = HttpResponse(buf.getvalue(), content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

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

    _ENTITY_SUMMARY_TEMPLATE = "admin/traffic_control/streetscan_import/entity_summary.html"

    @admin.display(description=_("Mounts"))
    def mounts_summary(self, obj: StreetScanImportRun) -> str:
        """Display mount create/update counts.

        Args:
            obj (StreetScanImportRun): The run log instance.

        Returns:
            str: HTML summary of mount counts.
        """
        return render_to_string(
            self._ENTITY_SUMMARY_TEMPLATE,
            {"created": obj.mounts_created, "updated": obj.mounts_updated, "deactivated": None},
        )

    @admin.display(description=_("Signs"))
    def signs_summary(self, obj: StreetScanImportRun) -> str:
        """Display traffic sign create/update/deactivate counts.

        Args:
            obj (StreetScanImportRun): The run log instance.

        Returns:
            str: HTML summary of sign counts.
        """
        return render_to_string(
            self._ENTITY_SUMMARY_TEMPLATE,
            {"created": obj.signs_created, "updated": obj.signs_updated, "deactivated": obj.signs_deactivated},
        )

    @admin.display(description=_("Signposts"))
    def signposts_summary(self, obj: StreetScanImportRun) -> str:
        """Display signpost create/update/deactivate counts.

        Args:
            obj (StreetScanImportRun): The run log instance.

        Returns:
            str: HTML summary of signpost counts.
        """
        return render_to_string(
            self._ENTITY_SUMMARY_TEMPLATE,
            {
                "created": obj.signposts_created,
                "updated": obj.signposts_updated,
                "deactivated": obj.signposts_deactivated,
            },
        )

    @admin.display(description=_("Additional signs"))
    def additional_signs_summary(self, obj: StreetScanImportRun) -> str:
        """Display additional sign create/update/deactivate counts.

        Args:
            obj (StreetScanImportRun): The run log instance.

        Returns:
            str: HTML summary of additional sign counts.
        """
        return render_to_string(
            self._ENTITY_SUMMARY_TEMPLATE,
            {
                "created": obj.additional_signs_created,
                "updated": obj.additional_signs_updated,
                "deactivated": obj.additional_signs_deactivated,
            },
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
        rows = [
            {"obj_type": obj_type, "phase": phase, "duration": f"{duration_s:.3f}s"}
            for obj_type, phases in durations.items()
            for phase, duration_s in phases.items()
        ]
        return render_to_string(
            "admin/traffic_control/streetscan_import/phase_durations.html",
            {"rows": rows},
        )

    @admin.display(description=_("Event details"))
    def details_display(self, obj: StreetScanImportRun) -> str:
        """Render the details list as HTML tables grouped by object type and level.

        Entries are categorised first by object type (in dependency order), then by
        level (warning → skip → error). Entries from old run records that carry no
        ``object_type`` key are collected under an ``"unknown"`` bucket. Each
        object-type section contains one table per level with a CSV download link.

        Args:
            obj (StreetScanImportRun): The run log instance.

        Returns:
            str: Safe HTML of grouped event detail tables.
        """
        details: list[dict] = obj.details or []
        base_csv_url = reverse("admin:traffic_control_streetscanimportrun_details_csv", args=[obj.pk])
        grouped = self._group_details(details)
        context = self._build_details_context(grouped, base_csv_url)
        return render_to_string(
            "admin/traffic_control/streetscan_import/event_details.html",
            context,
        )

    @staticmethod
    def _group_details(details: list[dict]) -> dict[str, dict[str, list[dict]]]:
        """Group detail entries by object_type then by level.

        Args:
            details (list[dict]): Raw details list from the run log.

        Returns:
            dict[str, dict[str, list[dict]]]: Nested mapping
                ``{object_type: {level: [entries]}}``.
        """
        object_type_order = ("mounts", "signs", "signposts", "additional-signs", "unknown")
        level_order = ("warning", "skip", "error")

        grouped: dict[str, dict[str, list[dict]]] = {ot: {lv: [] for lv in level_order} for ot in object_type_order}

        for entry in details:
            ot = entry.get("object_type") or "unknown"
            if ot not in grouped:
                grouped[ot] = {lv: [] for lv in level_order}
            lv = entry.get("level", "")
            if lv not in grouped[ot]:
                grouped[ot][lv] = []
            grouped[ot][lv].append(entry)

        return grouped

    @staticmethod
    def _build_details_context(grouped: dict[str, dict[str, list[dict]]], base_csv_url: str) -> dict:
        """Build the template context for the event details display.

        At most ``_MAX_ROWS_PER_LEVEL`` entries are included per level bucket to
        avoid rendering multi-megabyte HTML pages for large imports.

        Args:
            grouped (dict[str, dict[str, list[dict]]]): Output of ``_group_details``.
            base_csv_url (str): Base URL for the CSV download endpoint.

        Returns:
            dict: Template context with a ``sections`` list.
        """
        _MAX_ROWS_PER_LEVEL = 200
        level_order = ("warning", "skip", "error")
        level_colour = {"skip": "#ffffff", "warning": "#ffffff", "error": "#ffffff"}
        level_bg = {"skip": "#e9ecef", "warning": "#fff3cd", "error": "#f8d7da"}
        level_border = {"skip": "#adb5bd", "warning": "#ffc107", "error": "#dc3545"}
        level_summary_bg = {"skip": "#6c757d", "warning": "#e6a817", "error": "#dc3545"}

        sections = []
        for object_type, levels in grouped.items():
            level_contexts = []
            for level in level_order:
                entries = levels.get(level, [])
                if not entries:
                    continue
                total = len(entries)
                level_contexts.append(
                    {
                        "level": level,
                        "total": total,
                        "displayed_entries": [
                            {
                                "source_id": e.get("source_id", ""),
                                "phase": e.get("phase", ""),
                                "reason": e.get("reason", ""),
                            }
                            for e in entries[:_MAX_ROWS_PER_LEVEL]
                        ],
                        "truncated": total > _MAX_ROWS_PER_LEVEL,
                        "max_rows": _MAX_ROWS_PER_LEVEL,
                        "csv_url": f"{base_csv_url}?object_type={object_type}&level={level}",
                        "colour": level_colour.get(level, "#fff"),
                        "bg": level_bg.get(level, "#fff"),
                        "border": level_border.get(level, "#ccc"),
                        "summary_bg": level_summary_bg.get(level, "#6c757d"),
                    }
                )
            sections.append(
                {
                    "object_type": object_type,
                    "has_entries": bool(level_contexts),
                    "levels": level_contexts,
                }
            )

        return {"sections": sections}

"""Django admin configuration for import attachment cleanup run tracking."""
from typing import Any, Optional

from django.contrib import admin
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from traffic_control.models import ImportAttachmentCleanupRun


@admin.register(ImportAttachmentCleanupRun)
class ImportAttachmentCleanupRunAdmin(admin.ModelAdmin):
    """Read-only admin interface for stale import attachment cleanup runs."""

    list_display = (
        "id",
        "started_at",
        "completed_at",
        "executed_by",
        "dry_run",
        "max_age_hours",
        "discarded_batches_count",
        "files_discarded",
        "status",
    )
    list_filter = ("dry_run", "status", "started_at")
    search_fields = ("id", "executed_by__username", "error_message")
    list_select_related = ("executed_by",)
    ordering = ("-started_at",)
    readonly_fields = (
        "id",
        "started_at",
        "completed_at",
        "executed_by",
        "dry_run",
        "max_age_hours",
        "discarded_batches_count",
        "files_discarded",
        "discarded_batches",
        "status",
        "error_message",
    )
    fieldsets = (
        (
            _("Run Information"),
            {
                "fields": (
                    "id",
                    "started_at",
                    "completed_at",
                    "executed_by",
                    "dry_run",
                    "max_age_hours",
                    "status",
                )
            },
        ),
        (
            _("Cleanup Statistics"),
            {"fields": ("discarded_batches_count", "files_discarded", "discarded_batches")},
        ),
        (
            _("Error Information"),
            {"fields": ("error_message",), "classes": ("collapse",)},
        ),
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Disable manual creation of cleanup runs.

        Args:
            request (HttpRequest): Current admin request.

        Returns:
            bool: Always ``False``.
        """
        return False

    def has_change_permission(self, request: HttpRequest, obj: Optional[Any] = None) -> bool:
        """Disable editing of cleanup runs.

        Args:
            request (HttpRequest): Current admin request.
            obj (Optional[Any]): Cleanup run being viewed, if any.

        Returns:
            bool: Always ``False``.
        """
        return False

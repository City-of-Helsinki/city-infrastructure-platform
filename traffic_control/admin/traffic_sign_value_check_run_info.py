from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from traffic_control.models import TrafficSignValueCheckRunInfo


@admin.register(TrafficSignValueCheckRunInfo)
class TrafficSignValueCheckRunInfoAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            _("Schedule"),
            {"fields": ("start_time", "end_time", "database_update")},
        ),
        (
            _("Results"),
            {"fields": ("checked_count", "problem_count", "fixed_count", "skipped_fix_count")},
        ),
        (
            _("Details"),
            {"fields": ("checked_codes", "problems")},
        ),
    )
    list_display = (
        "start_time",
        "checked_count",
        "problem_count",
        "fixed_count",
        "skipped_fix_count",
        "database_update",
    )
    list_filter = ("database_update", "start_time")
    ordering = ("-start_time",)

    def has_add_permission(self, request) -> bool:
        """Disable adding run infos through admin.

        https://docs.djangoproject.com/en/5.2/ref/contrib/admin/#django.contrib.admin.ModelAdmin.has_add_permission

        Args:
            request: The current request.

        Returns:
            bool: Always False, as run infos are only written by the management command.
        """
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        """Disable editing existing run infos through admin.

        https://docs.djangoproject.com/en/5.2/ref/contrib/admin/#django.contrib.admin.ModelAdmin.has_change_permission

        Args:
            request: The current request.
            obj: The run info being edited, if any.

        Returns:
            bool: Always False, as run infos are a record of what a command did.
        """
        return False

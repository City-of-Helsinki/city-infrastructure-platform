from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from site_alert.models import SiteAlert


@admin.register(SiteAlert)
class SiteAlertAdmin(admin.ModelAdmin):
    list_display = ("short_message", "level", "is_active", "start_at", "end_at")
    list_editable = ("is_active",)
    list_filter = ("is_active", "level", "created_at")
    search_fields = ("message_en", "message_fi", "message_sv")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (_("Configuration"), {"fields": ("is_active", "level")}),
        (
            _("Content"),
            {
                "fields": ("message_en", "message_fi", "message_sv"),
            },
        ),
        (_("Scheduling"), {"fields": ("start_at", "end_at")}),
        (
            _("Metadata"),
            {
                "classes": ("collapse",),
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    def short_message(self, obj):
        """Returns a truncated preview of the message."""
        msg = obj.translated_message
        return msg[:60] + "..." if len(msg) > 60 else msg

    short_message.short_description = _("Message Preview")

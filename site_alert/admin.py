# alerts/admin.py
from django.contrib import admin

from .models import SiteAlert


@admin.register(SiteAlert)
class SiteAlertAdmin(admin.ModelAdmin):
    list_display = ("short_message", "level", "is_active", "created_at")
    list_editable = ("is_active",)
    list_filter = ("is_active", "level", "created_at")
    search_fields = ("message_en", "message_fi", "message_sv")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Configuration", {"fields": ("is_active", "level")}),
        (
            "Content",
            {
                "description": "Enter the alert text for all supported languages.",
                "fields": ("message_en", "message_fi", "message_sv"),
            },
        ),
        (
            "Metadata",
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

    short_message.short_description = "Message Preview"

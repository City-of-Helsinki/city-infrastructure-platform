from django.db import models
from django.utils.translation import get_language, gettext_lazy as _


class SiteAlert(models.Model):
    LEVEL_CHOICES = [
        ("info", "Info (Blue)"),
        ("warning", "Warning (Yellow)"),
        ("critical", "Critical (Red)"),
    ]

    is_active = models.BooleanField(
        _("Message active"),
        default=True,
        help_text=_("When enabled, display this message to users in the admin pages."),
    )
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default="info")

    message_en = models.TextField(_("Message (English)"), blank=False, null=False, help_text="English message")
    message_fi = models.TextField(_("Message (Finnish)"), blank=False, null=False, help_text="Finnish message")
    message_sv = models.TextField(_("Message (Swedish)"), blank=False, null=False, help_text="Swedish message")

    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    def __str__(self):
        return f"Alert {self.pk} - {self.level}: {self.message_en}"

    @property
    def translated_message(self):
        """Helper to return the correct message based on current active language."""
        lang = get_language()

        if "fi" in lang:
            return self.message_fi or self.message_en
        elif "sv" in lang:
            return self.message_sv or self.message_en
        return self.message_en

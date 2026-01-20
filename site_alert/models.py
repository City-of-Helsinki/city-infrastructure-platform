from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import get_language, gettext_lazy as _
from enumfields import EnumIntegerField


class SiteAlertLevel(models.IntegerChoices):
    INFO = 0, _("Info")
    WARNING = 100, _("Warning")
    CRITICAL = 10000, _("Critical")


class SiteAlertManager(models.Manager):
    def active(self):
        """Return all alerts that are active, respecting their optional activation window."""
        now = timezone.now()
        return self.filter(
            Q(is_active=True)
            & (Q(start_at__isnull=True) | Q(start_at__lte=now))
            & (Q(end_at__isnull=True) | Q(end_at__gte=now))
        )


class SiteAlert(models.Model):
    is_active = models.BooleanField(
        _("Message active"),
        default=True,
        help_text=_("When enabled, display this message to users in the admin pages."),
    )
    level = EnumIntegerField(
        SiteAlertLevel,
        verbose_name=_("Alert level"),
        default=SiteAlertLevel.INFO,
        help_text=_("Select a style of warning to reflect how critical it is"),
    )

    message_en = models.TextField(_("Message (English)"), blank=False, null=False, help_text="English message")
    message_fi = models.TextField(_("Message (Finnish)"), blank=True, null=False, help_text="Finnish message")
    message_sv = models.TextField(_("Message (Swedish)"), blank=True, null=False, help_text="Swedish message")

    start_at = models.DateTimeField(
        _("Start time"),
        blank=True,
        null=True,
        help_text="(Optional) When to start showing this alert. Leave blank to show immediately.",
    )
    end_at = models.DateTimeField(
        _("End time"),
        blank=True,
        null=True,
        help_text="(Optional) When to stop showing this alert. Leave blank to show indefinitely.",
    )

    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    objects = SiteAlertManager()

    class Meta:
        verbose_name = _("Site Alert")
        verbose_name_plural = _("Site Alerts")

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

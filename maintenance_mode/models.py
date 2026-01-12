from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class MaintenanceMode(models.Model):
    """
    Maintenance mode configuration.
    Only one row is allowed in this table.
    """

    id = models.IntegerField(primary_key=True, default=1, editable=False)
    is_active = models.BooleanField(
        _("Maintenance mode active"),
        default=False,
        help_text=_("When active, all requests (except admin for admin users) will be blocked with 503 status."),
    )
    message_fi = models.TextField(
        _("Message (Finnish)"),
        blank=True,
        default="Järjestelmä on huoltotilassa. Yritä myöhemmin uudelleen.",
        help_text=_("Message to display on the maintenance page in Finnish."),
    )
    message_en = models.TextField(
        _("Message (English)"),
        blank=True,
        default="System is under maintenance. Please try again later.",
        help_text=_("Message to display on the maintenance page in English."),
    )
    message_sv = models.TextField(
        _("Message (Swedish)"),
        blank=True,
        default="Systemet är under underhåll. Försök igen senare.",
        help_text=_("Message to display on the maintenance page in Swedish."),
    )
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    updated_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Updated by"),
        related_name="maintenance_mode_updates",
    )

    class Meta:
        verbose_name = _("Maintenance Mode")
        verbose_name_plural = _("Maintenance Mode")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(id=1),
                name="only_one_maintenance_mode_row",
            ),
        ]

    def __str__(self):
        return f"Maintenance Mode ({'Active' if self.is_active else 'Inactive'})"

    def save(self, *args, **kwargs):
        # Force id to be 1 to ensure singleton pattern
        self.id = 1
        self.pk = 1
        # Always use force_update if a row exists to avoid INSERT attempts
        if MaintenanceMode.objects.filter(pk=1).exists():
            kwargs["force_update"] = True
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Prevent deletion
        raise ValidationError(_("Maintenance mode configuration cannot be deleted."))

    @classmethod
    def get_instance(cls):
        """Get or create the single instance of MaintenanceMode."""
        instance, _ = cls.objects.get_or_create(id=1)
        return instance

"""Common base models and mixins for migration tracking."""
from django.db import models
from django.utils.translation import gettext_lazy as _


class BaseFieldTrackingMixin(models.Model):
    """Abstract base class for common field tracking across migration Plan and Real records."""

    # Common field tracking (fields that exist in both TrafficSignPlan and TrafficSignReal)
    had_height = models.BooleanField(_("Had height"), default=False)
    had_size = models.BooleanField(_("Had size"), default=False)
    had_direction = models.BooleanField(_("Had direction"), default=False)
    had_reflection_class = models.BooleanField(_("Had reflection_class"), default=False)
    had_surface_class = models.BooleanField(_("Had surface_class"), default=False)
    had_mount_type = models.BooleanField(_("Had mount_type"), default=False)
    had_road_name = models.BooleanField(_("Had road_name"), default=False)
    had_lane_number = models.BooleanField(_("Had lane_number"), default=False)
    had_lane_type = models.BooleanField(_("Had lane_type"), default=False)
    had_location_specifier = models.BooleanField(_("Had location_specifier"), default=False)
    had_validity_period_start = models.BooleanField(_("Had validity_period_start"), default=False)
    had_validity_period_end = models.BooleanField(_("Had validity_period_end"), default=False)
    had_source_name = models.BooleanField(_("Had source_name"), default=False)
    had_source_id = models.BooleanField(_("Had source_id"), default=False)

    files_migrated = models.IntegerField(
        _("Files migrated"),
        default=0,
        help_text=_("Number of file attachments migrated."),
    )
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)

    class Meta:
        abstract = True


class TicketMachineFieldTrackingMixin(BaseFieldTrackingMixin):
    """Extended field tracking for ticket machine migrations (includes lost fields specific to ticket machines)."""

    # Lost fields specific to ticket machines
    lost_value = models.CharField(_("Lost value"), max_length=50, blank=True, default="")
    lost_txt = models.CharField(_("Lost txt"), max_length=254, blank=True, default="")
    lost_double_sided = models.BooleanField(_("Lost double_sided"), default=False)
    lost_peak_fastened = models.BooleanField(_("Lost peak_fastened"), default=False)

    # Default values set (specific to ticket machine -> additional sign migration)
    set_color_to_blue = models.BooleanField(_("Set color to BLUE"), default=True)
    set_content_s_null = models.BooleanField(_("Set content_s to null"), default=True)
    set_missing_content_false = models.BooleanField(_("Set missing_content to false"), default=True)
    set_additional_information_empty = models.BooleanField(_("Set additional_information to empty"), default=True)

    class Meta:
        abstract = True

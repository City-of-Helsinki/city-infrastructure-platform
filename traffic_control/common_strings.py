from django.utils.translation import gettext_lazy as _

direction_field_verbose_name = _("Direction")
direction_help_text = _(
    "The orientation of the device’s front side in degrees (0–359): 0 = north, 90 = east, 180 = south, 270 = west. "
    "The direction indicates from which side the device is correctly visible."
)

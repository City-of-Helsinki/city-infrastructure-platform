import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class Layer(models.Model):
    identifier = models.CharField(_("Identifier"), max_length=200)
    app_name = models.CharField(_("App Name"), max_length=200, default="traffic_control")
    name_fi = models.CharField(_("Finnish name"), max_length=200)
    name_en = models.CharField(_("English name"), max_length=200)
    is_basemap = models.BooleanField(_("Is basemap"), default=False)
    order = models.IntegerField(_("Order"), default=1)
    filter_fields = models.CharField(_("Filter fields"), max_length=200, blank=True)
    use_traffic_sign_icons = models.BooleanField(_("Use Traffic Sign Icons"), default=False)

    class Meta:
        verbose_name = _("Layer")
        verbose_name_plural = _("Layers")
        ordering = ("is_basemap", "order")

    def __str__(self):
        return self.name_fi


class FeatureTypeEditMapping(models.Model):
    """Model for mapping feature type to another string that is used in map-view FeatureInfo component edit button.
    Usage is eg. for mountplancentroids which do not have own model -> it should be mapped to mountplan
    """

    id = models.UUIDField(primary_key=True, unique=True, editable=False, default=uuid.uuid4)
    name = models.CharField(
        _("Name"), max_length=200, null=False, blank=False, help_text=_("Name of feature type"), unique=True
    )
    edit_name = models.CharField(
        max_length=200,
        null=False,
        blank=False,
        help_text=_("Edit name, used in map-view FeatureInfo component edit link"),
    )

    @staticmethod
    def get_featuretype_edit_name_mapping():
        return {mapping.name: mapping.edit_name for mapping in FeatureTypeEditMapping.objects.all()}

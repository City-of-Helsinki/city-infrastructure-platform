from django.db import models
from django.utils.translation import ugettext_lazy as _


class Layer(models.Model):
    identifier = models.CharField(_("Identifier"), max_length=200)
    name_fi = models.CharField(_("Finnish name"), max_length=200)
    name_en = models.CharField(_("English name"), max_length=200)
    is_basemap = models.BooleanField(_("Is basemap"), default=False)
    order = models.IntegerField(_("Order"), default=1)

    class Meta:
        verbose_name = _("Layer")
        verbose_name_plural = _("Layers")
        ordering = ("is_basemap", "order")

    def __str__(self):
        return self.name_fi

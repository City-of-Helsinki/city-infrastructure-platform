import uuid

from django.conf import settings
from django.db import models, NotSupportedError
from django.utils.translation import gettext_lazy as _

from map.validators import validate_layer_extra_feature_info


class Layer(models.Model):
    identifier = models.CharField(_("Identifier"), max_length=200)
    app_name = models.CharField(_("App Name"), max_length=200, default="traffic_control")
    name_fi = models.CharField(_("Finnish name"), max_length=200)
    name_en = models.CharField(_("English name"), max_length=200)
    name_sv = models.CharField(_("Swedish name"), max_length=200, default="Missing SW translation")
    is_basemap = models.BooleanField(_("Is basemap"), default=False)
    order = models.IntegerField(_("Order"), default=1)
    filter_fields = models.CharField(_("Filter fields"), max_length=200, blank=True)
    use_traffic_sign_icons = models.BooleanField(_("Use Traffic Sign Icons"), default=False)
    clustered = models.BooleanField(_("Clustered"), default=True)
    extra_feature_info = models.JSONField(
        _("Extra Feature Info"),
        null=True,
        blank=True,
        help_text=_("Fields added here need to be included in the corresponding WFS Feature"),
        validators=[validate_layer_extra_feature_info],
    )

    class Meta:
        verbose_name = _("Layer")
        verbose_name_plural = _("Layers")
        ordering = ("is_basemap", "order")

    def __str__(self):
        return self.name_fi

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class FeatureTypeEditMapping(models.Model):
    """Model for mapping feature type to another string that is used in map-view FeatureInfo component edit button.
    Usage is eg. for mountplancentroids which do not have own model -> it should be mapped to mountplan
    """

    id = models.UUIDField(primary_key=True, unique=True, editable=False, default=uuid.uuid4)
    name = models.CharField(
        _("Name"), max_length=200, null=False, blank=False, help_text=_("Name of feature type"), unique=True
    )
    edit_name = models.CharField(
        _("Edit name"),
        max_length=200,
        null=False,
        blank=False,
        help_text=_("Edit name, used in map-view FeatureInfo component edit link"),
    )

    class Meta:
        verbose_name = _("Feature Type Edit Mapping")
        verbose_name_plural = _("Feature Type Edit Mappings")

    @staticmethod
    def get_featuretype_edit_name_mapping():
        return {mapping.name: mapping.edit_name for mapping in FeatureTypeEditMapping.objects.all()}


class IconDrawingConfig(models.Model):
    DEFAULT_ICON_URL = settings.TRAFFIC_CONTROL_DEVICE_TYPE_SVG_ICON_DESTINATION
    DEFAULT_ICON_SCALE = 0.075

    class ImageType(models.TextChoices):
        PNG = "png", _("png")
        SVG = "svg", _("svg")

    class PngSize(models.IntegerChoices):
        SMALL = 32
        MEDIUM = 64
        LARGE = 128
        EXTRA_LARGE = 256

    id = models.UUIDField(primary_key=True, unique=True, editable=False, default=uuid.uuid4)
    name = models.CharField(_("Name"), max_length=200, unique=True)
    enabled = models.BooleanField(_("Enabled"), default=False)
    image_type = models.CharField(_("Image Type"), choices=ImageType.choices, max_length=10, null=False, blank=False)
    png_size = models.IntegerField(_("PNG Size"), choices=PngSize.choices, null=False, blank=False)
    scale = models.FloatField(_("Scale"), null=True, blank=False, default=None)

    class Meta:
        verbose_name = _("IconDrawingConfig")
        verbose_name_plural = _("IconDrawingConfigs")
        constraints = [
            models.UniqueConstraint(
                fields=["image_type", "png_size"],
                name="%(app_label)s_%(class)s_unique_image_type_png_size",
            ),
            models.UniqueConstraint(
                fields=["enabled"],
                condition=models.Q(enabled=True),
                name="%(app_label)s_%(class)s_unique_enabled",
            ),
        ]

    @property
    def icons_relative_url(self) -> str:
        if self.image_type == IconDrawingConfig.ImageType.SVG:
            return self.DEFAULT_ICON_URL
        elif self.image_type == IconDrawingConfig.ImageType.PNG:
            return f"{settings.TRAFFIC_CONTROL_DEVICE_TYPE_PNG_ICON_DESTINATION}{self.png_size}/"
        raise NotSupportedError(f"No support for image type: {self.image_type}")

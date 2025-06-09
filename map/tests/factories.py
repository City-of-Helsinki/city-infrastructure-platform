import factory.django

from map.models import IconDrawingConfig


class IconDrawingConfigFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = IconDrawingConfig
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"iconDrawConfig{n}")
    enabled = False
    image_type = "svg"
    png_size = 32
    scale = IconDrawingConfig.DEFAULT_ICON_SCALE

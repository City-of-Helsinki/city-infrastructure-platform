import factory.django

from map.models import FeatureTypeEditMapping, IconDrawingConfig, Layer


class IconDrawingConfigFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = IconDrawingConfig
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"iconDrawConfig{n}")
    enabled = False
    image_type = "svg"
    png_size = 32
    scale = IconDrawingConfig.DEFAULT_ICON_SCALE


class LayerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Layer

    identifier = factory.Sequence(lambda n: f"layer{n}")
    app_name = "traffic_control"
    name_fi = factory.LazyAttribute(lambda layer: f"{layer.identifier} fi")
    name_en = factory.LazyAttribute(lambda layer: f"{layer.identifier} en")
    name_sv = factory.LazyAttribute(lambda layer: f"{layer.identifier} sv")
    is_basemap = False


class FeatureTypeEditMappingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FeatureTypeEditMapping
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"featuretype{n}")
    edit_name = factory.Sequence(lambda n: f"editname{n}")

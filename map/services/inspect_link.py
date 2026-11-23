"""Builds links from admin edit views to a single feature in the map-view."""

from urllib.parse import urlencode

from django.conf import settings
from django.db.models import Model
from django.urls import reverse

from map.models import FeatureTypeEditMapping, Layer

INSPECT_LAYER_PARAM = "inspect_layer"
INSPECT_ID_PARAM = "inspect_id"


def get_inspect_layer_identifier(model: type[Model]) -> str | None:
    """Finds the map-view overlay layer that shows features of the given model.

    The layer identifier is the WFS feature type name, which is the lowercase model name by convention.
    Feature types without an own model (e.g. ``mountrealcentroid``) are found through
    ``FeatureTypeEditMapping`` rows whose ``edit_name`` points to the model.

    Args:
        model (type[Model]): The model class whose layer is looked up.

    Returns:
        str | None: The overlay layer identifier, or None if no layer is configured for the model.
    """
    model_name = model._meta.model_name
    candidates = [
        model_name,
        *FeatureTypeEditMapping.objects.filter(edit_name=model_name).values_list("name", flat=True),
    ]
    identifiers = set(
        Layer.objects.filter(
            is_basemap=False,
            app_name=model._meta.app_label,
            identifier__in=candidates,
        ).values_list("identifier", flat=True)
    )
    return next((candidate for candidate in candidates if candidate in identifiers), None)


def build_map_view_inspect_url(obj: Model) -> str | None:
    """Builds a map-view URL that shows only the given object, zoomed to it.

    Args:
        obj (Model): The saved model instance to inspect.

    Returns:
        str | None: The map-view URL, or None if the object is unsaved, has no map layer or is not shown
            in the map-view (e.g. soft deleted, inactive lifecycle, expired validity period or not the
            current plan version).
    """
    if obj._state.adding:
        return None
    identifier = get_inspect_layer_identifier(type(obj))
    if identifier is None or not is_shown_in_map_view(obj, identifier):
        return None
    query = urlencode({INSPECT_LAYER_PARAM: identifier, INSPECT_ID_PARAM: str(obj.pk)})
    return f"{get_map_view_base_url()}?{query}"


def is_shown_in_map_view(obj: Model, identifier: str) -> bool:
    """Checks whether the map-view can show the object on the given layer.

    The map-view loads features from the WFS API, so the object is shown only if it is included in the
    queryset of the WFS feature type that the layer identifier names.

    Args:
        obj (Model): The saved model instance.
        identifier (str): The map-view layer identifier, i.e. the WFS feature type name.

    Returns:
        bool: True if the WFS feature type exists and its queryset contains the object.
    """
    # Imported here to avoid a circular import: admin mixins -> WFS views -> models.
    from traffic_control.views.wfs.views import CityInfrastructureWFSView

    feature_type = next((ft for ft in CityInfrastructureWFSView.feature_types if ft.name == identifier), None)
    return feature_type is not None and feature_type.queryset.filter(pk=obj.pk).exists()


def get_map_view_base_url() -> str:
    """Returns the base URL of the map-view.

    Returns:
        str: ``settings.MAP_VIEW_URL`` when set (e.g. a Vite dev server in local development),
            otherwise the path of the map-view served by Django.
    """
    return settings.MAP_VIEW_URL or reverse("map-view")

"""Builds links from admin edit views to a single feature in the map-view."""

from django.conf import settings
from django.urls import reverse


def get_map_view_base_url() -> str:
    """Returns the base URL of the map-view.

    Returns:
        str: ``settings.MAP_VIEW_URL`` when set (e.g. a Vite dev server in local development),
            otherwise the path of the map-view served by Django.
    """
    return settings.MAP_VIEW_URL or reverse("map-view")

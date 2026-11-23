from django.urls import reverse

from map.services.inspect_link import get_map_view_base_url


def test_map_view_base_url_defaults_to_django_map_view(settings) -> None:
    settings.MAP_VIEW_URL = ""
    assert get_map_view_base_url() == reverse("map-view")


def test_map_view_base_url_uses_setting(settings) -> None:
    settings.MAP_VIEW_URL = "http://localhost:5173/"
    assert get_map_view_base_url() == "http://localhost:5173/"
